#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 stock_list 表中名称的实际情况
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

def check_stock_names():
    """检查股票名称情况"""
    db = MySQLClient(MYSQL_CONFIG)
    
    # 查询不同名称类型的数量
    result = db.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE name LIKE '股票%'")
    placeholder_count = result['cnt']
    
    result = db.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE name IS NOT NULL AND name != '' AND name NOT LIKE '股票%'")
    real_name_count = result['cnt']
    
    result = db.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE name IS NULL OR name = ''")
    null_count = result['cnt']
    
    # 查看一些示例
    result = db.query_all("SELECT code, name, current_price, market_cap FROM stock_list WHERE name NOT LIKE '股票%' AND name IS NOT NULL AND name != '' LIMIT 10")
    
    print("股票名称统计:")
    print("-" * 60)
    print(f"占位符名称(股票****): {placeholder_count}")
    print(f"真实名称: {real_name_count}")
    print(f"空名称: {null_count}")
    print("-" * 60)
    
    if real_name_count > 0:
        print("\n有真实名称的股票示例:")
        for row in result:
            print(f"  {row['code']}: {row['name']}, 价格:{row['current_price']}, 市值:{row['market_cap']}")
    else:
        print("\n还没有真实名称的股票")
        # 查看占位符示例
        result = db.query_all("SELECT code, name, current_price, market_cap FROM stock_list WHERE current_price IS NOT NULL LIMIT 10")
        print("\n已更新价格的股票示例:")
        for row in result:
            print(f"  {row['code']}: {row['name']}, 价格:{row['current_price']}, 市值:{row['market_cap']}")
    
    db.close()

if __name__ == '__main__':
    check_stock_names()