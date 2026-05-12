#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通达信 F10 数据爬虫
功能：直接抓取通达信 F10 接口，获取公司资讯、盈利预测等数据
"""

import os
import sys
import json
import logging
from typing import Dict, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TDX_DIR

logger = logging.getLogger(__name__)


class TdxF10Spider:
    """
    通达信 F10 数据爬虫

    通达信 F10 数据存储:
    - vipdoc/sh/sz/f10/ 目录下的各种 .dat 文件
    - 通过通达信客户端内置 HTTP 服务获取（如有）
    """

    def __init__(self, tdx_dir: str = TDX_DIR):
        self.tdx_dir = tdx_dir
        self.f10_dir = None
        self._find_f10_dir()

    def _find_f10_dir(self):
        """查找 F10 数据目录"""
        # 可能的 F10 数据位置
        candidates = [
            os.path.join(self.tdx_dir, "vipdoc", "sh", "f10"),
            os.path.join(self.tdx_dir, "vipdoc", "sz", "f10"),
            os.path.join(self.tdx_dir, "vipdoc", "f10"),
        ]
        for cand in candidates:
            if os.path.exists(cand):
                self.f10_dir = cand
                logger.info(f"F10 目录: {cand}")
                return
        logger.warning(f"未找到 F10 目录，请检查通达信安装路径: {self.tdx_dir}")

    def get_company_profile(self, code: str) -> Optional[Dict]:
        """
        获取公司基本信息

        截图中的信息：
        - 所属行业：金属制品业
        - 主营业务：先进铜基金属粉体材料...
        - 上市时间
        - 总股本、流通股本

        Returns:
            Dict: 公司基本信息
        """
        market = 'sh' if code.startswith(('6', '68')) else 'sz'

        info = {
            'code': code,
            'name': '',
            'industry': '',
            'main_business': '',
            'listing_date': '',
            'total_shares': 0,    # 总股本
            'float_shares': 0,     # 流通股本
            'province': '',
            'city': '',
        }

        # 方法1: 从通达信 F10 文件读取
        if self.f10_dir:
            profile = self._read_f10_profile(code, market)
            if profile:
                info.update(profile)

        # 方法2: 使用 AKShare 补充（网络连接）
        if not info.get('industry'):
            try:
                import akshare as ak
                df = ak.stock_individual_info_em(symbol=code)
                if not df.empty:
                    for _, row in df.iterrows():
                        item = row['item']
                        val = row['value']
                        if '股票简称' in item or '名称' in item:
                            info['name'] = val
                        elif '行业' in item:
                            info['industry'] = val
                        elif '上市' in item:
                            info['listing_date'] = val
                        elif '主营' in item:
                            info['main_business'] = val
                        elif '省份' in item or '地区' in item:
                            info['province'] = val
                logger.info(f"  [AKShare] 获取公司信息: {info['name']}")
            except Exception as e:
                logger.warning(f"  AKShare 获取失败: {e}")

        return info

    def _read_f10_profile(self, code: str, market: str) -> Optional[Dict]:
        """读取通达信 F10 公司资料文件"""
        # 通达信 F10 文件格式需要逆向分析
        # 常见文件名: {code}.txt, {code}.dat, company.dat 等
        f10_path = os.path.join(self.tdx_dir, "vipdoc", market, "f10")
        if not os.path.exists(f10_path):
            return None

        # 尝试查找公司资料文件
        candidates = [
            os.path.join(f10_path, f"{code}.txt"),
            os.path.join(f10_path, f"{code}.dat"),
            os.path.join(f10_path, "company", f"{code}.dat"),
        ]

        for cand in candidates:
            if os.path.exists(cand):
                return self._parse_f10_text(cand)

        return None

    def _parse_f10_text(self, file_path: str) -> Dict:
        """解析 F10 文本文件"""
        info = {}
        try:
            with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                content = f.read()
                # 简单解析（需要根据实际格式调整）
                lines = content.split('\n')
                for line in lines:
                    if '行业' in line or '主营' in line:
                        # 解析键值对
                        pass
        except Exception as e:
            logger.error(f"解析 F10 文件失败 {file_path}: {e}")
        return info

    def get_earnings_forecast(self, code: str) -> Optional[List[Dict]]:
        """
        获取盈利预测数据

        截图中的数据格式:
        | 预测年度 | 预测每股收益 | 预测每股净资产 | 预测净资产收益率(%) | 预测归属母公司净利润(元) | 预测营业总收入(元) | 预测营业利润(元) | 市场一致预期(元) | 报告日期 |
        """
        logger.info(f"  获取 {code} 盈利预测...")

        forecasts = []

        # 方法1: AKShare - 东方财富机构预测
        try:
            import akshare as ak
            # 获取机构预测数据
            df = ak.stock_yjyg_em(symbol=code)
            if not df.empty:
                for _, row in df.iterrows():
                    forecasts.append({
                        'year': row.get('预测年度', ''),
                        'eps_forecast': row.get('预测每股收益', 0),
                        'bps_forecast': row.get('预测每股净资产', 0),
                        'roe_forecast': row.get('预测净资产收益率', 0),
                        'net_profit_forecast': row.get('预测归属净利润', 0),
                        'revenue_forecast': row.get('预测营业总收入', 0),
                        'operating_profit_forecast': row.get('预测营业利润', 0),
                        'report_date': row.get('报告日期', ''),
                    })
                logger.info(f"  [AKShare] 获取 {len(forecasts)} 条预测")
                return forecasts
        except Exception as e:
            logger.warning(f"  AKShare 获取盈利预测失败: {e}")

        # 方法2: 从通达信 F10 本地文件读取
        # 盈利预测数据通常存储在 F10 的特定文件中
        local_data = self._read_local_forecast(code)
        if local_data:
            return local_data

        return None

    def _read_local_forecast(self, code: str) -> Optional[List[Dict]]:
        """从通达信本地文件读取盈利预测"""
        # 通达信盈利预测数据文件格式需要逆向分析
        # 可能的文件名: forecast.dat, yuce.dat,  etc.
        return None

    def get_realtime_quote_enhanced(self, code: str) -> Optional[Dict]:
        """
        获取增强版实时行情（包含市值、换手率）

        数据来源:
        1. pytdx 实时行情接口
        2. 本地财务数据（总股本）
        """
        try:
            from pytdx.hq import TdxHq_API
            from fetchers.finance_collector import FinanceCollector

            market = 1 if code.startswith(('6', '68')) else 0

            api = TdxHq_API(heartbeat=True, auto_retry=True)

            # 连接行情服务器
            # 常用服务器: 119.147.212.81:7709 (上海), 112.74.216.106:7709 (深圳)
            servers = [
                ('119.147.212.81', 7709),  # 上海
                ('112.74.216.106', 7709),  # 深圳
                ('47.107.75.102', 7709),    # 备用
            ]

            connected = False
            for host, port in servers:
                try:
                    if api.connect(host, port):
                        connected = True
                        break
                except:
                    continue

            if not connected:
                logger.error("  连接行情服务器失败")
                return None

            # 获取实时行情
            quotes = api.get_security_quotes([(market, code)])
            api.disconnect()

            if not quotes or len(quotes) == 0:
                return None

            q = quotes[0]

            # 获取总股本（用于计算市值和换手率）
            total_shares = None
            try:
                collector = FinanceCollector()
                _, total_shares = collector.collect(code, max_quarters=1)
            except:
                pass

            # 价格相关（pytdx 返回的价格需要除以 100）
            price = q['price'] / 100 if q.get('price') else 0
            last_close = q['last_close'] / 100 if q.get('last_close') else 0

            # 涨跌幅
            change_pct = ((price - last_close) / last_close * 100) if last_close > 0 else 0

            # 换手率 = 成交量(手) * 100 / 流通股本 * 100
            volume = q.get('vol', 0)  # 成交量（手）
            turnover = 0
            if total_shares and total_shares > 0:
                # 假设流通股本 ≈ 总股本（实际情况需要单独获取）
                turnover = (volume * 100) / (total_shares) * 100

            # 市值 = 价格 * 总股本 / 1e8
            market_cap = (price * total_shares / 1e8) if total_shares else 0

            return {
                'code': code,
                'name': q.get('name', ''),
                'price': round(price, 2),
                'change_pct': round(change_pct, 2),
                'turnover': round(turnover, 2),
                'market_cap': round(market_cap, 2),  # 亿元
                'volume': volume,           # 成交量（手）
                'amount': q.get('amount', 0),  # 成交额
                'open': q.get('open', 0) / 100,
                'high': q.get('high', 0) / 100,
                'low': q.get('low', 0) / 100,
                'pre_close': last_close,
                'bid1': q.get('bid1', 0) / 100,
                'ask1': q.get('ask1', 0) / 100,
                'total_shares': total_shares,
            }

        except Exception as e:
            logger.error(f"  获取实时行情失败: {e}")
            return None


def print_stock_summary(info: Dict):
    """打印股票摘要信息"""
    code = info.get('code', '')
    quote = info.get('quote', {})
    company = info.get('company', {})
    forecasts = info.get('forecasts', [])

    print("\n" + "=" * 80)
    print(f"  股票代码: {code}  {quote.get('name', '')}")
    print("=" * 80)

    # 行情数据
    if quote:
        print("\n【实时行情】")
        print(f"  当前价格:  {quote['price']:.2f} 元")
        color = "📈" if quote['change_pct'] >= 0 else "📉"
        print(f"  涨跌幅:    {color} {quote['change_pct']:+.2f}%")
        print(f"  换手率:    {quote['turnover']:.2f}%")
        print(f"  总市值:    {quote['market_cap']:.2f} 亿元")
        print(f"  开盘价:    {quote.get('open', 0):.2f} 元")
        print(f"  最高价:    {quote.get('high', 0):.2f} 元")
        print(f"  最低价:    {quote.get('low', 0):.2f} 元")

    # 公司信息
    if company:
        print("\n【公司信息】")
        print(f"  公司名称: {company.get('name', 'N/A')}")
        print(f"  所属行业: {company.get('industry', 'N/A')}")
        print(f"  主营业务: {company.get('main_business', 'N/A')[:50]}...")
        print(f"  上市日期: {company.get('listing_date', 'N/A')}")

    # 盈利预测
    if forecasts:
        print("\n【盈利预测】")
        print(f"  {'年度':<8} {'EPS(元)':<12} {'营收(亿元)':<15} {'净利润(亿元)':<15}")
        print("  " + "-" * 60)
        for f in forecasts[:5]:  # 只显示前5条
            print(f"  {f['year']:<8} {f.get('eps_forecast', 0):<12.4f} "
                  f"{f.get('revenue_forecast', 0)/1e8:<15.2f} "
                  f"{f.get('net_profit_forecast', 0)/1e8:<15.2f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import argparse
    import time

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%H:%M:%S')

    parser = argparse.ArgumentParser(description='获取股票 F10 综合信息')
    parser.add_argument('code', nargs='?', default='688456', help='股票代码')
    args = parser.parse_args()

    code = args.code.zfill(6)
    print(f"\n{'=' * 60}")
    print(f"  采集股票: {code}")
    print(f"{'=' * 60}\n")

    spider = TdxF10Spider()

    # 1. 获取实时行情
    print("[1/3] 获取实时行情...")
    quote = spider.get_realtime_quote_enhanced(code)

    # 2. 获取公司信息
    print("\n[2/3] 获取公司信息...")
    company = spider.get_company_profile(code)

    # 3. 获取盈利预测
    print("\n[3/3] 获取盈利预测...")
    forecasts = spider.get_earnings_forecast(code)

    # 汇总并打印
    info = {
        'code': code,
        'quote': quote,
        'company': company,
        'forecasts': forecasts
    }
    print_stock_summary(info)
