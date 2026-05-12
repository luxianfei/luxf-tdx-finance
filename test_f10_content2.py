#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pytdx.hq import TdxHq_API

api = TdxHq_API()

print("连接到 120.25.129.112:7709...")
result = api.connect('120.25.129.112', 7709)
print(f"连接结果: {result}")

if result:
    # 获取公司概况内容
    print("\n=== 获取 688456 公司概况 ===")
    try:
        # 上海股票 688456，文件名688456.txt，起始位置43129，长度12290
        data = api.get_company_info_content(1, '688456', '688456.txt', 43129, 12290)
        print(f"数据长度: {len(data) if data else 0}")
        if data:
            print(f"公司概况内容:\n{data}")
    except Exception as e:
        print(f"获取公司概况失败: {e}")
        import traceback
        traceback.print_exc()

    # 也尝试获取最新提示（第一个类别）
    print("\n=== 获取 688456 最新提示 ===")
    try:
        data = api.get_company_info_content(1, '688456', '688456.txt', 0, 43129)
        print(f"数据长度: {len(data) if data else 0}")
        if data:
            print(f"最新提示内容:\n{data[:1000]}")
    except Exception as e:
        print(f"获取最新提示失败: {e}")
        import traceback
        traceback.print_exc()

    api.disconnect()
else:
    print("连接失败")