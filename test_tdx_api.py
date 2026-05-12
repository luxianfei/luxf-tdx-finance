#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pytdx.hq import TdxHq_API
import time

api = TdxHq_API()

# 尝试连接
print("尝试连接通达信...")
if api.connect('127.0.0.1', 7709):
    print("连接成功!")
else:
    print("连接失败")

# 检查API支持的方法
print("\n=== TdxHq_API 支持的方法 ===")
methods = [m for m in dir(api) if not m.startswith('_')]
for m in methods:
    print(m)

api.disconnect()