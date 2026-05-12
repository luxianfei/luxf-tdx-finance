#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查数据库中代码的格式"""

import sys
sys.path.insert(0, '.')
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

db = MySQLClient(MYSQL_CONFIG)

try:
    # 获取未更新的A股代码
    sql = """
    SELECT code FROM stock_list 
    WHERE name LIKE "股票%" AND 
          (code LIKE "6%" OR code LIKE "0%" OR code LIKE "3%" OR code LIKE "8%")
    LIMIT 10
    """
    results = db.query_all(sql)
    
    print('数据库中未更新的A股代码格式:')
    for r in results:
        code = r['code']
        print(f'  代码:{repr(code)}, 长度:{len(code)}, 类型:{type(code)}')
    
    print()
    print('已更新的A股代码格式:')
    sql = """
    SELECT code FROM stock_list 
    WHERE name NOT LIKE "股票%" AND 
          (code LIKE "6%" OR code LIKE "0%" OR code LIKE "3%" OR code LIKE "8%")
    LIMIT 10
    """
    results = db.query_all(sql)
    for r in results:
        code = r['code']
        print(f'  代码:{repr(code)}, 长度:{len(code)}, 类型:{type(code)}')
        
finally:
    db.close()