#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用通达信资讯主站获取股票名称
"""

import sys
sys.path.insert(0, '.')

from pytdx.hq import TdxHq_API
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def fetch_stock_names_from_tdx():
    """从通达信服务器获取股票名称"""
    # 用户提供的通达信主站
    servers = [
        # 行情主站
        ('120.25.129.1', 7709),
        ('139.196.1.13', 7709),
        # 资讯主站
        ('120.236.1.187', 7709),
        ('42.96.251.80', 7709),
        ('139.196.1.132', 7709),
        ('47.109.68.139', 7709),
        # 备用服务器
        ('120.25.129.112', 7709),
        ('119.147.212.81', 7709),
        ('60.191.116.58', 7709),
        ('60.191.116.167', 7709),
        ('113.108.112.130', 7709),
        ('113.108.144.108', 7709),
    ]
    
    stock_names = {}
    
    for host, port in servers:
        print(f"尝试连接 {host}:{port}...")
        api = TdxHq_API()
        try:
            if api.connect(host, port, time_out=3):
                print("  连接成功")
                
                # 获取上海市场
                print("  获取上海市场股票...")
                start = 0
                while start < 10000:
                    try:
                        data = api.get_security_list(1, start)
                        if not data or len(data) == 0:
                            break
                        for stock in data:
                            code = stock.get('code')
                            name = stock.get('name')
                            if code and name and code.isdigit() and len(code) == 6:
                                stock_names[code] = name
                        start += 80
                    except Exception:
                        break
                
                # 获取深圳市场
                print("  获取深圳市场股票...")
                start = 0
                while start < 10000:
                    try:
                        data = api.get_security_list(0, start)
                        if not data or len(data) == 0:
                            break
                        for stock in data:
                            code = stock.get('code')
                            name = stock.get('name')
                            if code and name and code.isdigit() and len(code) == 6:
                                stock_names[code] = name
                        start += 80
                    except Exception:
                        break
                
                api.disconnect()
                print(f"  从该服务器获取了 {len(stock_names)} 只股票")
                
                # 如果获取了足够多的股票，退出
                if len(stock_names) > 5000:
                    print("  已获取足够多的股票，退出")
                    break
                    
            else:
                print("  连接失败")
                
        except Exception as e:
            print(f"  连接异常: {e}")
    
    return stock_names


def update_stock_names():
    """更新股票名称"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取需要更新的股票代码
        sql = "SELECT code FROM stock_list WHERE name LIKE '股票%'"
        results = db.query_all(sql)
        codes_to_update = {r['code'] for r in results}
        
        print(f"需要更新名称的股票数量: {len(codes_to_update)}")
        
        if not codes_to_update:
            print("没有需要更新的股票")
            return
        
        # 从通达信服务器获取股票名称
        print("\n从通达信服务器获取股票名称...")
        stock_names = fetch_stock_names_from_tdx()
        
        print(f"\n服务器返回 {len(stock_names)} 只股票名称")
        
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
        sql = "SELECT code, name FROM stock_list WHERE name NOT LIKE '股票%' ORDER BY code LIMIT 10"
        for r in db.query_all(sql):
            print(f"  {r['code']}: {r['name']}")
        
    finally:
        db.close()


if __name__ == '__main__':
    update_stock_names()