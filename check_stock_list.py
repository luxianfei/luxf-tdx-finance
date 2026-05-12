#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 stock_list 表结构和数据
"""

import sys
sys.path.insert(0, '.')

from database import MySQLClient
from config import MYSQL_CONFIG

def main():
    db = MySQLClient(MYSQL_CONFIG)
    
    # 检查 stock_list 表结构
    print("检查 stock_list 表结构:")
    sql = "DESCRIBE stock_list"
    results = db.query_all(sql)
    for row in results:
        print(f"  {row['Field']} - {row['Type']}")
    
    # 检查 stock_list 表数据
    print("\n检查 stock_list 表数据:")
    sql = "SELECT COUNT(*) as count FROM stock_list"
    result = db.query_one(sql)
    print(f"  总记录数: {result['count']}")
    
    sql = "SELECT * FROM stock_list LIMIT 10"
    results = db.query_all(sql)
    print("  前10条记录:")
    for row in results:
        print(f"    {row}")
    
    # 检查 quarterly_finance 表（可能包含股票信息）
    print("\n检查 quarterly_finance 表:")
    sql = "SELECT COUNT(DISTINCT code) as count FROM quarterly_finance"
    result = db.query_one(sql)
    print(f"  不同股票数量: {result['count']}")
    
    sql = "SELECT DISTINCT code, name FROM quarterly_finance LIMIT 5"
    results = db.query_all(sql)
    print("  前5个股票:")
    for row in results:
        print(f"    {row['code']} - {row['name']}")
    
    db.close()

if __name__ == '__main__':
    main()
