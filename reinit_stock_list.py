#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新初始化stock_list表，从通达信服务器获取A股股票名称
"""

import sys
sys.path.insert(0, '.')

from pytdx.hq import TdxHq_API
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG, TDX_DIR
import os


def get_stock_codes_from_local():
    """从本地通达信目录获取股票代码"""
    stock_codes = set()
    
    # 上海市场 (1)
    sh_dir = os.path.join(TDX_DIR, "vipdoc", "sh", "lday")
    if os.path.exists(sh_dir):
        for f in os.listdir(sh_dir):
            if f.endswith('.day'):
                code = f[2:8]  # 提取 shxxx.day 中的 xxx 部分
                if code.isdigit() and len(code) == 6:
                    stock_codes.add((1, code))  # 1 表示上海
    
    # 深圳市场 (0)
    sz_dir = os.path.join(TDX_DIR, "vipdoc", "sz", "lday")
    if os.path.exists(sz_dir):
        for f in os.listdir(sz_dir):
            if f.endswith('.day'):
                code = f[2:8]
                if code.isdigit() and len(code) == 6:
                    stock_codes.add((0, code))  # 0 表示深圳
    
    print(f"从本地通达信目录获取了 {len(stock_codes)} 只股票代码")
    return stock_codes


def fetch_stock_names_from_tdx():
    """从通达信服务器获取股票名称"""
    servers = [
        ('120.25.129.112', 7709),
        ('119.147.212.81', 7709),
        ('124.74.236.94', 7709),
        ('60.191.116.58', 7709),
    ]
    
    stock_names = {}
    
    for host, port in servers:
        print(f"尝试连接 {host}:{port}...")
        api = TdxHq_API()
        try:
            if api.connect(host, port):
                print("  连接成功")
                
                # 获取上海市场
                print("  获取上海市场股票...")
                start = 0
                while True:
                    data = api.get_security_list(1, start)
                    if not data or len(data) == 0:
                        break
                    for stock in data:
                        code = stock.get('code')
                        name = stock.get('name')
                        if code and name and code.isdigit() and len(code) == 6:
                            if code.startswith('6'):  # 上海A股
                                stock_names[code] = name
                    start += 80
                
                # 获取深圳市场
                print("  获取深圳市场股票...")
                start = 0
                while True:
                    data = api.get_security_list(0, start)
                    if not data or len(data) == 0:
                        break
                    for stock in data:
                        code = stock.get('code')
                        name = stock.get('name')
                        if code and name and code.isdigit() and len(code) == 6:
                            if code.startswith(('0', '3')):  # 深圳A股
                                stock_names[code] = name
                    start += 80
                
                api.disconnect()
                print(f"  从该服务器获取了 {len(stock_names)} 只股票")
                
                # 如果获取了足够多的股票，退出
                if len(stock_names) > 5000:
                    break
                    
            else:
                print("  连接失败")
                
        except Exception as e:
            print(f"  连接异常: {e}")
    
    return stock_names


def is_a_stock(code):
    """判断是否为A股"""
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
    
    return False


def update_stock_list():
    """更新stock_list表"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取本地股票代码
        local_codes = get_stock_codes_from_local()
        
        # 过滤只保留A股
        a_stock_codes = {(market, code) for market, code in local_codes if is_a_stock(code)}
        print(f"过滤后A股数量: {len(a_stock_codes)}")
        
        # 从服务器获取股票名称
        print("\n从通达信服务器获取股票名称...")
        stock_names = fetch_stock_names_from_tdx()
        
        print(f"\n服务器返回 {len(stock_names)} 只股票名称")
        
        # 准备插入/更新数据
        conn = db.connect()
        
        # 先清空表（根据用户说已清除无效记录）
        print("清空stock_list表...")
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM stock_list")
            conn.commit()
        
        # 插入新数据
        print("插入股票数据...")
        insert_sql = "INSERT IGNORE INTO stock_list (code, name, market) VALUES (%s, %s, %s)"
        
        with conn.cursor() as cursor:
            count = 0
            for market, code in a_stock_codes:
                name = stock_names.get(code, f"股票{code}")
                cursor.execute(insert_sql, (code, name, market))
                count += 1
            conn.commit()
        
        print(f"成功插入 {count} 只股票")
        
        # 统计结果
        print("\n统计结果:")
        for prefix in ['600', '601', '603', '605', '688', '000', '001', '002', '300', '301']:
            sql = f"SELECT COUNT(*) as cnt FROM stock_list WHERE code LIKE '{prefix}%'"
            cnt = db.query_one(sql)['cnt']
            print(f"  {prefix}开头: {cnt} 只")
        
        # 显示部分结果
        print("\n股票列表示例（前10条）:")
        sql = "SELECT code, name, market FROM stock_list ORDER BY code LIMIT 10"
        for r in db.query_all(sql):
            market_str = "上海" if r['market'] == 1 else "深圳"
            print(f"  {r['code']}: {r['name']} ({market_str})")
        
    finally:
        db.close()


if __name__ == '__main__':
    update_stock_list()