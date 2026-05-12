#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pytdx.hq import TdxHq_API

api = TdxHq_API()

print("连接到 120.25.129.112:7709...")
result = api.connect('120.25.129.112', 7709)
print(f"连接结果: {result}")

if result:
    # 获取公司信息类别
    print("\n=== 获取 688456 公司信息类别 ===")
    try:
        category = api.get_company_info_category(1, '688456')
        print(f"类别数据: {category}")
    except Exception as e:
        print(f"获取类别失败: {e}")
        import traceback
        traceback.print_exc()

    # 尝试获取整个文件内容
    print("\n=== 获取 688456 整个公司信息文件 ===")
    try:
        # 尝试获取前100字节
        data = api.get_company_info_content(1, '688456', 0, 100)
        print(f"start=0, length=100: {data}")

        # 尝试获取不同的start值
        data2 = api.get_company_info_content(1, '688456', 43129, 200)
        print(f"start=43129, length=200: {data2}")
    except Exception as e:
        print(f"获取公司信息失败: {e}")
        import traceback
        traceback.print_exc()

    api.disconnect()
else:
    print("连接失败")