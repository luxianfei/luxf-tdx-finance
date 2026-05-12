#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查财务数据采集进度
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

def check_finance_progress():
    """检查财务数据采集进度"""
    db = MySQLClient(MYSQL_CONFIG)
    
    # 查询季度财务数据总量
    result = db.query_one("SELECT COUNT(*) as total FROM quarterly_finance")
    total = result['total']
    
    # 查询已更新updated_at的记录数
    result = db.query_one("SELECT COUNT(*) as updated FROM quarterly_finance WHERE updated_at IS NOT NULL")
    updated = result['updated']
    
    # 查询股票总数
    result = db.query_one("SELECT COUNT(*) as stocks FROM stock_list")
    stocks = result['stocks']
    
    # 查询有财务数据的股票数
    result = db.query_one("SELECT COUNT(DISTINCT code) as stocks_with_data FROM quarterly_finance")
    stocks_with_data = result['stocks_with_data']
    
    db.close()
    
    print("财务数据采集进度:")
    print("-" * 60)
    print(f"股票总数: {stocks}")
    print(f"已采集财务数据的股票数: {stocks_with_data} ({(stocks_with_data/stocks*100):.1f}%)")
    print(f"季度财务记录总数: {total}")
    print(f"已更新updated_at的记录数: {updated}")
    print(f"平均每只股票季度数: {total/stocks_with_data:.1f}" if stocks_with_data > 0 else "暂无数据")

if __name__ == '__main__':
    check_finance_progress()