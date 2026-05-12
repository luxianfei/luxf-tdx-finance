#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从本地通达信目录获取股票代码
"""

import os

TDX_DIR = "D:/SoftwaresInstalled/dycy"


def get_stock_codes_from_local():
    """从本地通达信目录获取股票代码"""
    stock_codes = {}
    
    # 上海市场
    sh_dir = os.path.join(TDX_DIR, "vipdoc", "sh", "lday")
    if os.path.exists(sh_dir):
        print(f"扫描上海市场目录: {sh_dir}")
        for f in os.listdir(sh_dir):
            if f.endswith('.day'):
                code = f[2:8]
                if code.isdigit() and len(code) == 6:
                    stock_codes[code] = 'sh'
    
    # 深圳市场
    sz_dir = os.path.join(TDX_DIR, "vipdoc", "sz", "lday")
    if os.path.exists(sz_dir):
        print(f"扫描深圳市场目录: {sz_dir}")
        for f in os.listdir(sz_dir):
            if f.endswith('.day'):
                code = f[2:8]
                if code.isdigit() and len(code) == 6:
                    stock_codes[code] = 'sz'
    
    print(f"从本地目录获取了 {len(stock_codes)} 只股票代码")
    
    # 统计代码前缀
    prefix_counts = {}
    for code in stock_codes.keys():
        prefix = code[:2]
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    
    print("\n本地股票代码前缀分布:")
    for prefix, count in sorted(prefix_counts.items()):
        print(f"  {prefix}开头: {count} 只")
    
    return stock_codes


if __name__ == '__main__':
    codes = get_stock_codes_from_local()
    
    # 保存到文件
    with open('local_stock_codes.txt', 'w', encoding='utf-8') as f:
        for code in sorted(codes.keys()):
            f.write(f"{code}\n")
    print("\n股票代码已保存到 local_stock_codes.txt")