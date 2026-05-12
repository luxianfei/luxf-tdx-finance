#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

# 检查几个关键文件
files_to_check = [
    r'D:\SoftwaresInstalled\dycy\T0002\hq_cache\ds_stk.dat',
    r'D:\SoftwaresInstalled\dycy\T0002\hq_cache\pttab.dat',
    r'D:\SoftwaresInstalled\dycy\T0002\hq_cache\relation.dat',
    r'D:\SoftwaresInstalled\dycy\T0002\hq_cache\sbblock.dat',
]

for fpath in files_to_check:
    if not os.path.exists(fpath):
        print(f'{fpath}: 文件不存在')
        continue

    fsize = os.path.getsize(fpath)
    print(f'\n=== {os.path.basename(fpath)} (大小: {fsize} bytes) ===')

    with open(fpath, 'rb') as f:
        data = f.read()

    # 尝试解码并显示前500字符
    for enc in ['gbk', 'gb2312', 'utf-8']:
        try:
            text = data.decode(enc, errors='ignore')
            print(f'{enc}解码前500字符:')
            print(text[:500])
            print('...')
            break
        except Exception as e:
            print(f'{enc}解码失败: {e}')