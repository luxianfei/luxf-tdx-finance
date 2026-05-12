#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用akshare获取股票名称（简化版）
"""

import sys
import time
import random
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def fetch_stock_names_with_akshare():
    """使用akshare获取股票名称"""
    try:
        import akshare as ak
        
        print("正在从akshare获取A股股票列表...")
        
        # 添加随机延迟，避免被封
        time.sleep(random.uniform(2, 5))
        
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
            return fetch_stock_names_with_akshare()
        except Exception as e:
            print(f"安装akshare失败: {e}")
            return None
    except Exception as e:
        print(f"获取失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_stock_names():
    """更新股票名称"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取股票名称
        stock_names = fetch_stock_names_with_akshare()
        
        if not stock_names:
            print("无法获取股票名称")
            return
        
        # 保存到文件
        with open('stock_names_akshare.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(stock_names.items()):
                f.write(f"{code}\t{name}\n")
        print("股票名称已保存到 stock_names_akshare.txt")
        
        # 获取需要更新的股票代码
        sql = "SELECT code FROM stock_list WHERE name LIKE '股票%'"
        results = db.query_all(sql)
        codes_to_update = {r['code'] for r in results}
        
        print(f"\n需要更新名称的股票数量: {len(codes_to_update)}")
        
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
                    if count % 100 == 0:
                        print(f"  已更新 {count} 只...")
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
        
    finally:
        db.close()


if __name__ == '__main__':
    update_stock_names()