#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查文件中股票代码的前缀分布
"""

def check_prefix():
    """检查代码前缀"""
    prefix_counts = {}
    codes = []
    
    with open('all_a_stock_names.txt', 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.split('\t')
            if parts:
                code = parts[0].strip()
                codes.append(code)
                prefix = code[:2]
                prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    
    print("文件中股票代码前缀分布:")
    for prefix, count in sorted(prefix_counts.items()):
        print(f"  {prefix}开头: {count} 只")
    
    print("\n文件中代码示例:")
    for code in codes[:20]:
        print(f"  {code}")


if __name__ == '__main__':
    check_prefix()