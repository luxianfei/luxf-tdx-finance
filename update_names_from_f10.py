#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用F10采集器从通达信远程服务器获取缺失股票的名称
"""

import sys
import time
import random
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG
from fetchers.f10_collector import F10Collector


def fetch_missing_names_from_f10():
    """从F10数据获取缺失股票的名称"""
    missing_codes = [
        '000044', '000122', '000300', '000687', '000689', '000699', '000847',
        '000986', '000991', '000992', '600200', '600355', '603056',
        '002231', '300344', '300379', '300391'
    ]
    
    collector = F10Collector()
    print("使用F10采集器从通达信远程服务器查询...")
    print()
    
    found = {}
    for i, code in enumerate(missing_codes, 1):
        print(f"[{i}/{len(missing_codes)}] 查询 {code}...", end=" ", flush=True)
        
        try:
            profile = collector.get_company_profile(code)
            company_name = profile.get('company_name', '')
            
            if company_name and company_name != '--':
                # 尝试从公司全称中提取简称
                short_name = extract_short_name(company_name, code)
                found[code] = short_name
                print(f"✓ 找到: {short_name}")
            else:
                print(f"✗ 未找到")
        except Exception as e:
            print(f"✗ 查询失败: {e}")
        
        time.sleep(random.uniform(0.3, 0.8))
    
    print()
    print(f"共找到 {len(found)} 只股票的名称")
    
    if found:
        with open('missing_stock_names_f10.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(found.items()):
                f.write(f"{code}\t{name}\n")
        print("已保存到 missing_stock_names_f10.txt")
    
    return found


def extract_short_name(company_name, code):
    """从公司全称中提取简称"""
    # 移除括号中的内容
    import re
    name_clean = re.sub(r'（.*?）|\(.*?\)', '', company_name)
    
    # 常见后缀
    suffixes = ['股份有限公司', '有限责任公司', '有限公司', '股份公司', '集团']
    
    for suffix in suffixes:
        if name_clean.endswith(suffix):
            name_clean = name_clean[:-len(suffix)]
            break
    
    # 如果剩下的名字太长，取前4-6个字
    if len(name_clean) > 6:
        name_clean = name_clean[:4]
    
    return name_clean.strip()


def update_remaining_names(names):
    """更新剩余股票名称"""
    if not names:
        print("没有可用的股票名称数据")
        return
    
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        conn = db.connect()
        update_sql = "UPDATE stock_list SET name = %s WHERE code = %s"
        
        count = 0
        with conn.cursor() as cursor:
            for code, name in names.items():
                cursor.execute(update_sql, (name, code))
                count += 1
                print(f"  更新 {code}: {name}")
            conn.commit()
        
        print(f"\n成功更新 {count} 只股票的名称")
        
        sql_updated = "SELECT COUNT(*) as cnt FROM stock_list WHERE name NOT LIKE '股票%'"
        sql_not_updated = "SELECT COUNT(*) as cnt FROM stock_list WHERE name LIKE '股票%'"
        
        updated = db.query_one(sql_updated)['cnt']
        not_updated = db.query_one(sql_not_updated)['cnt']
        
        print(f"\n最终统计结果:")
        print(f"  已更新名称: {updated} 只")
        print(f"  未更新名称: {not_updated} 只")
        
    finally:
        db.close()


if __name__ == '__main__':
    names = fetch_missing_names_from_f10()
    if names:
        update_remaining_names(names)