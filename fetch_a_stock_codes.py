#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从通达信服务器获取真正的A股股票代码和名称
"""

from pytdx.hq import TdxHq_API


def fetch_real_stock_names():
    """获取真正的A股股票名称"""
    api = TdxHq_API()
    
    stock_names = {}
    
    if api.connect('139.196.1.132', 7709):
        print("连接成功")
        
        # 尝试从不同位置获取上海A股
        print("\n=== 获取上海A股 ===")
        # 上海A股通常在较高的位置开始
        for start in range(1000, 8000, 80):
            try:
                data = api.get_security_list(1, start)
                if not data or len(data) == 0:
                    break
                for stock in data:
                    code = stock.get('code')
                    name = stock.get('name')
                    if code and name and code.isdigit() and len(code) == 6:
                        if code.startswith('6'):
                            stock_names[code] = name
                            print(f"  {code}: {name}")
            except Exception as e:
                break
        
        # 尝试从不同位置获取深圳A股
        print("\n=== 获取深圳A股 ===")
        # 深圳A股也需要从较高位置开始
        for start in range(1000, 8000, 80):
            try:
                data = api.get_security_list(0, start)
                if not data or len(data) == 0:
                    break
                for stock in data:
                    code = stock.get('code')
                    name = stock.get('name')
                    if code and name and code.isdigit() and len(code) == 6:
                        if code.startswith(('0', '3')):
                            stock_names[code] = name
                            print(f"  {code}: {name}")
            except Exception as e:
                break
        
        api.disconnect()
        
    print(f"\n总计获取 {len(stock_names)} 只A股股票")
    return stock_names


if __name__ == '__main__':
    stocks = fetch_real_stock_names()
    
    # 保存到文件
    if stocks:
        with open('a_stock_names.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(stocks.items()):
                f.write(f"{code}\t{name}\n")
        print("股票名称已保存到 a_stock_names.txt")