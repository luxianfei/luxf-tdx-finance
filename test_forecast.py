#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pytdx.hq import TdxHq_API

api = TdxHq_API()
api.connect('120.25.129.112', 7709)

category = api.get_company_info_category(1, '688456')
print('所有类别:')
for item in category:
    print(f"  {item['name']}: start={item['start']}, length={item['length']}")

# 获取研报评级
forecast_info = None
filename = None
for item in category:
    if item['name'] == '研报评级':
        forecast_info = item
        filename = item['filename']
        break

if forecast_info:
    content = api.get_company_info_content(1, '688456', filename, forecast_info['start'], forecast_info['length'])
    print(f'\n研报评级内容前2000字符:')
    print(content[:2000])

api.disconnect()