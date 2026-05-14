#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查未更新名称的股票"""

import sys
sys.path.insert(0, '.')
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

db = MySQLClient(MYSQL_CONFIG)

try:
    # 查询未更新名称的股票（名称仍以'股票'开头）
    sql = 'SELECT code, name FROM stock_list WHERE name LIKE "股票%" LIMIT 20'
    results = db.query_all(sql)
    
    print('未更新名称的股票示例（名称仍为默认值）:')
    for r in results:
        print(f'  {r["code"]}: {r["name"]}')
    
    print()
    print('代码类型分析:')
    
    # 统计各类型代码数量
    sql = '''
    SELECT 
        CASE 
            WHEN code LIKE "6%" THEN "上海市场"
            WHEN code LIKE "0%" THEN "深圳市场"
            WHEN code LIKE "3%" THEN "创业板"
            WHEN code LIKE "8%" THEN "北交所"
            ELSE "其他"
        END AS market_type,
        COUNT(*) as count
    FROM stock_list 
    WHERE name LIKE "股票%"
    GROUP BY market_type
    '''
    results = db.query_all(sql)
    for r in results:
        print(f'  {r["market_type"]}: {r["count"]} 只')
        
finally:
    db.close()