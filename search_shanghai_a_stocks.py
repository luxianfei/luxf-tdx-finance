#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索上海市场的A股股票（60开头和68开头）
"""

from pytdx.hq import TdxHq_API


def search_shanghai_a_stocks():
    """搜索上海A股"""
    api = TdxHq_API()
    
    stock_names = {}
    
    if api.connect('139.196.1.132', 7709):
        print("连接成功")
        
        print("\n=== 搜索上海市场A股 ===")
        
        # 上海市场A股通常在较高位置，尝试大范围搜索
        # 从8000开始，因为前面是指数和债券
        for start in range(8000, 20000, 80):
            try:
                data = api.get_security_list(1, start)
                if not data or len(data) == 0:
                    continue
                
                found = False
                for stock in data:
                    code = stock.get('code')
                    name = stock.get('name')
                    
                    if code and name and code.isdigit() and len(code) == 6:
                        # 只保留上海A股代码（60开头和68开头）
                        if code.startswith(('60', '68')):
                            stock_names[code] = name
                            print(f"  {code}: {name}")
                            found = True
                
                if found:
                    print(f"  起始位置 {start} 找到A股股票")
                
            except Exception as e:
                print(f"  获取起始位置 {start} 失败: {e}")
                break
        
        api.disconnect()
        
    print(f"\n总计获取 {len(stock_names)} 只上海A股股票")
    return stock_names


if __name__ == '__main__':
    stocks = search_shanghai_a_stocks()
    
    # 统计代码前缀
    prefix_counts = {}
    for code in stocks.keys():
        prefix = code[:2]
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    
    print("\n股票代码前缀分布:")
    for prefix, count in sorted(prefix_counts.items()):
        print(f"  {prefix}开头: {count} 只")
    
    # 保存到文件
    if stocks:
        with open('shanghai_a_stocks.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(stocks.items()):
                f.write(f"{code}\t{name}\n")
        print("\n上海A股股票名称已保存到 shanghai_a_stocks.txt")