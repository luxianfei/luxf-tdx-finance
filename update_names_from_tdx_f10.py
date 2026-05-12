#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从通达信本地F10数据中查找缺失股票的名称
"""

import sys
import os
from pathlib import Path
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

TDX_DIR = 'D:/SoftwaresInstalled/dycy'


def find_f10_data(code):
    """查找F10数据文件"""
    # 尝试上海市场
    sh_path = Path(TDX_DIR) / 'vipdoc' / 'sh' / 'f10' / f'sh{code}'
    if sh_path.exists():
        return sh_path, 'sh'
    
    # 尝试深圳市场
    sz_path = Path(TDX_DIR) / 'vipdoc' / 'sz' / 'f10' / f'sz{code}'
    if sz_path.exists():
        return sz_path, 'sz'
    
    return None, None


def extract_name_from_f10(path, market):
    """从F10数据中提取股票名称"""
    try:
        # 检查是否有txt文件
        txt_files = list(path.glob('*.txt'))
        if txt_files:
            with open(txt_files[0], 'r', encoding='gbk', errors='ignore') as f:
                content = f.read(2000)
                # 查找股票名称相关信息
                import re
                name_matches = re.findall(r'(?:股票简称|公司全称|公司名称)[:：]?\s*([^\s\n]+)', content)
                if name_matches:
                    return name_matches[0]
        
        # 检查是否有dat文件
        dat_files = list(path.glob('*.dat'))
        if dat_files:
            with open(dat_files[0], 'rb') as f:
                content = f.read(2000)
                try:
                    text = content.decode('gbk', errors='ignore')
                    import re
                    name_matches = re.findall(r'(?:股票简称|公司全称|公司名称)[:：]?\s*([^\s\n]+)', text)
                    if name_matches:
                        return name_matches[0]
                except:
                    pass
        
        return None
        
    except Exception as e:
        return None


def fetch_names_from_tdx():
    """从通达信本地F10获取名称"""
    missing_codes = [
        '000044', '000122', '000300', '000687', '000689', '000699', '000847',
        '000986', '000991', '000992', '600200', '600355', '603056',
        '002231', '300344', '300379', '300391'
    ]
    
    print("从通达信本地F10数据中查找...")
    print()
    
    found = {}
    for code in missing_codes:
        print(f"查询 {code}...", end=" ")
        
        path, market = find_f10_data(code)
        if path:
            name = extract_name_from_f10(path, market)
            if name:
                found[code] = name
                print(f"✓ 找到: {name}")
            else:
                print(f"✗ 找到目录但无法提取名称")
        else:
            print(f"✗ 无F10数据")
    
    print()
    print(f"共找到 {len(found)} 只股票的名称")
    
    if found:
        with open('missing_stock_names_tdx.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(found.items()):
                f.write(f"{code}\t{name}\n")
        print("已保存到 missing_stock_names_tdx.txt")
    
    return found


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
    names = fetch_names_from_tdx()
    if names:
        update_remaining_names(names)