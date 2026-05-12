#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F10数据采集器 - 从通达信远程服务器获取
"""
import os
import sys
import re
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pytdx.hq import TdxHq_API

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

TDX_SERVERS = [
    ('120.25.129.112', 7709),
    ('183.239.132.37', 7709),
    ('180.153.18.178', 7709),
]


class TdxF10Collector:
    """从通达信服务器获取F10数据"""

    def __init__(self):
        self.api = None
        self._connect()

    def _connect(self) -> bool:
        """连接到通达信服务器"""
        for host, port in TDX_SERVERS:
            try:
                self.api = TdxHq_API()
                if self.api.connect(host, port):
                    logger.info(f"成功连接到 {host}:{port}")
                    return True
            except Exception as e:
                logger.debug(f"连接 {host}:{port} 失败: {e}")
        logger.error("无法连接到任何通达信服务器")
        return False

    def get_company_profile(self, code: str) -> dict:
        """获取公司概况"""
        if not self.api:
            logger.error("未连接到服务器")
            return {}

        try:
            # 判断市场
            market = 1 if code.startswith('6') else 0

            # 获取公司信息类别
            category = self.api.get_company_info_category(market, code)
            if not category:
                return {}

            # 找到公司概况
            profile_info = None
            filename = None
            for item in category:
                if item['name'] == '公司概况':
                    profile_info = item
                    filename = item['filename']
                    break

            if not profile_info:
                return {}

            # 获取公司概况内容
            content = self.api.get_company_info_content(
                market, code, filename,
                profile_info['start'],
                profile_info['length']
            )

            if not content:
                return {}

            # 解析内容（表格格式）
            return self._parse_profile_table(content)

        except Exception as e:
            logger.error(f"获取公司概况失败 {code}: {e}")
            return {}

    def _parse_profile_table(self, content: str) -> dict:
        """解析表格格式的公司概况"""
        info = {
            'company_name': '--',
            'english_name': '--',
            'industry': '--',
            'business_scope': '--',
            'list_date': '--',
            'reg_capital': '--',
            'chairman': '--',
            'general_manager': '--',
            'address': '--',
            'phone': '--',
            'website': '--'
        }

        # 按行分割
        lines = content.split('\n')

        for line in lines:
            # 去除表格边框字符
            line_clean = line.replace('┌', '').replace('┐', '').replace('├', '').replace('┤', '')
            line_clean = line_clean.replace('─', '').replace('│', '|').strip()

            # 按 | 分割
            parts = [p.strip() for p in line_clean.split('|') if p.strip()]

            if len(parts) >= 2:
                key = parts[0]
                value = parts[1] if len(parts) > 1 else ''

                if '公司名称' in key:
                    info['company_name'] = value
                elif '英文全称' in key:
                    info['english_name'] = value
                elif '行业' in key and info['industry'] == '--':
                    info['industry'] = value
                elif '上市日期' in key:
                    info['list_date'] = value
                elif '注册资本' in key:
                    info['reg_capital'] = value
                elif '法人代表' in key:
                    info['chairman'] = value
                elif '总经理' in key:
                    info['general_manager'] = value

                # 处理双列格式
                if len(parts) >= 4:
                    key2 = parts[2]
                    value2 = parts[3] if len(parts) > 3 else ''
                    if '行业' in key2 and info['industry'] == '--':
                        info['industry'] = value2
                    elif '上市日期' in key2:
                        info['list_date'] = value2

        return info

    def disconnect(self):
        """断开连接"""
        if self.api:
            self.api.disconnect()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='获取F10公司概况')
    parser.add_argument('code', nargs='?', default='688456', help='股票代码')
    args = parser.parse_args()

    collector = TdxF10Collector()
    profile = collector.get_company_profile(args.code)

    print(f"\n股票代码: {args.code}")
    print("=" * 60)
    print(f"公司名称:    {profile.get('company_name', '--')}")
    print(f"英文名称:    {profile.get('english_name', '--')}")
    print(f"所属行业:    {profile.get('industry', '--')}")
    print(f"上市日期:    {profile.get('list_date', '--')}")
    print(f"注册资本:    {profile.get('reg_capital', '--')}")
    print(f"法人代表:    {profile.get('chairman', '--')}")
    print(f"总经理:      {profile.get('general_manager', '--')}")
    print("=" * 60)

    collector.disconnect()


if __name__ == '__main__':
    main()