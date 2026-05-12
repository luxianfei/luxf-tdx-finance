#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析数据库中未更新的股票代码类型
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def analyze_codes():
    """分析股票代码"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取所有未更新的股票代码
        sql = "SELECT code FROM stock_list WHERE name LIKE '股票%'"
        results = db.query_all(sql)
        
        codes = [r['code'] for r in results]
        
        # 分析代码前缀
        prefix_counts = {}
        for code in codes:
            prefix = code[:2]
            prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
        
        print("未更新股票代码前缀分布:")
        for prefix, count in sorted(prefix_counts.items()):
            print(f"  {prefix}开头: {count} 只")
        
        # 列出一些未更新的股票代码示例
        print("\n未更新股票代码示例:")
        for code in codes[:20]:
            print(f"  {code}")
        
        # 获取文件中的股票代码集合
        file_codes = set()
        try:
            with open('all_a_stock_names.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.split('\t')
                    if parts:
                        file_codes.add(parts[0].strip())
        except Exception as e:
            print(f"读取文件失败: {e}")
        
        print(f"\n文件中股票代码数量: {len(file_codes)}")
        
        # 检查是否有重叠
        overlap = [c for c in codes if c in file_codes]
        print(f"数据库未更新代码与文件代码重叠数量: {len(overlap)}")
        if overlap:
            print("重叠代码示例:")
            for code in overlap[:10]:
                print(f"  {code}")
        
    finally:
        db.close()


if __name__ == '__main__':
    analyze_codes()