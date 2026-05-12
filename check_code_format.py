#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查股票代码格式
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def check_format():
    """检查代码格式"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取数据库中的代码
        print("数据库中未更新的股票代码:")
        sql = "SELECT code FROM stock_list WHERE name LIKE '股票%' LIMIT 10"
        db_codes = db.query_all(sql)
        for r in db_codes:
            code = r['code']
            print(f"  {repr(code)}")
        
        # 获取文件中的代码
        print("\n文件中的股票代码:")
        with open('a_stock_names.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()[:10]
            for line in lines:
                parts = line.split('\t')
                if parts:
                    print(f"  {repr(parts[0])}")
        
    finally:
        db.close()


if __name__ == '__main__':
    check_format()