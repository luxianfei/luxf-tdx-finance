#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试获取股票简称"""

import sys
sys.path.insert(0, '.')
from pytdx.hq import TdxHq_API

servers = [
    ('120.25.129.112', 7709),
    ('119.147.212.81', 7709),
    ('124.74.236.94', 7709),
]

for host, port in servers:
    print(f"尝试连接 {host}:{port}...")
    api = TdxHq_API()
    try:
        if api.connect(host, port):
            # 获取上海市场股票列表（从位置0开始）
            data = api.get_security_list(1, 0)
            if data and len(data) > 0:
                print('成功！股票列表数据字段:', list(data[0].keys()))
                print()
                for i, stock in enumerate(data[:3]):
                    name = stock.get('name', 'N/A')
                    print(f'{i+1}. 代码:{stock["code"]}, 名称:{name}')
            else:
                print('获取数据为空')
            api.disconnect()
            break
        else:
            print('连接失败')
    except Exception as e:
        print(f'连接异常: {e}')
