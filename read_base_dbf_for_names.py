#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 base.dbf 读取股票名称
"""

from dbfread import DBF
import os

def read_stock_names_from_base_dbf():
    """从 base.dbf 读取股票代码和名称"""
    base_dbf = "D:/SoftwaresInstalled/dycy/T0002/hq_cache/base.dbf"
    
    if not os.path.exists(base_dbf):
        print(f"文件不存在: {base_dbf}")
        return
    
    print("正在读取 base.dbf 文件...")
    table = DBF(base_dbf, encoding='gbk')
    
    stock_names = {}
    count = 0
    
    for record in table:
        # 获取股票代码和名称
        code = record.get('GPDM', '') or record.get('CODE', '') or record.get('DM', '')
        name = record.get('GPJC', '') or record.get('NAME', '') or record.get('MC', '')
        
        if code and name:
            code = str(code).zfill(6)
            # 只保留A股代码
            if code.startswith(('60', '68', '00', '30')):
                stock_names[code] = name
                count += 1
                if count <= 10:
                    print(f"  {code}: {name}")
    
    print(f"\n共找到 {count} 只A股股票")
    return stock_names

if __name__ == '__main__':
    read_stock_names_from_base_dbf()