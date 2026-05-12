#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票综合信息采集器
功能：获取实时行情、公司基本信息、盈利预测数据
"""

import os
import sys
import struct
import logging
from typing import Dict, Optional, List
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TDX_DIR

logger = logging.getLogger(__name__)


class StockInfoCollector:
    """
    股票综合信息采集器

    从通达信本地数据获取：
    1. 实时行情数据（价格、涨跌幅、换手率、市值）
    2. 公司基本信息（行业、主营业务）
    3. 盈利预测数据
    """

    def __init__(self, tdx_dir: str = TDX_DIR):
        """
        初始化

        Args:
            tdx_dir: 通达信安装目录
        """
        self.tdx_dir = tdx_dir
        self.vipdoc_dir = os.path.join(tdx_dir, "vipdoc")

    def get_market(self, code: str) -> int:
        """根据代码判断市场 (1=上海, 0=深圳)"""
        if code.startswith('6') or code.startswith('68'):
            return 1  # 上海
        return 0  # 深圳

    def get_realtime_quote(self, code: str) -> Optional[Dict]:
        """
        获取实时行情数据（使用 pytdx）

        Returns:
            Dict: {
                'price': 当前价格,
                'change_pct': 涨跌幅%,
                'turnover': 换手率%,
                'market_cap': 总市值(亿),
                'volume': 成交量,
                'amount': 成交额,
                'open': 开盘价,
                'high': 最高价,
                'low': 最低价,
                'pre_close': 昨收价
            }
        """
        try:
            from pytdx.hq import TdxHq_API

            market = self.get_market(code)
            api = TdxHq_API(heartbeat=True)

            if not api.connect('119.147.212.81', 7709):
                logger.error("连接行情服务器失败")
                return None

            data = api.get_security_quotes([(market, code)])
            api.disconnect()

            if not data or len(data) == 0:
                return None

            quote = data[0]

            # 计算涨跌幅
            price = quote.get('price', 0) / 100  # 价格需要除以100
            pre_close = quote.get('last_close', 0) / 100
            change_pct = ((price - pre_close) / pre_close * 100) if pre_close > 0 else 0

            # 计算市值（需要总股本）
            total_shares = self._get_total_shares(code)
            market_cap = (price * total_shares / 1e8) if total_shares > 0 else 0  # 亿元

            # 换手率 = 成交量 / 流通股本 * 100
            volume = quote.get('vol', 0)
            turnover = 0
            if total_shares > 0:
                turnover = (volume / total_shares * 100)

            return {
                'code': code,
                'price': round(price, 2),
                'change_pct': round(change_pct, 2),
                'turnover': round(turnover, 2),
                'market_cap': round(market_cap, 2),
                'volume': volume,
                'amount': quote.get('amount', 0),
                'open': quote.get('open', 0) / 100,
                'high': quote.get('high', 0) / 100,
                'low': quote.get('low', 0) / 100,
                'pre_close': pre_close,
                'bid1': quote.get('bid1', 0) / 100,
                'ask1': quote.get('ask1', 0) / 100,
            }

        except Exception as e:
            logger.error(f"获取实时行情失败 {code}: {e}")
            return None

    def _get_total_shares(self, code: str) -> float:
        """从 gpcw 数据获取总股本"""
        try:
            from fetchers.finance_collector import FinanceCollector
            collector = FinanceCollector()
            df, total_shares = collector.collect(code, max_quarters=1)
            return total_shares if total_shares else 0
        except:
            return 0

    def get_company_info(self, code: str) -> Optional[Dict]:
        """
        获取公司基本信息

        从通达信 F10 本地文件获取：
        - 行业分类
        - 主营业务
        - 公司名称
        - 上市日期

        Returns:
            Dict: {
                'name': 公司名称,
                'industry': 所属行业,
                'main_business': 主营业务,
                'list_date': 上市日期,
                'province': 所属省份,
                'city': 所属城市
            }
        """
        info = {
            'code': code,
            'name': '',
            'industry': '',
            'main_business': '',
            'list_date': '',
            'province': '',
            'city': ''
        }

        # 方法1: 尝试从 pytdx 获取
        try:
            from pytdx.exhq import TdxExHq_API
            api = TdxExHq_API()
            # pytdx 的 F10 接口有限，这里作为备选
        except:
            pass

        # 方法2: 从通达信本地文件解析
        # 通达信的 F10 数据存储在 vipdoc/sh[sz]/fzline/ 等目录
        market = 'sh' if self.get_market(code) == 1 else 'sz'

        # 尝试读取公司资料文件
        company_file = os.path.join(self.vipdoc_dir, market, "fzline", f"{code}.dat")
        if os.path.exists(company_file):
            info.update(self._parse_company_file(company_file))

        # 方法3: 使用 akshare 作为备选（需要网络）
        if not info.get('industry'):
            try:
                import akshare as ak
                stock_info = ak.stock_individual_info_em(symbol=code)
                if not stock_info.empty:
                    info['name'] = stock_info.loc[stock_info['item'] == '股票简称', 'value'].values[0] if '股票简称' in stock_info['item'].values else ''
                    info['industry'] = stock_info.loc[stock_info['item'] == '所属行业', 'value'].values[0] if '所属行业' in stock_info['item'].values else ''
                    info['list_date'] = stock_info.loc[stock_info['item'] == '上市时间', 'value'].values[0] if '上市时间' in stock_info['item'].values else ''
            except Exception as e:
                logger.warning(f"akshare 获取公司信息失败: {e}")

        return info if info.get('name') or info.get('industry') else None

    def _parse_company_file(self, file_path: str) -> Dict:
        """解析通达信公司资料文件"""
        info = {}
        try:
            # 通达信公司资料文件格式需要逆向分析
            # 这里使用简化处理
            with open(file_path, 'rb') as f:
                content = f.read()
                # TODO: 实现具体的解析逻辑
        except Exception as e:
            logger.error(f"解析公司资料文件失败: {e}")
        return info

    def get_earnings_forecast(self, code: str) -> Optional[pd.DataFrame]:
        """
        获取盈利预测数据

        从通达信 F10 获取机构盈利预测：
        - 预测年度
        - 预测 EPS
        - 预测营收
        - 预测净利润
        - 预测机构数量

        Returns:
            DataFrame: 盈利预测数据
        """
        # 方法1: 尝试从 akshare 获取（东方财富数据源）
        try:
            import akshare as ak

            # 获取机构预测数据
            forecast = ak.stock_yjyg_em(symbol=code)
            if not forecast.empty:
                return forecast
        except Exception as e:
            logger.warning(f"akshare 获取盈利预测失败: {e}")

        # 方法2: 从通达信本地 F10 数据库获取
        # 盈利预测数据通常在 F10 的特定文件中
        forecast_data = self._parse_local_forecast(code)
        if forecast_data:
            return forecast_data

        return None

    def _parse_local_forecast(self, code: str) -> Optional[pd.DataFrame]:
        """从通达信本地文件解析盈利预测"""
        # 盈利预测数据通常存储在 F10 数据库中
        # 文件路径: vipdoc/sh[sz]/...（需要具体逆向分析）

        # 这里返回示例数据结构
        # 实际实现需要根据通达信文件格式解析
        return None

    def collect_all(self, code: str) -> Dict:
        """
        采集所有信息

        Args:
            code: 股票代码

        Returns:
            Dict: 包含所有信息的字典
        """
        code = code.zfill(6)
        logger.info(f"开始采集 {code} 综合信息...")

        result = {
            'code': code,
            'quote': self.get_realtime_quote(code),
            'company': self.get_company_info(code),
            'forecast': self.get_earnings_forecast(code)
        }

        return result


def print_stock_info(info: Dict):
    """打印股票综合信息"""
    code = info.get('code', '')

    print("\n" + "=" * 80)
    print(f"  股票代码: {code}")
    print("=" * 80)

    # 实时行情
    quote = info.get('quote')
    if quote:
        print("\n【实时行情】")
        print(f"  当前价格: {quote['price']:.2f} 元")
        print(f"  涨跌幅:   {quote['change_pct']:+.2f}%")
        print(f"  换手率:   {quote['turnover']:.2f}%")
        print(f"  总市值:   {quote['market_cap']:.2f} 亿元")
        print(f"  开盘价:   {quote['open']:.2f} 元")
        print(f"  最高价:   {quote['high']:.2f} 元")
        print(f"  最低价:   {quote['low']:.2f} 元")
        print(f"  昨收价:   {quote['pre_close']:.2f} 元")
        print(f"  成交量:   {quote['volume']:,} 手")

    # 公司信息
    company = info.get('company')
    if company:
        print("\n【公司信息】")
        print(f"  公司名称: {company.get('name', 'N/A')}")
        print(f"  所属行业: {company.get('industry', 'N/A')}")
        print(f"  主营业务: {company.get('main_business', 'N/A')}")
        print(f"  上市日期: {company.get('list_date', 'N/A')}")

    # 盈利预测
    forecast = info.get('forecast')
    if forecast is not None and not forecast.empty:
        print("\n【盈利预测】")
        print(forecast.to_string(index=False))

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='采集股票综合信息')
    parser.add_argument('code', nargs='?', default='688456', help='股票代码')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(message)s')

    collector = StockInfoCollector()
    info = collector.collect_all(args.code)
    print_stock_info(info)
