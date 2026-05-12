#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接从东方财富网获取股票名称
"""

import sys
import requests
import json

sys.path.insert(0, '.')
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def get_stock_names_direct():
    """直接从东方财富网获取股票名称"""
    stock_names = {}
    
    try:
        # 东方财富网的API
        url = "http://push2.eastmoney.com/api/qt/clist/get"
        
        # 分批获取
        for page in range(1, 100):  # 最多100页
            params = {
                'pn': page,
                'pz': 100,
                'po': 1,
                'np': 1,
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': 2,
                'invt': 2,
                'fid': 'f3',
                'fs': 'm:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23',
                'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152',
                '_': '1623833763641'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.encoding = 'utf-8'
            
            data = response.json()
            
            if data['data'] and data['data']['diff']:
                for item in data['data']['diff']:
                    code = str(item.get('f12', '')).zfill(6)
                    name = item.get('f14', '')
                    if code and name and code.isdigit():
                        stock_names[code] = name
            
            print(f"第 {page} 页: 已获取 {len(stock_names)} 只股票")
            
            # 如果没有更多数据，退出
            if not data['data']['diff'] or len(data['data']['diff']) < 100:
                break
                
        print(f"总计获取 {len(stock_names)} 只股票名称")
        return stock_names
        
    except Exception as e:
        print(f"获取失败: {e}")
        import traceback
        traceback.print_exc()
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
        
        # 从东方财富网获取股票名称
        stock_names = get_stock_names_direct()
        
        if not stock_names:
            print("无法获取股票名称")
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