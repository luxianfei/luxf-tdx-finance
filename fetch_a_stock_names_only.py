#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
只从通达信服务器获取A股股票简称
过滤掉概念板块、指数等非股票代码
"""

import sys
sys.path.insert(0, '.')

from pytdx.hq import TdxHq_API
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def is_a_stock(code):
    """判断是否为A股股票代码"""
    if not code or not code.isdigit() or len(code) != 6:
        return False
    
    # 上海A股
    if code.startswith('600') or code.startswith('601') or code.startswith('603') or \
       code.startswith('605') or code.startswith('688'):
        return True
    
    # 深圳A股
    if code.startswith('000') or code.startswith('001') or code.startswith('002') or \
       code.startswith('300') or code.startswith('301'):
        return True
    
    # 北交所
    if code.startswith('83') or code.startswith('87') or code.startswith('88'):
        # 排除880开头的概念板块
        if not code.startswith('880'):
            return True
    
    return False


def fetch_a_stock_names():
    """只获取A股股票名称"""
    api = TdxHq_API()
    servers = [
        ('120.25.129.112', 7709),
        ('119.147.212.81', 7709),
    ]
    
    stock_names = {}
    
    for host, port in servers:
        try:
            if api.connect(host, port):
                print(f"成功连接到 {host}:{port}")
                
                # 获取上海市场股票
                print("获取上海市场股票...")
                for start in range(0, 10000, 80):
                    data = api.get_security_list(1, start)
                    if not data or len(data) == 0:
                        break
                    for stock in data:
                        code = stock.get('code')
                        name = stock.get('name')
                        if code and name and is_a_stock(code):
                            stock_names[code] = name
                
                # 获取深圳市场股票
                print("获取深圳市场股票...")
                for start in range(0, 10000, 80):
                    data = api.get_security_list(0, start)
                    if not data or len(data) == 0:
                        break
                    for stock in data:
                        code = stock.get('code')
                        name = stock.get('name')
                        if code and name and is_a_stock(code):
                            stock_names[code] = name
                
                api.disconnect()
                print(f"共获取 {len(stock_names)} 只A股股票名称")
                return stock_names
                
        except Exception as e:
            print(f"连接 {host}:{port} 失败: {e}")
    
    print("无法连接到任何通达信服务器")
    return None


def update_a_stock_names():
    """更新A股股票名称"""
    print("尝试从通达信服务器获取A股股票名称...")
    stock_names = fetch_a_stock_names()
    
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
        
        print(f"数据库中有 {len(db_codes)} 只未更新名称的A股")
        
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
        WHERE name NOT LIKE "股票%" AND 
              (code LIKE "6%" OR code LIKE "0%" OR code LIKE "3%" OR code LIKE "8%")
        LIMIT 15
        """
        results = db.query_all(verify_sql)
        print("\n更新后的A股列表（前15条）:")
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
    update_a_stock_names()