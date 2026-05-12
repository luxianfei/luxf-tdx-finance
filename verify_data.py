#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证数据是否成功存储到数据库"""

from database import MySQLClient
from config import MYSQL_CONFIG

def main():
    client = MySQLClient(MYSQL_CONFIG)
    
    # 查询688456的财务数据
    data = client.get_stock_finance_history('688456', 5)
    print(f"查询到 {len(data)} 条记录（最近5条）:")
    for d in data:
        print(f"{d['report_date']}: EPS={d['eps_basic']}, ROE={d['roe_diluted']}%, 扣非TTM={d['kfe_np_ttm_w']}万")
    
    # 查询采集日志
    stats = client.get_fetch_stats()
    print(f"\n采集统计:")
    print(f"  总股票数: {stats.get('total_codes', 0)}")
    print(f"  总记录数: {stats.get('total_records', 0)}")
    print(f"  成功数: {stats.get('success_count', 0)}")
    print(f"  失败数: {stats.get('failed_count', 0)}")

if __name__ == "__main__":
    main()