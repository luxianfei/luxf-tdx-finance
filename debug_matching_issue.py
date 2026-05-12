#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试为什么只有部分股票代码匹配成功
"""

import sys
sys.path.insert(0, '.')

from pytdx.hq import TdxHq_API
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def debug_matching():
    """调试代码匹配问题"""
    # 获取数据库中的A股代码
    db = MySQLClient(MYSQL_CONFIG)
    try:
        sql = """
        SELECT code FROM stock_list 
        WHERE code LIKE "6%" OR code LIKE "0%" OR code LIKE "3%" OR code LIKE "8%"
        """
        db_codes = {r['code'] for r in db.query_all(sql)}
        print(f"数据库中有 {len(db_codes)} 只A股")
        
        # 从服务器获取股票代码
        api = TdxHq_API()
        servers = [('120.25.129.112', 7709)]
        
        for host, port in servers:
            try:
                if api.connect(host, port):
                    print(f"\n连接到 {host}:{port}")
                    
                    stock_names = {}
                    
                    # 获取上海市场股票（尝试不同的起始位置）
                    print("获取上海市场股票...")
                    for start in range(0, 10000, 80):
                        data = api.get_security_list(1, start)
                        if not data or len(data) == 0:
                            continue
                        for stock in data:
                            code = stock.get('code')
                            name = stock.get('name')
                            if code and name:
                                # 只保留6位数字代码
                                if code.isdigit() and len(code) == 6:
                                    stock_names[code] = name
                    
                    # 获取深圳市场股票
                    print("获取深圳市场股票...")
                    for start in range(0, 10000, 80):
                        data = api.get_security_list(0, start)
                        if not data or len(data) == 0:
                            continue
                        for stock in data:
                            code = stock.get('code')
                            name = stock.get('name')
                            if code and name:
                                if code.isdigit() and len(code) == 6:
                                    stock_names[code] = name
                    
                    api.disconnect()
                    print(f"\n服务器返回 {len(stock_names)} 只6位数字代码的股票")
                    
                    # 统计匹配情况
                    matched = set(stock_names.keys()) & db_codes
                    print(f"与数据库匹配的数量: {len(matched)}")
                    
                    # 显示一些匹配和不匹配的示例
                    print("\n服务器返回的股票示例（前10条）:")
                    for i, (code, name) in enumerate(list(stock_names.items())[:10]):
                        in_db = "✓" if code in db_codes else "✗"
                        print(f"  {code}: {name} [{in_db}]")
                    
                    # 检查未匹配的数据库代码
                    unmatched_db = db_codes - set(stock_names.keys())
                    print(f"\n数据库中未匹配的A股数量: {len(unmatched_db)}")
                    print("未匹配的A股示例（前10条）:")
                    for code in list(unmatched_db)[:10]:
                        print(f"  {code}")
                    
                    break
                    
            except Exception as e:
                print(f"连接失败: {e}")
    
    finally:
        db.close()


if __name__ == '__main__':
    debug_matching()