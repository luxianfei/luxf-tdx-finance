#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
batch_fetch.py - 全A股批量财务数据采集
================================================================================
功能：批量采集所有A股股票的财务数据，存入MySQL数据库

用法：
    # 初始化数据库（首次运行）
    python batch_fetch.py --init

    # 采集全部A股（首次运行）
    python batch_fetch.py --all

    # 采集指定代码列表
    python batch_fetch.py --codes 688456,000001,600519

    # 增量更新（只采集未完成采集的股票）
    python batch_fetch.py --update

    # 只更新特定市场
    python batch_fetch.py --market sh

    # 设置并发数
    python batch_fetch.py --all --workers 4
================================================================================
"""

import sys
import os
import argparse
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MYSQL_CONFIG, FINANCE_DIR
from fetchers import FinanceCollector
from models import to_mysql_dict
from utils import StockListHelper
from database import MySQLClient

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class BatchFetcher:
    """批量采集器"""

    def __init__(self, mysql_config: dict = None, cache_dir: str = FINANCE_DIR,
                 workers: int = 1):
        """
        初始化

        Args:
            mysql_config: MySQL 配置
            cache_dir: 缓存目录
            workers: 并发数
        """
        self.mysql_config = mysql_config or MYSQL_CONFIG
        self.cache_dir = cache_dir
        self.workers = workers
        self.collector = FinanceCollector(cache_dir=cache_dir)
        self.client = MySQLClient(self.mysql_config)

    def init_database(self):
        """初始化数据库"""
        logger.info("初始化数据库...")
        try:
            self.client.init_tables()
            logger.info("✓ 数据库初始化完成")
        except Exception as e:
            logger.error(f"✗ 数据库初始化失败: {e}")
            raise

    def fetch_one(self, code: str, max_quarters: int = 16) -> Dict:
        """
        采集单个股票

        Args:
            code: 股票代码
            max_quarters: 最大季度数

        Returns:
            Dict: 结果字典
        """
        start_time = time.time()
        try:
            result = self.collector.collect_to_dict(code, max_quarters)
            df = result['dataframe']

            # 保存到 MySQL
            with MySQLClient(self.mysql_config) as client:
                records = to_mysql_dict(df, code)
                count = client.batch_insert_quarterly_finance(records)
                client.log_fetch(code, result['latest_report_date'], 'success',
                               f'插入 {count} 条', count)

            elapsed = time.time() - start_time
            return {
                'code': code,
                'status': 'success',
                'records': len(df),
                'time': elapsed,
            }

        except Exception as e:
            elapsed = time.time() - start_time
            with MySQLClient(self.mysql_config) as client:
                client.log_fetch(code, None, 'failed', str(e), 0)

            return {
                'code': code,
                'status': 'failed',
                'error': str(e),
                'time': elapsed,
            }

    def batch_fetch(self, codes: List[str], max_quarters: int = 16,
                    progress: bool = True) -> Dict:
        """
        批量采集

        Args:
            codes: 股票代码列表
            max_quarters: 最大季度数
            progress: 是否显示进度

        Returns:
            Dict: 统计结果
        """
        total = len(codes)
        success = 0
        failed = 0
        start_time = time.time()

        logger.info(f"\n开始批量采集 {total} 只股票...")

        if self.workers > 1:
            # 并发模式
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = {
                    executor.submit(self.fetch_one, code, max_quarters): code
                    for code in codes
                }

                for idx, future in enumerate(as_completed(futures), 1):
                    result = future.result()
                    if result['status'] == 'success':
                        success += 1
                        status = '✓'
                    else:
                        failed += 1
                        status = '✗'

                    if progress:
                        elapsed = time.time() - start_time
                        logger.info(
                            f"[{idx:>4}/{total}] {status} {result['code']} "
                            f"({result.get('records', 0)}条, {result['time']:.1f}s) "
                            f"- 累计 {elapsed:.0f}s"
                        )
        else:
            # 串行模式
            for idx, code in enumerate(codes, 1):
                result = self.fetch_one(code, max_quarters)
                if result['status'] == 'success':
                    success += 1
                    status = '✓'
                else:
                    failed += 1
                    status = '✗'

                if progress:
                    elapsed = time.time() - start_time
                    logger.info(
                        f"[{idx:>4}/{total}] {status} {result['code']} "
                        f"({result.get('records', 0)}条, {result['time']:.1f}s) "
                        f"- 累计 {elapsed:.0f}s"
                    )

        total_time = time.time() - start_time

        stats = {
            'total': total,
            'success': success,
            'failed': failed,
            'time': total_time,
            'avg_time': total_time / total if total > 0 else 0,
        }

        return stats

    def fetch_all(self, market: str = None, max_quarters: int = 16) -> Dict:
        """
        采集全部A股

        Args:
            market: 市场过滤 ("sh", "sz", None表示全部)
            max_quarters: 最大季度数

        Returns:
            Dict: 统计结果
        """
        logger.info("获取股票列表...")
        helper = StockListHelper()
        codes = helper.get_all_codes()

        if market:
            codes = helper.filter_codes(codes, market=market)

        logger.info(f"股票列表: {len(codes)} 只")
        return self.batch_fetch(codes, max_quarters)

    def update_missing(self, max_quarters: int = 16) -> Dict:
        """
        增量更新：只采集未完成的股票

        Returns:
            Dict: 统计结果
        """
        logger.info("获取未采集的股票列表...")
        helper = StockListHelper()
        all_codes = helper.get_all_codes()

        with MySQLClient(self.mysql_config) as client:
            missing_codes = client.get_missing_codes(all_codes)

        logger.info(f"待采集股票: {len(missing_codes)} 只")
        if not missing_codes:
            logger.info("✓ 所有股票已采集完成")
            return {'total': 0, 'success': 0, 'failed': 0}

        return self.batch_fetch(missing_codes, max_quarters)

    def get_stats(self) -> Dict:
        """获取采集统计"""
        try:
            with MySQLClient(self.mysql_config) as client:
                return client.get_fetch_stats()
        except Exception as e:
            logger.error(f"获取统计失败: {e}")
            return {}


def print_stats(stats: Dict, title: str = "采集统计"):
    """打印统计信息"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)
    print(f"  总计:     {stats.get('total', 0)}")
    print(f"  成功:     {stats.get('success', 0)}")
    print(f"  失败:     {stats.get('failed', 0)}")
    if stats.get('time'):
        print(f"  总耗时:   {stats['time']:.1f} 秒")
        print(f"  平均耗时: {stats.get('avg_time', 0):.2f} 秒/只")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='全A股财务数据批量采集')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--all', action='store_true', help='采集全部A股')
    parser.add_argument('--update', action='store_true', help='增量更新未采集的股票')
    parser.add_argument('--codes', type=str, help='指定股票代码（逗号分隔）')
    parser.add_argument('--market', type=str, choices=['sh', 'sz'], help='只采集特定市场')
    parser.add_argument('--quarters', '-n', type=int, default=16, help='采集季度数')
    parser.add_argument('--workers', '-w', type=int, default=1, help='并发数')
    parser.add_argument('--cache-dir', '-c', default=FINANCE_DIR, help='缓存目录')
    parser.add_argument('--no-progress', action='store_true', help='不显示详细进度')

    args = parser.parse_args()

    # 创建采集器
    fetcher = BatchFetcher(
        mysql_config=MYSQL_CONFIG,
        cache_dir=args.cache_dir,
        workers=args.workers
    )

    # 初始化数据库
    if args.init:
        fetcher.init_database()
        return

    # 显示当前统计
    stats = fetcher.get_stats()
    if stats.get('total_codes', 0) > 0:
        print_stats(stats, "当前数据库状态")

    # 批量采集
    if args.all:
        result = fetcher.fetch_all(market=args.market, max_quarters=args.quarters)
        print_stats(result, "采集完成")

    elif args.update:
        result = fetcher.update_missing(max_quarters=args.quarters)
        print_stats(result, "增量更新完成")

    elif args.codes:
        codes = [c.strip().zfill(6) for c in args.codes.split(',')]
        result = fetcher.batch_fetch(codes, max_quarters=args.quarters,
                                     progress=not args.no_progress)
        print_stats(result, "指定代码采集完成")

    else:
        parser.print_help()
        print("\n示例:")
        print("  python batch_fetch.py --init              # 初始化数据库")
        print("  python batch_fetch.py --all               # 采集全部A股")
        print("  python batch_fetch.py --update            # 增量更新")
        print("  python batch_fetch.py --codes 688456,000001  # 指定代码")


if __name__ == "__main__":
    main()
