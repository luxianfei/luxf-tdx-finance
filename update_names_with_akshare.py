#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 akshare 联网获取股票名称并更新数据库
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def get_stock_names_from_akshare():
    """从 akshare 获取股票简称"""
    try:
        import akshare as ak
        import pandas as pd
        
        print("从 akshare 获取股票列表...")
        
        # 获取沪深A股列表
        df = ak.stock_zh_a_spot_em()
        
        stock_names = {}
        for _, row in df.iterrows():
            code = str(row['代码']).zfill(6)
            name = row['名称']
            stock_names[code] = name
        
        print(f"从 akshare 获取了 {len(stock_names)} 只股票名称")
        return stock_names
        
    except ImportError:
        print("akshare 未安装，正在尝试安装...")
        try:
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "akshare"])
            return get_stock_names_from_akshare()
        except Exception as e:
            print(f"安装 akshare 失败: {e}")
            return None
    except Exception as e:
        print(f"从 akshare 获取股票名称失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_stock_names():
    """使用 akshare 更新股票名称"""
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
        
        if not db_codes:
            print("没有需要更新的股票")
            return
        
        # 从 akshare 获取股票名称
        stock_names = get_stock_names_from_akshare()
        
        if not stock_names:
            print("无法从 akshare 获取股票名称")
            return
        
        # 更新股票名称
        update_sql = "UPDATE stock_list SET name = %s WHERE code = %s"
        
        conn = db.connect()
        with conn.cursor() as cursor:
            count = 0
            for code in db_codes:
                name = stock_names.get(code)
                if name:
                    cursor.execute(update_sql, (name, code))
                    count += 1
            conn.commit()
        
        print(f"成功更新 {count} 只A股的名称")
        
        # 验证更新结果
        verify_sql = """
        SELECT code, name FROM stock_list 
        WHERE name NOT LIKE "股票%" AND 
              (code LIKE "6%" OR code LIKE "0%" OR code LIKE "3%" OR code LIKE "8%")
        ORDER BY code
        LIMIT 20
        """
        results = db.query_all(verify_sql)
        print("\n更新后的A股列表（前20条）:")
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
        
        # 统计已更新数量
        sql_updated = """
        SELECT COUNT(*) as cnt FROM stock_list 
        WHERE name NOT LIKE "股票%" AND 
              (code LIKE "6%" OR code LIKE "0%" OR code LIKE "3%" OR code LIKE "8%")
        """
        result_updated = db.query_one(sql_updated)
        print(f"已更新的A股数量: {result_updated['cnt']}")
        
    finally:
        db.close()


if __name__ == '__main__':
    update_stock_names()