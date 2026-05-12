#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 base.dbf 的字段结构
"""

from dbfread import DBF
import os

def check_base_dbf_fields():
    """检查 base.dbf 的字段"""
    base_dbf = "D:/SoftwaresInstalled/dycy/T0002/hq_cache/base.dbf"
    
    if not os.path.exists(base_dbf):
        print(f"文件不存在: {base_dbf}")
        return
    
    print("正在读取 base.dbf 文件...")
    table = DBF(base_dbf, encoding='gbk')
    
    # 打印字段名
    print("\n字段列表:")
    for field in table.fields:
        print(f"  {field.name}: {field.type}({field.length})")
    
    # 打印前5条记录
    print("\n前5条记录:")
    count = 0
    for record in table:
        print(f"\n记录 {count + 1}:")
        for key, value in record.items():
            print(f"  {key}: {value}")
        count += 1
        if count >= 5:
            break

if __name__ == '__main__':
    check_base_dbf_fields()