#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用网络API获取股票名称
"""

import sys
sys.path.insert(0, '.')

import requests
import json

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def fetch_stock_names():
    """获取股票名称"""
    stock_names = {}
    
    try:
        # 尝试多个API
        apis = [
            # 东方财富网API
            {
                'url': 'http://push2.eastmoney.com/api/qt/clist/get',
                'params': {
                    'pn': 1,
                    'pz': 100,
                    'po': 1,
                    'np': 1,
                    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                    'fltt': 2,
                    'invt': 2,
                    'fid': 'f3',
                    'fs': 'm:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23',
                    'fields': 'f12,f14',
                }
            },
            # 新浪财经API
            {
                'url': 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData',
                'params': {
                    'page': 1,
                    'num': 100,
                    'sort': 'symbol',
                    'asc': 1,
                    'node': 'hs_a',
                    'symbol': '',
                    '_s_r_a': 'page',
                }
            }
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'http://quote.eastmoney.com/',
        }
        
        for api_info in apis:
            print(f"尝试API: {api_info['url']}")
            
            try:
                response = requests.get(api_info['url'], params=api_info['params'], headers=headers, timeout=30)
                response.encoding = 'utf-8'
                
                data = response.json()
                
                if 'data' in data and 'diff' in data['data']:
                    # 东方财富网格式
                    for item in data['data']['diff']:
                        code = str(item.get('f12', '')).zfill(6)
                        name = item.get('f14', '')
                        if code and name and code.isdigit() and len(code) == 6:
                            stock_names[code] = name
                elif isinstance(data, list):
                    # 新浪财经格式
                    for item in data:
                        code = str(item.get('symbol', '')).zfill(6)
                        name = item.get('name', '')
                        if code and name and code.isdigit() and len(code) == 6:
                            stock_names[code] = name
                
                print(f"  获取了 {len(stock_names)} 只股票")
                
                if len(stock_names) > 5000:
                    break
                    
            except Exception as e:
                print(f"  API失败: {e}")
                continue
        
        # 尝试获取上海A股
        print("\n尝试获取上海A股...")
        sh_url = 'http://push2.eastmoney.com/api/qt/clist/get'
        for page in range(1, 50):
            params = {
                'pn': page,
                'pz': 100,
                'po': 1,
                'np': 1,
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': 2,
                'invt': 2,
                'fid': 'f3',
                'fs': 'm:1+t:2,m:1+t:23',  # 上海A股
                'fields': 'f12,f14',
            }
            try:
                response = requests.get(sh_url, params=params, headers=headers, timeout=30)
                data = response.json()
                
                if data['data'] and data['data']['diff']:
                    for item in data['data']['diff']:
                        code = str(item.get('f12', '')).zfill(6)
                        name = item.get('f14', '')
                        if code and name and code.isdigit() and len(code) == 6:
                            stock_names[code] = name
                else:
                    break
            except Exception as e:
                print(f"  第{page}页失败: {e}")
                break
        
        # 尝试获取深圳A股
        print("\n尝试获取深圳A股...")
        sz_url = 'http://push2.eastmoney.com/api/qt/clist/get'
        for page in range(1, 50):
            params = {
                'pn': page,
                'pz': 100,
                'po': 1,
                'np': 1,
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': 2,
                'invt': 2,
                'fid': 'f3',
                'fs': 'm:0+t:6,m:0+t:13,m:0+t:80',  # 深圳A股
                'fields': 'f12,f14',
            }
            try:
                response = requests.get(sz_url, params=params, headers=headers, timeout=30)
                data = response.json()
                
                if data['data'] and data['data']['diff']:
                    for item in data['data']['diff']:
                        code = str(item.get('f12', '')).zfill(6)
                        name = item.get('f14', '')
                        if code and name and code.isdigit() and len(code) == 6:
                            stock_names[code] = name
                else:
                    break
            except Exception as e:
                print(f"  第{page}页失败: {e}")
                break
        
        print(f"\n总计获取 {len(stock_names)} 只股票名称")
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
        # 获取股票名称
        stock_names = fetch_stock_names()
        
        if not stock_names:
            print("无法获取股票名称")
            return
        
        # 保存到文件
        with open('stock_names_network.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(stock_names.items()):
                f.write(f"{code}\t{name}\n")
        print("股票名称已保存到 stock_names_network.txt")
        
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