#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尝试获取这17只股票的名称
"""

import sys
import time
import random
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def try_fetch_missing_names():
    """尝试获取缺失的股票名称"""
    try:
        import akshare as ak
        
        missing_codes = [
            '000044', '000122', '000300', '000687', '000689', '000699', '000847',
            '000986', '000991', '000992', '600200', '600355', '603056',
            '002231', '300344', '300379', '300391'
        ]
        
        print("尝试使用 stock_zh_a_spot() 获取股票名称...")
        time.sleep(random.uniform(1, 2))
        
        try:
            df = ak.stock_zh_a_spot()
            print(f"成功获取 {len(df)} 只股票")
            
            # 创建代码到名称的映射
            name_map = {}
            for _, row in df.iterrows():
                code = str(row['代码']).zfill(6)
                name = row['名称']
                name_map[code] = name
            
            # 检查缺失的代码
            found = {}
            for code in missing_codes:
                if code in name_map:
                    found[code] = name_map[code]
                    print(f"  ✓ {code}: {name_map[code]}")
                else:
                    print(f"  ✗ {code}: 未找到")
            
            print(f"\n共找到 {len(found)} 只缺失股票的名称")
            
            if found:
                # 保存到文件
                with open('missing_stock_names.txt', 'w', encoding='utf-8') as f:
                    for code, name in sorted(found.items()):
                        f.write(f"{code}\t{name}\n")
                print("已保存到 missing_stock_names.txt")
            
            return found
            
        except Exception as e:
            print(f"stock_zh_a_spot() 失败: {e}")
            return None
            
    except Exception as e:
        print(f"导入akshare失败: {e}")
        return None


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
        
        # 统计结果
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
    names = try_fetch_missing_names()
    if names:
        update_remaining_names(names)