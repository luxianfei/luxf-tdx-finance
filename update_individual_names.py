#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用stock_individual_info_em逐个查询缺失股票的名称
"""

import sys
import time
import random
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def fetch_individual_stock_name(code):
    """获取单个股票的名称"""
    try:
        import akshare as ak
        
        time.sleep(random.uniform(0.5, 1.5))
        
        df = ak.stock_individual_info_em(symbol=code)
        
        # 查找股票简称
        name_row = df[df['item'] == '股票简称']
        if len(name_row) > 0:
            return name_row['value'].values[0]
        
        return None
        
    except Exception as e:
        return None


def fetch_missing_names():
    """获取缺失股票的名称"""
    missing_codes = [
        '000044', '000122', '000300', '000687', '000689', '000699', '000847',
        '000986', '000991', '000992', '600200', '600355', '603056',
        '002231', '300344', '300379', '300391'
    ]
    
    print("使用 stock_individual_info_em 逐个查询...")
    print()
    
    found = {}
    for i, code in enumerate(missing_codes, 1):
        print(f"[{i}/{len(missing_codes)}] 查询 {code}...", end=" ")
        
        name = fetch_individual_stock_name(code)
        
        if name:
            found[code] = name
            print(f"✓ 找到: {name}")
        else:
            print(f"✗ 未找到")
    
    print()
    print(f"共找到 {len(found)} 只缺失股票的名称")
    
    if found:
        with open('missing_stock_names.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(found.items()):
                f.write(f"{code}\t{name}\n")
        print("已保存到 missing_stock_names.txt")
    
    return found


def update_remaining_names(names):
    """更新剩余股票名称"""
    if not names:
        print("没有可用的股票名称数据")
        return
    
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        conn = db.connect()
        update_sql = "UPDATE stock_list SET name = %s WHERE code = %s"
        
        count = 0
        with conn.cursor() as cursor:
            for code, name in names.items():
                cursor.execute(update_sql, (name, code))
                count += 1
                print(f"  更新 {code}: {name}")
            conn.commit()
        
        print(f"\n成功更新 {count} 只股票的名称")
        
        sql_updated = "SELECT COUNT(*) as cnt FROM stock_list WHERE name NOT LIKE '股票%'"
        sql_not_updated = "SELECT COUNT(*) as cnt FROM stock_list WHERE name LIKE '股票%'"
        
        updated = db.query_one(sql_updated)['cnt']
        not_updated = db.query_one(sql_not_updated)['cnt']
        
        print(f"\n最终统计结果:")
        print(f"  已更新名称: {updated} 只")
        print(f"  未更新名称: {not_updated} 只")
        
    finally:
        db.close()


if __name__ == '__main__':
    names = fetch_missing_names()
    if names:
        update_remaining_names(names)