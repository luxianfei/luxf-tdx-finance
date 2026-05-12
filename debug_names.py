#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试名称更新
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

def debug_names():
    """调试名称"""
    db = MySQLClient(MYSQL_CONFIG)
    
    # 查询前10条记录
    result = db.query_all("SELECT code, name FROM stock_list LIMIT 10")
    print("前10条记录:")
    for row in result:
        print(f"  {row['code']}: '{row['name']}'")
    
    # 查询特定代码
    result = db.query_one("SELECT code, name FROM stock_list WHERE code = '000001'")
    print(f"\n000001: '{result['name']}'")
    
    # 统计名称长度
    result = db.query_all("SELECT code, name, LENGTH(name) as name_len FROM stock_list LIMIT 10")
    print("\n名称长度:")
    for row in result:
        print(f"  {row['code']}: '{row['name']}' (长度:{row['name_len']})")
    
    db.close()

if __name__ == '__main__':
    debug_names()