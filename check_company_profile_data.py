#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 company_profile 表中的数据，看是否有公司全称可以用来提取简称
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def check_company_profiles():
    """检查公司概况数据"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取有公司名称的记录
        sql = """
        SELECT code, company_name, industry, business_scope 
        FROM company_profile 
        WHERE company_name IS NOT NULL AND company_name != '--'
        LIMIT 20
        """
        results = db.query_all(sql)
        
        print(f"company_profile 表中有 {len(results)} 条有公司名称的记录（显示前20条）:")
        for r in results:
            print(f"\n代码: {r['code']}")
            print(f"  公司名称: {r['company_name']}")
            print(f"  行业: {r['industry']}")
            print(f"  经营范围: {r['business_scope'][:50] if r['business_scope'] else '无'}")
        
        # 统计数量
        sql_count = """
        SELECT COUNT(*) as cnt FROM company_profile 
        WHERE company_name IS NOT NULL AND company_name != '--'
        """
        count = db.query_one(sql_count)
        print(f"\ncompany_profile 表中有 {count['cnt']} 条有公司名称的记录")
        
        # 检查 stock_list 中未更新的股票是否在 company_profile 中有数据
        sql_join = """
        SELECT sl.code, sl.name as list_name, cp.company_name 
        FROM stock_list sl
        LEFT JOIN company_profile cp ON sl.code = cp.code
        WHERE sl.name LIKE "股票%" AND cp.company_name IS NOT NULL AND cp.company_name != '--'
        LIMIT 10
        """
        joined = db.query_all(sql_join)
        
        print(f"\n有 {len(joined)} 只未更新名称的股票在 company_profile 中有数据（显示前10条）:")
        for r in joined:
            print(f"  {r['code']}: {r['list_name']} -> {r['company_name']}")
        
    finally:
        db.close()


if __name__ == '__main__':
    check_company_profiles()