#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查表结构
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

def check_stock_list_structure():
    """检查 stock_list 表结构"""
    db = MySQLClient(MYSQL_CONFIG)
    
    # 获取表结构
    result = db.query_all("DESCRIBE stock_list")
    print("stock_list 表结构:")
    print("-" * 60)
    for row in result:
        print(f"{row['Field']}: {row['Type']}")
    
    # 查看600011的数据
    result = db.query_one("SELECT code, name, current_price, change_pct, market_cap FROM stock_list WHERE code = '600011'")
    print("\n600011 的数据:")
    print(f"  code: {result.get('code')}")
    print(f"  name: {result.get('name')}")
    print(f"  current_price: {result.get('current_price')}")
    print(f"  change_pct: {result.get('change_pct')}")
    print(f"  market_cap: {result.get('market_cap')}")
    
    db.close()

if __name__ == '__main__':
    check_stock_list_structure()