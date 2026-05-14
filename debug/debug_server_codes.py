#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试服务器返回的股票代码格式
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
            
            # 获取上海市场股票列表（从不同位置开始）
            print("\n获取上海市场股票（位置0-100）:")
            for start in [0, 100, 200]:
                data = api.get_security_list(1, start)
                if data and len(data) > 0:
                    print(f"\n位置 {start} 开始的股票:")
                    for stock in data[:5]:
                        code = stock.get('code')
                        name = stock.get('name')
                        print(f"  {code}: {name}")
                else:
                    print(f"  位置 {start} 无数据")
            
            # 获取深圳市场股票列表
            print("\n获取深圳市场股票（位置0-100）:")
            for start in [0, 100, 200]:
                data = api.get_security_list(0, start)
                if data and len(data) > 0:
                    print(f"\n位置 {start} 开始的股票:")
                    for stock in data[:5]:
                        code = stock.get('code')
                        name = stock.get('name')
                        print(f"  {code}: {name}")
                else:
                    print(f"  位置 {start} 无数据")
            
            api.disconnect()
            break
        else:
            print("连接失败")
    except Exception as e:
        print(f"连接异常: {e}")
        import traceback
        traceback.print_exc()