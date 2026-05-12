#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新初始化stock_list表，使用批量插入
"""

import sys
sys.path.insert(0, '.')

from pytdx.hq import TdxHq_API
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG, TDX_DIR
import os


def get_stock_codes_from_local():
    """从本地通达信目录获取股票代码"""
    stock_codes = {}
    
    # 上海市场 (1)
    sh_dir = os.path.join(TDX_DIR, "vipdoc", "sh", "lday")
    if os.path.exists(sh_dir):
        for f in os.listdir(sh_dir):
            if f.endswith('.day'):
                code = f[2:8]
                if code.isdigit() and len(code) == 6:
                    stock_codes[code] = 1  # 1 表示上海
    
    # 深圳市场 (0)
    sz_dir = os.path.join(TDX_DIR, "vipdoc", "sz", "lday")
    if os.path.exists(sz_dir):
        for f in os.listdir(sz_dir):
            if f.endswith('.day'):
                code = f[2:8]
                if code.isdigit() and len(code) == 6:
                    stock_codes[code] = 0  # 0 表示深圳
    
    print(f"从本地通达信目录获取了 {len(stock_codes)} 只股票代码")
    return stock_codes


def is_a_stock(code):
    """判断是否为A股"""
    if not code or not code.isdigit() or len(code) != 6:
        return False
    
    if code.startswith('600') or code.startswith('601') or code.startswith('603') or \
       code.startswith('605') or code.startswith('688'):
        return True
    
    if code.startswith('000') or code.startswith('001') or code.startswith('002') or \
       code.startswith('300') or code.startswith('301'):
        return True
    
    return False


def main():
    """主函数"""
    # 获取本地股票代码
    all_codes = get_stock_codes_from_local()
    
    # 过滤只保留A股
    a_stock_codes = {code: market for code, market in all_codes.items() if is_a_stock(code)}
    print(f"过滤后A股数量: {len(a_stock_codes)}")
    
    # 准备数据 - 使用默认名称，后续再更新
    stock_data = []
    for code, market in a_stock_codes.items():
        stock_data.append((code, f"股票{code}", market))
    
    # 插入数据库
    db = MySQLClient(MYSQL_CONFIG)
    try:
        print("\n清空并重新插入股票数据...")
        conn = db.connect()
        
        with conn.cursor() as cursor:
            # 清空表
            cursor.execute("DELETE FROM stock_list")
            
            # 批量插入
            insert_sql = "INSERT INTO stock_list (code, name, market) VALUES (%s, %s, %s)"
            cursor.executemany(insert_sql, stock_data)
            
            conn.commit()
            print(f"成功插入 {len(stock_data)} 只股票")
        
        # 统计结果
        print("\n统计结果:")
        for prefix in ['600', '601', '603', '605', '688', '000', '001', '002', '300', '301']:
            sql = f"SELECT COUNT(*) as cnt FROM stock_list WHERE code LIKE '{prefix}%'"
            cnt = db.query_one(sql)['cnt']
            print(f"  {prefix}开头: {cnt} 只")
        
    finally:
        db.close()


if __name__ == '__main__':
    main()