#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 profit_forecast 表结构和数据量
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

def check_profit_forecast():
    """检查盈利预测表"""
    db = MySQLClient(MYSQL_CONFIG)
    
    # 获取表结构
    result = db.query_all("DESCRIBE profit_forecast")
    print("profit_forecast 表结构:")
    print("-" * 60)
    for row in result:
        print(f"{row['Field']}: {row['Type']}")
    
    # 统计数据量
    result = db.query_one("SELECT COUNT(*) as total FROM profit_forecast")
    print(f"\n盈利预测记录总数: {result['total']}")
    
    # 统计有多少只股票有盈利预测数据
    result = db.query_one("SELECT COUNT(DISTINCT code) as count FROM profit_forecast")
    print(f"有盈利预测数据的股票数: {result['count']}")
    
    # 获取股票总数
    result = db.query_one("SELECT COUNT(*) as total FROM stock_list")
    print(f"stock_list 表股票总数: {result['total']}")
    
    # 查看一些示例数据
    result = db.query_all("SELECT code, report_date, eps_forecast, net_profit_forecast FROM profit_forecast LIMIT 10")
    print("\n示例数据:")
    for row in result:
        print(f"  {row['code']}: {row['report_date']}, EPS预测:{row['eps_forecast']}, 净利润预测:{row['net_profit_forecast']}")
    
    db.close()

if __name__ == '__main__':
    check_profit_forecast()