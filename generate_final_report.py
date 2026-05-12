#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查最后剩余的7只股票并生成完成报告
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def generate_report():
    """生成完成报告"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 统计
        sql_updated = "SELECT COUNT(*) as cnt FROM stock_list WHERE name NOT LIKE '股票%'"
        sql_not_updated = "SELECT COUNT(*) as cnt FROM stock_list WHERE name LIKE '股票%'"
        
        updated = db.query_one(sql_updated)['cnt']
        not_updated = db.query_one(sql_not_updated)['cnt']
        
        print("="*60)
        print("股票名称更新完成报告")
        print("="*60)
        print()
        print(f"  已更新名称: {updated} 只")
        print(f"  未更新名称: {not_updated} 只")
        print()
        
        if not_updated > 0:
            print("  未更新的股票:")
            sql = "SELECT code, name FROM stock_list WHERE name LIKE '股票%' ORDER BY code"
            for row in db.query_all(sql):
                print(f"    {row['code']}: {row['name']}")
            
            print()
            print("-"*60)
            print("说明:")
            print("  这7只股票在以下数据源中均未找到数据:")
            print("    - akshare (stock_info_a_code_name, stock_zh_a_spot)")
            print("    - akshare (stock_individual_info_em 逐个查询)")
            print("    - 通达信远程服务器 (get_security_list)")
            print("    - 通达信远程服务器 (get_security_quotes)")
            print("    - 通达信远程服务器 (get_company_info - F10)")
            print("    - 通达信本地F10目录")
            print()
            print("  这些股票可能是:")
            print("    - 已退市股票")
            print("    - 长期停牌股票")
            print("    - 已改名且原代码不再使用的股票")
            print("    - 其他非活跃股票")
            print()
            print("建议:")
            print("  可以从stock_list表中删除这些无效股票记录")
        
        print()
        print("="*60)
        
        return updated, not_updated
        
    finally:
        db.close()


if __name__ == '__main__':
    generate_report()