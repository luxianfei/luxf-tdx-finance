#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尝试使用不同参数获取股票名称
"""

from pytdx.hq import TdxHq_API


def fetch_with_params():
    """使用不同参数获取股票"""
    api = TdxHq_API()
    
    stock_names = {}
    
    if api.connect('139.196.1.132', 7709):
        print("连接成功")
        
        # 尝试获取市场代码列表
        print("\n=== 获取市场代码列表 ===")
        try:
            market_codes = api.get_market_list()
            print(f"市场列表: {market_codes}")
        except Exception as e:
            print(f"获取市场列表失败: {e}")
        
        # 尝试获取股票数量
        print("\n=== 获取股票数量 ===")
        for market in [0, 1]:
            try:
                count = api.get_security_count(market)
                print(f"市场 {market} 股票数量: {count}")
            except Exception as e:
                print(f"获取市场 {market} 股票数量失败: {e}")
        
        # 尝试从0开始获取深圳市场
        print("\n=== 深圳市场详细信息 ===")
        for start in [0, 500, 1000, 1500, 2000, 2500, 3000]:
            try:
                data = api.get_security_list(0, start)
                if data:
                    print(f"\n起始位置 {start}:")
                    for stock in data[:5]:
                        code = stock.get('code')
                        name = stock.get('name')
                        print(f"  {code}: {name}")
            except Exception as e:
                print(f"获取起始位置 {start} 失败: {e}")
        
        # 尝试从0开始获取上海市场
        print("\n=== 上海市场详细信息 ===")
        for start in [0, 500, 1000, 1500, 2000, 2500, 3000]:
            try:
                data = api.get_security_list(1, start)
                if data:
                    print(f"\n起始位置 {start}:")
                    for stock in data[:5]:
                        code = stock.get('code')
                        name = stock.get('name')
                        print(f"  {code}: {name}")
            except Exception as e:
                print(f"获取起始位置 {start} 失败: {e}")
        
        api.disconnect()
    
    return stock_names


if __name__ == '__main__':
    fetch_with_params()