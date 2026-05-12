#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pytdx.hq import TdxHq_API
import inspect

api = TdxHq_API()

print("连接到 120.25.129.112:7709...")
result = api.connect('120.25.129.112', 7709)
print(f"连接结果: {result}")

if result:
    # 查看get_company_info_content的源码
    print("\n=== get_company_info_content 源码 ===")
    print(inspect.getsource(api.get_company_info_content))

    api.disconnect()
else:
    print("连接失败")