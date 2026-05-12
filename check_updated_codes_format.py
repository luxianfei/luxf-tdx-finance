#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查已更新和未更新的股票代码格式差异
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def check_code_formats():
    """检查股票代码格式"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取已更新的股票（名称不以"股票"开头）
        sql_updated = """
        SELECT code, name FROM stock_list 
        WHERE name NOT LIKE "股票%"
        LIMIT 20
        """
        updated = db.query_all(sql_updated)
        
        print("已更新的股票（前20条）:")
        for r in updated:
            print(f"  {r['code']}: {r['name']}")
        
        # 获取未更新的上海A股
        sql_unupdated_sh = """
        SELECT code FROM stock_list 
        WHERE name LIKE "股票%" AND (code LIKE "60%" OR code LIKE "688%")
        LIMIT 20
        """
        unupdated_sh = db.query_all(sql_unupdated_sh)
        
        print("\n未更新的上海A股（前20条）:")
        for r in unupdated_sh:
            print(f"  {r['code']}")
        
        # 检查已更新代码的长度分布
        sql_len = """
        SELECT LENGTH(code) as len, COUNT(*) as cnt 
        FROM stock_list 
        WHERE name NOT LIKE "股票%"
        GROUP BY LENGTH(code)
        """
        len_dist = db.query_all(sql_len)
        
        print("\n已更新股票代码长度分布:")
        for r in len_dist:
            print(f"  长度{r['len']}: {r['cnt']}只")
        
    finally:
        db.close()


if __name__ == '__main__':
    check_code_formats()