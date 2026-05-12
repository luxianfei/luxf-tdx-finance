#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试服务器返回的数据
"""

from pytdx.hq import TdxHq_API


def debug_server_data():
    """调试服务器数据"""
    api = TdxHq_API()
    
    if api.connect('120.25.129.112', 7709):
        print("连接成功")
        
        # 获取上海市场数据
        print("\n=== 上海市场（市场代码1） ===")
        sh_6_stocks = []
        
        for start in [0, 80, 160, 240, 320, 400, 480, 560, 640, 720, 800, 880, 960]:
            data = api.get_security_list(1, start)
            if data:
                for stock in data[:5]:  # 只看前5条
                    code = stock.get('code')
                    name = stock.get('name')
                    if code:
                        print(f"  {code}: {name}")
                        if code.startswith('6'):
                            sh_6_stocks.append(code)
        
        print(f"\n上海市场6开头股票数量: {len(sh_6_stocks)}")
        
        # 获取深圳市场数据
        print("\n=== 深圳市场（市场代码0） ===")
        sz_stocks = []
        
        for start in [0, 80, 160, 240, 320]:
            data = api.get_security_list(0, start)
            if data:
                for stock in data[:5]:
                    code = stock.get('code')
                    name = stock.get('name')
                    if code:
                        print(f"  {code}: {name}")
                        sz_stocks.append(code)
        
        print(f"\n深圳市场股票数量: {len(sz_stocks)}")
        
        api.disconnect()


if __name__ == '__main__':
    debug_server_data()