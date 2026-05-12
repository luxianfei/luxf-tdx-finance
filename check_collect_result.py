#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查采集结果
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

def check_collect_result():
    """检查采集结果"""
    db = MySQLClient(MYSQL_CONFIG)
    
    print("=" * 60)
    print("采集结果统计")
    print("=" * 60)
    
    # 统计 stock_list 表
    total_stocks = db.query_one("SELECT COUNT(*) as cnt FROM stock_list")
    print(f"股票总数: {total_stocks['cnt']}")
    
    updated_names = db.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE name NOT LIKE '股票%'")
    not_updated_names = db.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE name LIKE '股票%'")
    print(f"已更新名称: {updated_names['cnt']} 只")
    print(f"未更新名称: {not_updated_names['cnt']} 只")
    
    # 统计 quarterly_finance 表
    total_records = db.query_one("SELECT COUNT(*) as cnt FROM quarterly_finance")
    print(f"\n季度财务记录总数: {total_records['cnt']}")
    
    distinct_stocks = db.query_one("SELECT COUNT(DISTINCT code) as cnt FROM quarterly_finance")
    print(f"已采集财务数据的股票数: {distinct_stocks['cnt']}")
    
    # 检查 updated_at 字段
    has_updated_at = db.query_one("SELECT COUNT(*) as cnt FROM quarterly_finance WHERE updated_at IS NOT NULL")
    no_updated_at = db.query_one("SELECT COUNT(*) as cnt FROM quarterly_finance WHERE updated_at IS NULL")
    print(f"\nupdated_at 已更新的记录: {has_updated_at['cnt']}")
    print(f"updated_at 未更新的记录: {no_updated_at['cnt']}")
    
    # 获取最新更新时间
    latest_update = db.query_one("SELECT MAX(updated_at) as latest FROM quarterly_finance")
    if latest_update['latest']:
        print(f"最新更新时间: {latest_update['latest']}")
    
    # 检查每个股票的季度数量分布
    print("\n季度数据数量分布:")
    qtr_dist = db.query_all("""
        SELECT qtr_cnt, COUNT(*) as stock_cnt 
        FROM (SELECT code, COUNT(*) as qtr_cnt FROM quarterly_finance GROUP BY code) t 
        GROUP BY qtr_cnt 
        ORDER BY qtr_cnt DESC 
        LIMIT 10
    """)
    for row in qtr_dist:
        print(f"  {row['qtr_cnt']} 个季度: {row['stock_cnt']} 只股票")
    
    db.close()

if __name__ == '__main__':
    check_collect_result()