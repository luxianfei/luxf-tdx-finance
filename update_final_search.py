#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用get_security_list在更大范围搜索剩余股票的名称
"""

import sys
import time
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

try:
    from pytdx.hq import TdxHq_API
    HAS_PYTDX = True
except ImportError:
    HAS_PYTDX = False


TDX_SERVERS = [
    ('139.196.1.132', 7709),
    ('120.25.129.112', 7709),
]


def search_remaining_names():
    """搜索剩余股票名称"""
    remaining_codes = {
        '000044', '000122', '000300', '000847',
        '000986', '000991', '000992'
    }
    
    if not HAS_PYTDX:
        print("pytdx未安装")
        return {}
    
    api = TdxHq_API()
    found = {}
    
    print("使用 get_security_list 大范围搜索...")
    print()
    
    for host, port in TDX_SERVERS:
        print(f"连接 {host}:{port}...")
        
        try:
            if api.connect(host, port):
                print(f"  连接成功")
                
                # 搜索深圳市场 (0) - 更大范围
                print(f"  搜索深圳市场...")
                for start in range(0, 10000, 80):
                    if len(found) >= len(remaining_codes):
                        break
                    
                    try:
                        data = api.get_security_list(0, start)
                        if not data:
                            break
                        
                        for stock in data:
                            code = stock.get('code', '')
                            if code in remaining_codes and code not in found:
                                name = stock.get('name', '')
                                if name:
                                    found[code] = name
                                    print(f"    ✓ 找到 {code}: {name}")
                                    
                    except Exception as e:
                        break
                
                # 搜索上海市场 (1) - 更大范围
                if len(found) < len(remaining_codes):
                    print(f"  搜索上海市场...")
                    for start in range(0, 10000, 80):
                        if len(found) >= len(remaining_codes):
                            break
                        
                        try:
                            data = api.get_security_list(1, start)
                            if not data:
                                break
                            
                            for stock in data:
                                code = stock.get('code', '')
                                if code in remaining_codes and code not in found:
                                    name = stock.get('name', '')
                                    if name:
                                        found[code] = name
                                        print(f"    ✓ 找到 {code}: {name}")
                                        
                        except Exception as e:
                            break
                
                api.disconnect()
                print()
                
                if len(found) >= len(remaining_codes):
                    break
            else:
                print(f"  连接失败")
                
        except Exception as e:
            print(f"  异常: {e}")
    
    print(f"共找到 {len(found)} 只股票的名称")
    
    if found:
        with open('final_stock_names.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(found.items()):
                f.write(f"{code}\t{name}\n")
        print("已保存到 final_stock_names.txt")
    
    # 报告未找到的
    not_found = remaining_codes - set(found.keys())
    if not_found:
        print(f"\n未找到的股票: {sorted(not_found)}")
    
    return found


def update_final_names(names):
    """更新最后剩余的股票名称"""
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
        
        if not_updated > 0:
            print("\n剩余未更新股票:")
            sql = "SELECT code, name FROM stock_list WHERE name LIKE '股票%'"
            for row in db.query_all(sql):
                print(f"  {row['code']}: {row['name']}")
        
    finally:
        db.close()


if __name__ == '__main__':
    names = search_remaining_names()
    if names:
        update_final_names(names)