#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pytdx.hq import TdxHq_API

api = TdxHq_API()
api.connect('120.25.129.112', 7709)

# 获取公司信息类别
category = api.get_company_info_category(1, '688456')
print("公司信息类别:")
for item in category:
    print(f"  {item['name']}: start={item['start']}, length={item['length']}")

# 获取公司概况内容
profile = api.get_company_info_content(1, '688456', '688456.txt', 43129, 12290)
print(f"\n公司概况内容长度: {len(profile)}")
print("前1000字符:")
print(profile[:1000])

api.disconnect()