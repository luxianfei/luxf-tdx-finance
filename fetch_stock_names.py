#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从通达信服务器获取股票简称并更新到数据库
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def fetch_stock_names_from_tdx():
    """从通达信服务器获取股票简称"""
    try:
        from pytdx.hq import TdxHq_API
        
        servers = [
            ('120.25.129.112', 7709),
            ('119.147.212.81', 7709),
            ('124.74.236.94', 7709),
            ('60.191.116.58', 7709),
            ('60.191.116.167', 7709),
        ]
        
        api = TdxHq_API()
        connected = False
        
        for host, port in servers:
            try:
                if api.connect(host, port):
                    print(f"成功连接到 {host}:{port}")
                    connected = True
                    break
            except Exception as e:
                print(f"连接 {host}:{port} 失败: {e}")
        
        if not connected:
            print("无法连接到任何通达信服务器")
            return None
        
        stock_names = {}
        
        # 获取上海市场股票
        print("获取上海市场股票...")
        start = 0
        while True:
            data = api.get_security_list(1, start)
            if not data or len(data) == 0:
                break
            for stock in data:
                code = stock.get('code')
                name = stock.get('name')
                if code and name:
                    stock_names[code] = name
            start += 80
        
        # 获取深圳市场股票
        print("获取深圳市场股票...")
        start = 0
        while True:
            data = api.get_security_list(0, start)
            if not data or len(data) == 0:
                break
            for stock in data:
                code = stock.get('code')
                name = stock.get('name')
                if code and name:
                    stock_names[code] = name
            start += 80
        
        api.disconnect()
        print(f"共获取 {len(stock_names)} 只股票名称")
        return stock_names
        
    except Exception as e:
        print(f"获取股票名称失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_stock_names_from_tdx():
    """从通达信服务器获取股票名称并更新数据库"""
    print("尝试从通达信服务器获取股票名称...")
    stock_names = fetch_stock_names_from_tdx()
    
    if not stock_names:
        print("无法获取股票名称，将使用公司全称提取简称")
        return
    
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取数据库中已有的股票代码
        sql = "SELECT code FROM stock_list"
        results = db.query_all(sql)
        db_codes = {r['code'] for r in results}
        
        print(f"数据库中有 {len(db_codes)} 只股票")
        
        # 更新股票名称
        update_sql = "UPDATE stock_list SET name = %s WHERE code = %s"
        
        conn = db.connect()
        with conn.cursor() as cursor:
            count = 0
            for code, name in stock_names.items():
                if code in db_codes:
                    cursor.execute(update_sql, (name, code))
                    count += 1
            conn.commit()
        
        print(f"成功更新 {count} 只股票的名称")
        
        # 验证更新结果
        verify_sql = "SELECT code, name FROM stock_list LIMIT 10"
        results = db.query_all(verify_sql)
        print("\n更新后的股票列表（前10条）:")
        for r in results:
            print(f"  {r['code']}: {r['name']}")
        
    finally:
        db.close()


if __name__ == '__main__':
    update_stock_names_from_tdx()