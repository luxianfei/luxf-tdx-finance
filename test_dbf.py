#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试读取 base.dbf 文件
"""

import os
from config import TDX_DIR
from dbfread import DBF

base_dbf = os.path.join(TDX_DIR, "T0002", "hq_cache", "base.dbf")
print(f"文件路径: {base_dbf}")
print(f"文件存在: {os.path.exists(base_dbf)}")

if os.path.exists(base_dbf):
    table = DBF(base_dbf, encoding='gbk')
    print(f"\n字段列表: {table.fields}")
    
    # 打印前10条记录
    print("\n前10条记录:")
    for i, record in enumerate(table):
        if i >= 10:
            break
        print(f"{i+1}: {record}")