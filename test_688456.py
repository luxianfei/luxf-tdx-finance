#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

# 详细分析profile.dat文件
f = open(r'D:\SoftwaresInstalled\dycy\T0002\hq_cache\profile.dat', 'rb')
data = f.read()
f.close()

# 查找所有股票代码模式（7位数字，以0x00结尾）
pattern = rb'\x00(\d{6})\x00'
matches = list(re.finditer(pattern, data))

print(f'profile.dat 总记录数: {len(matches)}')

# 获取唯一股票代码
unique_codes = set()
for m in matches:
    code = m.group(1).decode('ascii')
    unique_codes.add(code)

print(f'唯一股票代码数: {len(unique_codes)}')

# 查找688456这条记录
target_code = b'688456'
pos = data.find(target_code)
if pos > 0:
    print(f'\n找到688456在位置: {pos}')
    print(f'周围50字节hex: {data[pos-25:pos+75].hex()}')

    # 尝试提取更多上下文
    start = max(0, pos - 50)
    end = min(len(data), pos + 150)
    context = data[start:end]

    # 查找以\x00结尾的字符串
    for i in range(len(context)):
        if context[i] == 0:
            try:
                s = context[i+1:].split(b'\x00')[0]
                print(f'后续字符串: {s.decode("gbk", errors="ignore")}')
            except:
                pass