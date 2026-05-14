#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pytdx.hq import TdxHq_API

api = TdxHq_API()

# 尝试连接远程服务器
print("尝试连接 120.25.129.112:7709...")
result = api.connect('120.25.129.112', 7709)
print(f"连接结果: {result}")

if result:
    # 测试获取公司信息类别
    print("\n=== 测试 get_company_info_category ===")
    try:
        # 上海股票 688456
        data = api.get_company_info_category(1, '688456')
        print(f"688456 公司信息类别: {data}")
    except Exception as e:
        print(f"获取公司信息类别失败: {e}")

    api.disconnect()
else:
    print("连接失败，尝试其他地址...")

# 尝试127.0.0.1
api2 = TdxHq_API()
print("\n尝试连接 127.0.0.1:7709...")
result2 = api2.connect('127.0.0.1', 7709)
print(f"连接结果: {result2}")

if result2:
    try:
        data = api2.get_company_info_category(1, '688456')
        print(f"688456 公司信息类别: {data}")
        api2.disconnect()
    except Exception as e:
        print(f"获取公司信息类别失败: {e}")
        api2.disconnect()