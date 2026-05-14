#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 stock_list 表结构
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

def check_stock_list_schema():
    """检查 stock_list 表结构"""
    db = MySQLClient(MYSQL_CONFIG)
    
    # 查询表结构
    sql = "DESCRIBE stock_list"
    result = db.query_all(sql)
    
    print("stock_list 表结构:")
    print("-" * 60)
    print(f"{'字段名':<20} {'类型':<20} {'是否为空':<10} {'键':<10}")
    print("-" * 60)
    for row in result:
        print(f"{row['Field']:<20} {row['Type']:<20} {row['Null']:<10} {row['Key']:<10}")
    
    db.close()

if __name__ == '__main__':
    check_stock_list_schema()