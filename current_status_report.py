#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
当前股票名称更新状态报告
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def generate_status_report():
    """生成状态报告"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 总股票数量
        sql_total = "SELECT COUNT(*) as cnt FROM stock_list"
        total = db.query_one(sql_total)['cnt']
        
        # 已更新名称的股票数量
        sql_updated = "SELECT COUNT(*) as cnt FROM stock_list WHERE name NOT LIKE '股票%'"
        updated = db.query_one(sql_updated)['cnt']
        
        # 未更新名称的股票数量
        sql_not_updated = "SELECT COUNT(*) as cnt FROM stock_list WHERE name LIKE '股票%'"
        not_updated = db.query_one(sql_not_updated)['cnt']
        
        # 已更新的A股数量
        sql_a_stock_updated = """
        SELECT COUNT(*) as cnt FROM stock_list 
        WHERE name NOT LIKE '股票%' AND 
              (code LIKE '6%' OR code LIKE '0%' OR code LIKE '3%' OR code LIKE '8%')
        """
        a_stock_updated = db.query_one(sql_a_stock_updated)['cnt']
        
        # 未更新的A股数量
        sql_a_stock_not_updated = """
        SELECT COUNT(*) as cnt FROM stock_list 
        WHERE name LIKE '股票%' AND 
              (code LIKE '6%' OR code LIKE '0%' OR code LIKE '3%' OR code LIKE '8%')
        """
        a_stock_not_updated = db.query_one(sql_a_stock_not_updated)['cnt']
        
        print("=" * 60)
        print("股票名称更新状态报告")
        print("=" * 60)
        print(f"总股票数量: {total:,}")
        print(f"已更新名称: {updated:,} ({updated/total*100:.1f}%)")
        print(f"未更新名称: {not_updated:,} ({not_updated/total*100:.1f}%)")
        print("-" * 60)
        print(f"A股已更新: {a_stock_updated:,}")
        print(f"A股未更新: {a_stock_not_updated:,}")
        print("=" * 60)
        
        # 显示部分已更新和未更新的股票
        print("\n已更新的股票示例:")
        sql_sample_updated = """
        SELECT code, name FROM stock_list 
        WHERE name NOT LIKE '股票%' 
        ORDER BY code 
        LIMIT 5
        """
        for r in db.query_all(sql_sample_updated):
            print(f"  {r['code']}: {r['name']}")
        
        print("\n未更新的A股示例:")
        sql_sample_not_updated = """
        SELECT code, name FROM stock_list 
        WHERE name LIKE '股票%' AND 
              (code LIKE '6%' OR code LIKE '0%' OR code LIKE '3%' OR code LIKE '8%')
        ORDER BY code 
        LIMIT 5
        """
        for r in db.query_all(sql_sample_not_updated):
            print(f"  {r['code']}: {r['name']}")
        
        print("\n" + "=" * 60)
        print("问题说明:")
        print("=" * 60)
        print("1. 通达信服务器返回的数据不完整")
        print("   - 只返回了深圳市场的部分数据")
        print("   - 上海A股、科创板、创业板数据缺失")
        print("2. 本地通达信目录没有直接包含股票名称的文件")
        print("   - base.dbf 文件存在但解析困难")
        print("   - 日线文件(.day)只包含价格数据，不含名称")
        print("3. 解决方案建议:")
        print("   - 继续使用服务器获取（部分成功）")
        print("   - 使用akshare联网获取（需要联网）")
        print("   - 接受当前状态，继续后续功能开发")
        
    finally:
        db.close()


if __name__ == '__main__':
    generate_status_report()