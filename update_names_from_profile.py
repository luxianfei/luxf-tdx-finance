#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 company_profile 表的公司全称提取股票简称并更新 stock_list
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def extract_stock_name(full_name):
    """从公司全称提取股票简称"""
    if not full_name or full_name == '--':
        return None
    
    # 去除末尾的常见后缀
    suffixes = ['股份有限公司', '有限公司', '股份公司', '集团股份有限公司', '集团有限公司',
                '(集团)股份有限公司', '(集团)有限公司']
    name = full_name
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    
    # 如果名称太短，直接返回
    if len(name) <= 4:
        return name
    
    # 尝试提取核心部分（去掉行业词）
    industry_words = ['科技', '银行', '证券', '保险', '集团', '控股', '股份', '发展', '投资', '实业',
                      '技术', '股份有限', '有限', '中国', '国际', '实业', '产业', '控股集团']
    
    result = name
    
    # 如果名称较长，尝试提取前半部分
    if len(name) > 6:
        for word in industry_words:
            idx = name.find(word)
            if idx > 0:
                if idx <= 4:
                    result = name[:idx + len(word)]
                else:
                    result = name[:4]
                break
        else:
            result = name[:4]
    
    return result


def update_stock_names_from_profile():
    """从公司概况数据更新股票简称"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取 stock_list 中未更新但在 company_profile 中有数据的股票
        sql = """
        SELECT sl.code, sl.name as list_name, cp.company_name 
        FROM stock_list sl
        JOIN company_profile cp ON sl.code = cp.code
        WHERE sl.name LIKE "股票%" AND cp.company_name IS NOT NULL AND cp.company_name != '--'
        """
        results = db.query_all(sql)
        
        print(f"找到 {len(results)} 只可以从 company_profile 更新名称的股票")
        
        if not results:
            print("没有需要更新的股票")
            return
        
        # 展示部分提取结果
        print("\n提取示例:")
        for r in results[:10]:
            short_name = extract_stock_name(r['company_name'])
            print(f"  {r['code']}: {r['company_name']} -> {short_name}")
        
        # 更新股票名称
        update_sql = "UPDATE stock_list SET name = %s WHERE code = %s"
        
        conn = db.connect()
        with conn.cursor() as cursor:
            count = 0
            for r in results:
                short_name = extract_stock_name(r['company_name'])
                if short_name:
                    cursor.execute(update_sql, (short_name, r['code']))
                    count += 1
            conn.commit()
        
        print(f"\n成功更新 {count} 只股票的名称")
        
    finally:
        db.close()


if __name__ == '__main__':
    update_stock_names_from_profile()