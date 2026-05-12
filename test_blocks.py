#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re

base_path = r'D:\SoftwaresInstalled\dycy\T0002\hq_cache'

files_to_check = [
    'brkcomp.dat',
    'csiblock.dat',
    'ds_tinf.dat',
    'hkcwdata.dat',
    'sbcwdata.dat',
]

for fname in files_to_check:
    fpath = os.path.join(base_path, fname)
    if not os.path.exists(fpath):
        print(f'{fname}: 文件不存在')
        continue

    fsize = os.path.getsize(fpath)
    print(f'\n=== {fname} (大小: {fsize} bytes) ===')

    with open(fpath, 'rb') as f:
        data = f.read(500)  # 只读前500字节

    # 尝试解码
    for encoding in ['gbk', 'gb2312', 'utf-8']:
        try:
            text = data.decode(encoding, errors='ignore')
            print(f'  {encoding}解码前200字符: {text[:200]}')
            break
        except:
            pass

    # 搜索行业关键词
    for kw in ['行业', '板块', '概念', '主营', '电子', '软件', '医药']:
        kw_bytes = kw.encode('gbk')
        if kw_bytes in data:
            print(f'  找到关键词: {kw}')