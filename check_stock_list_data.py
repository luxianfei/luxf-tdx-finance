#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 stock_list 表当前数据状态
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

def check_stock_list_data():
    """检查 stock_list 表数据状态"""
    db = MySQLClient(MYSQL_CONFIG)
    
    # 查询总数
    result = db.query_one("SELECT COUNT(*) as total FROM stock_list")
    total = result['total']
    
    # 查询已更新名称的股票数（排除占位符）
    result = db.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE name IS NOT NULL AND name != '' AND name NOT LIKE '股票%'")
    name_updated = result['cnt']
    
    # 查询已更新市值的股票数
    result = db.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE market_cap IS NOT NULL")
    market_cap_updated = result['cnt']
    
    # 查询已更新换手率的股票数
    result = db.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE change_pct IS NOT NULL")
    change_pct_updated = result['cnt']
    
    # 查询已更新current_price的股票数
    result = db.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE current_price IS NOT NULL")
    price_updated = result['cnt']
    
    # 查看一些示例数据
    result = db.query_all("SELECT code, name, current_price, change_pct, market_cap, pe_ratio FROM stock_list WHERE name NOT LIKE '股票%' LIMIT 5")
    
    db.close()
    
    print("stock_list 表数据状态:")
    print("-" * 60)
    print(f"股票总数: {total}")
    print(f"已更新名称: {name_updated} ({name_updated/total*100:.1f}%)")
    print(f"已更新市值: {market_cap_updated} ({market_cap_updated/total*100:.1f}%)")
    print(f"已更新涨跌幅: {change_pct_updated} ({change_pct_updated/total*100:.1f}%)")
    print(f"已更新当前价: {price_updated} ({price_updated/total*100:.1f}%)")
    print("-" * 60)
    print("\n示例数据:")
    for row in result:
        print(f"  {row['code']}: {row['name']}, 价格:{row['current_price']}, 涨跌:{row['change_pct']}%, 市值:{row['market_cap']}, PE:{row['pe_ratio']}")

if __name__ == '__main__':
    check_stock_list_data()