#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

fpath = r'D:\SoftwaresInstalled\dycy\T0002\lc_data\第一创业2168000071.dat'
with open(fpath, 'rb') as f:
    data = f.read()

print(f'文件大小: {len(data)} bytes')
print(f'前200字节(hex): {data[:200].hex()}')

# 尝试解码
for enc in ['gbk', 'gb2312', 'utf-8']:
    try:
        text = data.decode(enc, errors='ignore')
        if len(text) > 50:
            print(f'\n{enc}解码前200字符:')
            print(text[:200])
            break
    except Exception as e:
        print(f'{enc}解码失败: {e}')