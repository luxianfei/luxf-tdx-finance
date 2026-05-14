#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""

import sys
sys.path.insert(0, '.')

from database import MySQLClient
from config import MYSQL_CONFIG

def main():
    db = MySQLClient(MYSQL_CONFIG)
    
    # 获取所有表
    sql = "SHOW TABLES"
    tables = db.query_all(sql)
    print("数据库中的表:")
    for table in tables:
        print(f"  - {list(table.values())[0]}")
    
    # 检查 stock_basic 表
    print("\n检查 stock_basic 表:")
    sql = "SELECT COUNT(*) as count FROM stock_basic"
    result = db.query_one(sql)
    print(f"  记录数: {result['count']}")
    
    sql = "SELECT code, name FROM stock_basic LIMIT 5"
    results = db.query_all(sql)
    print("  前5条记录:")
    for row in results:
        print(f"    {row['code']} - {row['name']}")
    
    db.close()

if __name__ == '__main__':
    main()
