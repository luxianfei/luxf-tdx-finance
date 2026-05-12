#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门获取上海市场股票（60开头和68开头）
"""

from pytdx.hq import TdxHq_API


def fetch_shanghai_stocks():
    """获取上海市场股票"""
    api = TdxHq_API()
    
    stock_names = {}
    
    if api.connect('139.196.1.132', 7709):
        print("连接成功")
        
        # 尝试获取上海市场，从不同起始位置
        print("\n=== 获取上海市场股票 ===")
        
        # 尝试大范围搜索
        for start in range(0, 15000, 80):
            try:
                data = api.get_security_list(1, start)
                if not data or len(data) == 0:
                    break
                
                found = False
                for stock in data:
                    code = stock.get('code')
                    name = stock.get('name')
                    
                    if code and name and code.isdigit() and len(code) == 6:
                        # 只保留A股代码
                        if code.startswith(('60', '68')):
                            stock_names[code] = name
                            print(f"  {code}: {name}")
                            found = True
                
                if not found:
                    # 如果连续多个页面没有找到新股票，可能已经到头了
                    pass
                    
            except Exception as e:
                print(f"  获取数据失败: {e}")
                break
        
        api.disconnect()
        
    print(f"\n总计获取 {len(stock_names)} 只上海A股股票")
    return stock_names


if __name__ == '__main__':
    stocks = fetch_shanghai_stocks()
    
    # 保存到文件
    if stocks:
        with open('shanghai_stocks.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(stocks.items()):
                f.write(f"{code}\t{name}\n")
        print("上海股票名称已保存到 shanghai_stocks.txt")