#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从通达信服务器获取A股股票简称并更新到数据库
只处理A股（过滤债券、基金等）
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def is_a_stock(code):
    """判断是否为A股代码"""
    if code.startswith('60') or code.startswith('688'):  # 上海A股
        return True
    if code.startswith('000') or code.startswith('002'):  # 深圳主板/中小板
        return True
    if code.startswith('300') or code.startswith('301'):  # 创业板
        return True
    if code.startswith('83') or code.startswith('87') or code.startswith('88'):  # 北交所
        return True
    return False


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
                if code and name and is_a_stock(code):
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
                if code and name and is_a_stock(code):
                    stock_names[code] = name
            start += 80
        
        api.disconnect()
        print(f"共获取 {len(stock_names)} 只A股股票名称")
        return stock_names
        
    except Exception as e:
        print(f"获取股票名称失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_stock_names_from_tdx():
    """从通达信服务器获取A股股票名称并更新数据库"""
    print("尝试从通达信服务器获取A股股票名称...")
    stock_names = fetch_stock_names_from_tdx()
    
    if not stock_names:
        print("无法获取股票名称")
        return
    
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取数据库中未更新的A股代码
        sql = """
        SELECT code FROM stock_list 
        WHERE name LIKE "股票%" AND 
              (code LIKE "6%" OR code LIKE "0%" OR code LIKE "3%" OR code LIKE "8%")
        """
        results = db.query_all(sql)
        db_codes = {r['code'] for r in results}
        
        print(f"数据库中有 {len(db_codes)} 只A股未更新名称")
        
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
        
        print(f"成功更新 {count} 只A股的名称")
        
        # 验证更新结果
        verify_sql = """
        SELECT code, name FROM stock_list 
        WHERE code LIKE "6%" OR code LIKE "0%" OR code LIKE "3%" OR code LIKE "8%"
        LIMIT 10
        """
        results = db.query_all(verify_sql)
        print("\n更新后的A股列表（前10条）:")
        for r in results:
            print(f"  {r['code']}: {r['name']}")
        
        # 统计剩余未更新数量
        sql = """
        SELECT COUNT(*) as cnt FROM stock_list 
        WHERE name LIKE "股票%" AND 
              (code LIKE "6%" OR code LIKE "0%" OR code LIKE "3%" OR code LIKE "8%")
        """
        result = db.query_one(sql)
        print(f"\n剩余未更新的A股数量: {result['cnt']}")
        
    finally:
        db.close()


if __name__ == '__main__':
    update_stock_names_from_tdx()