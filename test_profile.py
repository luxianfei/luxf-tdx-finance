#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

# 检查profile.dat中是否有行业信息
f = open(r'D:\SoftwaresInstalled\dycy\T0002\hq_cache\profile.dat', 'rb')
data = f.read()
f.close()

# 搜索可能的行业关键词
industry_keywords = ['行业', '板块', '概念']
for kw in industry_keywords:
    kw_bytes = kw.encode('gbk')
    count = data.count(kw_bytes)
    print(f'关键词 "{kw}" 出现次数: {count}')

# 也搜索UTF-8编码
for kw in industry_keywords:
    kw_bytes = kw.encode('utf-8')
    count = data.count(kw_bytes)
    print(f'UTF-8 "{kw}" 出现次数: {count}')