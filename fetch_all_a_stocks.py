#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从通达信服务器获取所有A股股票代码和名称
"""

from pytdx.hq import TdxHq_API


def fetch_all_a_stocks():
    """获取所有A股股票"""
    api = TdxHq_API()
    
    stock_names = {}
    
    if api.connect('139.196.1.132', 7709):
        print("连接成功")
        
        # 获取上海A股（6开头）
        print("\n=== 获取上海A股（6开头）===")
        for start in range(0, 8000, 80):
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
        
        # 获取深圳A股（0开头和3开头）
        print("\n=== 获取深圳A股（0开头和3开头）===")
        for start in range(0, 8000, 80):
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
    stocks = fetch_all_a_stocks()
    
    # 保存到文件
    if stocks:
        with open('all_a_stock_names.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(stocks.items()):
                f.write(f"{code}\t{name}\n")
        print("股票名称已保存到 all_a_stock_names.txt")