#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pytdx.hq import TdxHq_API

api = TdxHq_API()

# 尝试连接
print("尝试连接通达信...")
result = api.connect('127.0.0.1', 7709)
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

    # 测试获取公司信息内容
    print("\n=== 测试 get_company_info_content ===")
    try:
        # 上海股票 688456
        data = api.get_company_info_content(1, '688456', 0, 10000)
        print(f"688456 公司信息内容长度: {len(data) if data else 0}")
        if data:
            print(f"前500字符: {str(data)[:500]}")
    except Exception as e:
        print(f"获取公司信息内容失败: {e}")

    api.disconnect()
else:
    print("无法连接到本地通达信服务器")