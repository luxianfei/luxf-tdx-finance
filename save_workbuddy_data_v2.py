#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从workbuddy数据保存到数据库（修复列名）
"""

import sys
import json
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def save_workbuddy_data_to_db():
    """保存workbuddy的stock_report_data.json到数据库"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        with open('workbuddy/stock_report_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        code = '688456'
        print(f"正在保存 {code} 的数据到数据库...")
        
        # 1. 保存K线历史数据（已保存，跳过）
        
        # 2. 保存公司信息
        company = data.get('company', {})
        if company:
            try:
                conn = db.connect()
                sql = """
                    INSERT INTO company_profile 
                    (code, company_name, industry, business_scope, list_date, reg_capital)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    company_name=VALUES(company_name), industry=VALUES(industry),
                    business_scope=VALUES(business_scope), list_date=VALUES(list_date),
                    reg_capital=VALUES(reg_capital)
                """
                with conn.cursor() as cursor:
                    cursor.execute(sql, (
                        code,
                        str(company.get('name', '')),
                        str(company.get('industry', '')),
                        str(company.get('main_business', '')),
                        int(company.get('listing_date', 0)) if company.get('listing_date') else 0,
                        str(company.get('total_shares', ''))
                    ))
                conn.commit()
                print(f"  公司信息: {company.get('name')} - {company.get('industry')}")
            except Exception as e:
                print(f"  公司信息保存失败: {e}")
        
        # 3. 更新stock_list表
        realtime = data.get('realtime', {})
        if realtime:
            try:
                conn = db.connect()
                # 先检查是否有这些列，没有就添加
                try:
                    check_sql = "SHOW COLUMNS FROM stock_list LIKE 'current_price'"
                    has_col = db.query_one(check_sql)
                    if not has_col:
                        add_sql = "ALTER TABLE stock_list ADD COLUMN current_price DECIMAL(10,2), ADD COLUMN change_pct DECIMAL(6,2), ADD COLUMN market_cap DECIMAL(20,2), ADD COLUMN pe_ratio DECIMAL(10,2)"
                        db.execute(add_sql)
                except Exception:
                    pass
                
                sql = """
                    UPDATE stock_list 
                    SET industry = %s
                    WHERE code = %s
                """
                with conn.cursor() as cursor:
                    cursor.execute(sql, (
                        str(company.get('industry', '')),
                        code
                    ))
                conn.commit()
                print(f"  stock_list已更新")
            except Exception as e:
                print(f"  stock_list更新失败: {e}")
        
        print("\n数据保存完成！")
        
    finally:
        db.close()


if __name__ == "__main__":
    save_workbuddy_data_to_db()
