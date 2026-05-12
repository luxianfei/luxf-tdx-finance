#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找服务器返回真实股票代码的位置
"""

from pytdx.hq import TdxHq_API

servers = [
    ('120.25.129.112', 7709),
]

for host, port in servers:
    print(f"\n尝试连接 {host}:{port}...")
    api = TdxHq_API()
    try:
        if api.connect(host, port):
            print("连接成功！")
            
            # 尝试从更大的位置索引获取真实股票代码
            print("\n尝试从不同位置获取真实股票代码...")
            
            # 上海市场 - 尝试不同的起始位置
            print("\n上海市场:")
            for start in [2000, 3000, 4000, 5000, 6000, 7000]:
                data = api.get_security_list(1, start)
                if data and len(data) > 0:
                    found_real = False
                    for stock in data[:3]:
                        code = stock.get('code')
                        name = stock.get('name')
                        if code and code.isdigit() and len(code) == 6:
                            if code.startswith('6'):
                                print(f"  位置 {start}: {code}: {name}")
                                found_real = True
                    if not found_real:
                        print(f"  位置 {start}: 无真实股票")
            
            # 深圳市场 - 尝试不同的起始位置
            print("\n深圳市场:")
            for start in [2000, 3000, 4000, 5000, 6000, 7000]:
                data = api.get_security_list(0, start)
                if data and len(data) > 0:
                    found_real = False
                    for stock in data[:3]:
                        code = stock.get('code')
                        name = stock.get('name')
                        if code and code.isdigit() and len(code) == 6:
                            if code.startswith(('0', '3')):
                                print(f"  位置 {start}: {code}: {name}")
                                found_real = True
                    if not found_real:
                        print(f"  位置 {start}: 无真实股票")
            
            api.disconnect()
            break
        else:
            print("连接失败")
    except Exception as e:
        print(f"连接异常: {e}")
        import traceback
        traceback.print_exc()