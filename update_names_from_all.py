#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从完整文件更新股票名称到数据库
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def load_stock_names(filepath):
    """从文件加载股票名称"""
    stock_names = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        code = parts[0].strip()
                        name = parts[1].strip()
                        stock_names[code] = name
        print(f"从文件加载了 {len(stock_names)} 只股票名称")
    except Exception as e:
        print(f"加载文件失败: {e}")
    return stock_names


def update_stock_names():
    """更新股票名称"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 从文件加载股票名称
        stock_names = load_stock_names('all_a_stock_names.txt')
        
        if not stock_names:
            print("没有加载到股票名称数据")
            return
        
        # 获取需要更新的股票代码
        sql = "SELECT code FROM stock_list WHERE name LIKE '股票%'"
        results = db.query_all(sql)
        codes_to_update = {r['code'] for r in results}
        
        print(f"需要更新名称的股票数量: {len(codes_to_update)}")
        
        # 匹配并更新
        conn = db.connect()
        update_sql = "UPDATE stock_list SET name = %s WHERE code = %s"
        
        with conn.cursor() as cursor:
            count = 0
            for code in codes_to_update:
                name = stock_names.get(code)
                if name:
                    cursor.execute(update_sql, (name, code))
                    count += 1
                    # 每100只打印一次进度
                    if count % 100 == 0:
                        print(f"  已更新 {count} 只...")
            conn.commit()
        
        print(f"\n成功更新 {count} 只股票的名称")
        
        # 统计结果
        sql_updated = "SELECT COUNT(*) as cnt FROM stock_list WHERE name NOT LIKE '股票%'"
        sql_not_updated = "SELECT COUNT(*) as cnt FROM stock_list WHERE name LIKE '股票%'"
        
        updated = db.query_one(sql_updated)['cnt']
        not_updated = db.query_one(sql_not_updated)['cnt']
        
        print(f"\n统计结果:")
        print(f"  已更新名称: {updated} 只")
        print(f"  未更新名称: {not_updated} 只")
        
        # 显示部分已更新的股票
        print("\n已更新的股票示例:")
        sql = "SELECT code, name FROM stock_list WHERE name NOT LIKE '股票%' ORDER BY code DESC LIMIT 10"
        for r in db.query_all(sql):
            print(f"  {r['code']}: {r['name']}")
        
    finally:
        db.close()


if __name__ == '__main__':
    update_stock_names()