#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
main.py - 单股票财务数据采集
================================================================================
用法：
    python main.py 688456          # 采集单只股票
    python main.py 688456 --mysql  # 采集并存入 MySQL
================================================================================
"""

import sys
import os
import argparse
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MYSQL_CONFIG, FINANCE_DIR
from fetchers import FinanceCollector
from models import to_mysql_dict
try:
    from database import MySQLClient
    MYSQL_AVAILABLE = True
except ImportError:
    MySQLClient = None
    MYSQL_AVAILABLE = False
    logger.warning("pymysql 未安装，将跳过 MySQL 保存功能")

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


def print_table(df):
    """打印表格"""
    print("\n" + "=" * 120)
    print(f"  {df['code'].iloc[0]} 季度财务数据")
    print("=" * 120)

    # 表头
    headers = ["报告期", "季度", "EPS", "毛利率%", "ROE%", "扣非TTM(万)", "营收YoY%", "扣非YoY%"]
    print("  " + "  ".join(f"{h:>14}" for h in headers))
    print("  " + "-" * 120)

    # 数据行
    for _, row in df.iterrows():
        q = f"{row['年份']}Q{row['季度']}"
        line = f"  {row['报告期']:>14}"
        line += f"  {q:>14}"
        line += f"  {row.get('eps_basic', 0):>14.4f}"
        line += f"  {row.get('gross_margin', 0):>14.2f}"
        line += f"  {row.get('roe_diluted', 0):>14.2f}"
        kf_ttm = row.get('kfe_np_ttm_w') or 0
        line += f"  {kf_ttm:>14,.0f}"
        rev_yoy = row.get('revenue_yoy') or 0
        line += f"  {rev_yoy:>14.2f}"
        kf_yoy = row.get('kfe_np_yoy') or 0
        line += f"  {kf_yoy:>14.2f}"
        print(line)


def save_to_mysql(code: str, df, mysql_config: dict = None):
    """
    保存数据到 MySQL

    Args:
        code: 股票代码
        df: 财务数据 DataFrame
        mysql_config: MySQL 配置
    """
    if not MYSQL_AVAILABLE:
        logger.warning("MySQL 功能不可用（pymysql 未安装）")
        return

    if mysql_config is None:
        mysql_config = MYSQL_CONFIG

    try:
        with MySQLClient(mysql_config) as client:
            # 初始化表
            client.init_tables()

            # 转换数据格式
            records = to_mysql_dict(df, code)

            # 批量插入
            count = client.batch_insert_quarterly_finance(records)
            logger.info(f"✓ 成功插入 {count} 条记录到 MySQL")

            # 记录日志
            client.log_fetch(code, int(df['报告期'].max()), 'success',
                            f'插入 {count} 条记录', count)

    except Exception as e:
        logger.error(f"✗ MySQL 保存失败: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description='采集单只股票财务数据')
    parser.add_argument('code', nargs='?', default='688456', help='股票代码')
    parser.add_argument('--quarters', '-n', type=int, default=20, 
                        help='采集季度数（默认20，包含用于计算同比的额外4个季度）')
    parser.add_argument('--mysql', '-m', action='store_true', help='保存到 MySQL')
    parser.add_argument('--cache-dir', '-c', default=FINANCE_DIR, help='缓存目录')

    args = parser.parse_args()

    code = args.code.zfill(6)  # 统一6位代码
    logger.info(f"=" * 60)
    logger.info(f"  股票代码: {code}")
    logger.info(f"  采集季度: {args.quarters}")
    logger.info(f"  缓存目录: {args.cache_dir}")
    logger.info(f"  说明: 采集20个季度以支持16个季度的同比计算")
    logger.info(f"=" * 60)

    # 采集数据
    collector = FinanceCollector(cache_dir=args.cache_dir)

    try:
        result = collector.collect_to_dict(code, max_quarters=args.quarters)
        df = result['dataframe']

        # 打印结果
        print_table(df)

        # 保存到 MySQL
        if args.mysql:
            if MYSQL_AVAILABLE:
                save_to_mysql(code, df)
            else:
                logger.warning("⚠️ pymysql 未安装，无法保存到 MySQL")
        else:
            logger.info("（使用 --mysql 参数可保存到数据库）")

        logger.info(f"\n✓ 采集完成: {code}")

    except ValueError as e:
        logger.error(f"✗ 采集失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
