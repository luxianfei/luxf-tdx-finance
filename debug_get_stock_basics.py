#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""尝试使用 get_stock_basics 获取股票信息"""

import sys
sys.path.insert(0, '.')
from pytdx.hq import TdxHq_API

servers = [
    ('120.25.129.112', 7709),
    ('119.147.212.81', 7709),
]

for host, port in servers:
    print(f"\n尝试连接 {host}:{port}...")
    api = TdxHq_API()
    try:
        if api.connect(host, port):
            print("连接成功！")
            
            # 尝试获取股票基本信息
            print("\n尝试获取股票基本信息:")
            try:
                data = api.get_stock_basics()
                if data and len(data) > 0:
                    print(f"成功获取 {len(data)} 条记录")
                    for i, (code, info) in enumerate(data.items()):
                        if i >= 10:
                            break
                        print(f"  {code}: {info.get('name', 'N/A')}")
                else:
                    print("  数据为空")
            except AttributeError as e:
                print(f"  get_stock_basics 方法不存在: {e}")
            
            api.disconnect()
            break
        else:
            print("连接失败")
    except Exception as e:
        print(f"连接异常: {e}")