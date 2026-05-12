#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re

base_path = r'D:\SoftwaresInstalled\dycy'

# 常见的行业关键词
keywords = ['电子', '软件', '医药', '化工', '机械', '银行', '保险', '证券']

def search_in_file(fpath, keyword):
    """在文件中搜索关键词"""
    try:
        with open(fpath, 'rb') as f:
            data = f.read()
        for enc in ['gbk', 'gb2312', 'utf-8']:
            try:
                text = data.decode(enc, errors='ignore')
                if keyword in text:
                    return True, enc
            except:
                pass
    except:
        pass
    return False, None

# 搜索目录
for root, dirs, files in os.walk(base_path):
    for fname in files:
        if fname.endswith(('.dat', '.dax', '.cfg')):
            fpath = os.path.join(root, fname)
            for kw in keywords:
                found, enc = search_in_file(fpath, kw)
                if found:
                    print(f'找到 "{kw}" 在文件: {fpath}')
                    break