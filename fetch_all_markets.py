#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尝试从通达信服务器获取所有市场的股票名称
"""

from pytdx.hq import TdxHq_API


def fetch_all_markets():
    """获取所有市场的股票"""
    api = TdxHq_API()
    
    stock_names = {}
    
    if api.connect('139.196.1.132', 7709):
        print("连接成功")
        
        # 尝试不同的市场代码
        markets = [
            (0, "深圳市场"),
            (1, "上海市场"),
            (2, "B股市场"),
            (3, "基金市场"),
            (4, "债券市场"),
        ]
        
        for market_code, market_name in markets:
            print(f"\n=== 获取 {market_name} (代码: {market_code}) ===")
            
            # 尝试大范围搜索
            found_count = 0
            for start in range(0, 20000, 80):
                try:
                    data = api.get_security_list(market_code, start)
                    if not data or len(data) == 0:
                        # 如果连续20个页面没有数据，可能已经到头了
                        if start > 0 and found_count > 0:
                            break
                        continue
                    
                    for stock in data:
                        code = stock.get('code')
                        name = stock.get('name')
                        
                        if code and name and code.isdigit() and len(code) == 6:
                            # 只保留A股代码（0、3、6开头）
                            if code.startswith(('0', '3', '6')):
                                if code not in stock_names:
                                    stock_names[code] = name
                                    print(f"  {code}: {name}")
                                    found_count += 1
                                    # 每200只打印一次进度
                                    if found_count % 200 == 0:
                                        print(f"  已找到 {found_count} 只...")
                                    
                except Exception as e:
                    print(f"  获取数据失败: {e}")
                    break
        
        api.disconnect()
        
    print(f"\n总计获取 {len(stock_names)} 只A股股票")
    return stock_names


if __name__ == '__main__':
    stocks = fetch_all_markets()
    
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
        with open('all_markets_stocks.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(stocks.items()):
                f.write(f"{code}\t{name}\n")
        print("\n股票名称已保存到 all_markets_stocks.txt")