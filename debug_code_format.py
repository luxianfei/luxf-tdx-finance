#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试股票代码格式问题
"""

from pytdx.hq import TdxHq_API


def debug_code_format():
    """调试代码格式"""
    api = TdxHq_API()
    
    if api.connect('139.196.1.132', 7709):
        print("连接成功")
        
        # 获取上海市场数据
        print("\n=== 上海市场（市场代码1）===")
        data = api.get_security_list(1, 0)
        if data:
            for stock in data[:20]:
                code = stock.get('code')
                name = stock.get('name')
                print(f"  {repr(code)}: {repr(name)}")
        
        # 获取深圳市场数据
        print("\n=== 深圳市场（市场代码0）===")
        data = api.get_security_list(0, 0)
        if data:
            for stock in data[:20]:
                code = stock.get('code')
                name = stock.get('name')
                print(f"  {repr(code)}: {repr(name)}")
        
        api.disconnect()


if __name__ == '__main__':
    debug_code_format()