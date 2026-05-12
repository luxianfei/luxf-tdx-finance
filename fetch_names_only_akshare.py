#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
仅从akshare获取股票名称并更新数据库
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def get_stock_names_from_akshare():
    """从akshare获取股票名称"""
    try:
        import akshare as ak
        import pandas as pd
        
        print("正在从akshare获取A股股票列表...")
        
        # 获取所有A股股票
        df = ak.stock_zh_a_spot_em()
        
        stock_names = {}
        for _, row in df.iterrows():
            code = str(row['代码']).zfill(6)
            name = row['名称']
            stock_names[code] = name
        
        print(f"成功获取 {len(stock_names)} 只股票名称")
        return stock_names
        
    except ImportError:
        print("akshare未安装，正在安装...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "akshare"])
            return get_stock_names_from_akshare()
        except Exception as e:
            print(f"安装akshare失败: {e}")
            return None
    except Exception as e:
        print(f"获取失败: {e}")
        return None


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
        
        # 从akshare获取股票名称
        stock_names = get_stock_names_from_akshare()
        
        if not stock_names:
            print("无法从akshare获取股票名称")
            return
        
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
        
        print(f"成功更新 {count} 只股票的名称")
        
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