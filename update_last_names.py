#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用通达信的get_security_quotes接口获取剩余股票名称
"""

import sys
import time
import random
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

try:
    from pytdx.hq import TdxHq_API
    HAS_PYTDX = True
except ImportError:
    HAS_PYTDX = False


# 通达信服务器列表
TDX_SERVERS = [
    ('139.196.1.132', 7709),
    ('120.25.129.112', 7709),
    ('183.239.132.37', 7709),
    ('120.196.127.88', 7709),
]


def get_market_code(code):
    """判断市场"""
    if code.startswith(('0', '2', '3')):
        return 0  # 深圳
    elif code.startswith(('6', '5')):
        return 1  # 上海
    return 1


def fetch_remaining_names():
    """获取剩余股票名称"""
    remaining_codes = [
        '000044', '000122', '000300', '000847',
        '000986', '000991', '000992'
    ]
    
    if not HAS_PYTDX:
        print("pytdx未安装")
        return {}
    
    api = TdxHq_API()
    found = {}
    
    print("使用 get_security_quotes 查询...")
    print()
    
    for host, port in TDX_SERVERS:
        print(f"尝试连接 {host}:{port}...")
        
        try:
            if api.connect(host, port):
                print(f"  连接成功")
                
                for code in remaining_codes:
                    if code in found:
                        continue
                    
                    market = get_market_code(code)
                    print(f"    查询 {code}...", end=" ", flush=True)
                    
                    try:
                        data = api.get_security_quotes([(market, code)])
                        if data and len(data) > 0:
                            quote = data[0]
                            name = quote.get('name', '')
                            if name:
                                found[code] = name
                                print(f"✓ 找到: {name}")
                            else:
                                print(f"✗ 无名称")
                        else:
                            print(f"✗ 无数据")
                    except Exception as e:
                        print(f"✗ 查询失败: {e}")
                    
                    time.sleep(0.2)
                
                api.disconnect()
                
                if len(found) == len(remaining_codes):
                    print(f"  全部找到，退出")
                    break
                
            else:
                print(f"  连接失败")
                
        except Exception as e:
            print(f"  连接异常: {e}")
    
    print()
    print(f"共找到 {len(found)} 只股票的名称")
    
    if found:
        with open('remaining_stock_names.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(found.items()):
                f.write(f"{code}\t{name}\n")
        print("已保存到 remaining_stock_names.txt")
    
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
        
        if not_updated > 0:
            print("\n剩余未更新股票:")
            sql = "SELECT code, name FROM stock_list WHERE name LIKE '股票%'"
            for row in db.query_all(sql):
                print(f"  {row['code']}: {row['name']}")
        
    finally:
        db.close()


if __name__ == '__main__':
    names = fetch_remaining_names()
    if names:
        update_remaining_names(names)