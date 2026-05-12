#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从workbuddy数据保存到数据库
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
        
        # 1. 保存K线历史数据
        historical = data.get('historical', [])
        if historical:
            for record in historical:
                try:
                    conn = db.connect()
                    sql = """
                        INSERT IGNORE INTO stock_kline 
                        (code, trade_date, open_price, high_price, low_price, close_price, volume, amount, change_pct)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    with conn.cursor() as cursor:
                        cursor.execute(sql, (
                            code,
                            record['date'],
                            record['open'],
                            record['high'],
                            record['low'],
                            record['price'],
                            record['volume'],
                            record['amount'],
                            record['change_pct']
                        ))
                    conn.commit()
                except Exception as e:
                    pass
            print(f"  K线数据: {len(historical)} 条已保存")
        
        # 2. 保存公司信息
        company = data.get('company', {})
        if company:
            try:
                conn = db.connect()
                sql = """
                    INSERT INTO company_profile 
                    (code, name, industry, main_business, listing_date, total_shares, circulating_shares)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    name=VALUES(name), industry=VALUES(industry), main_business=VALUES(main_business),
                    listing_date=VALUES(listing_date), total_shares=VALUES(total_shares),
                    circulating_shares=VALUES(circulating_shares)
                """
                with conn.cursor() as cursor:
                    cursor.execute(sql, (
                        code,
                        str(company.get('name', '')),
                        str(company.get('industry', '')),
                        str(company.get('main_business', '')),
                        str(company.get('listing_date', '')),
                        str(company.get('total_shares', '')),
                        str(company.get('circulating_shares', ''))
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
                sql = """
                    UPDATE stock_list 
                    SET current_price = %s, change_pct = %s, market_cap = %s, 
                        pe_ratio = %s, industry = %s
                    WHERE code = %s
                """
                with conn.cursor() as cursor:
                    cursor.execute(sql, (
                        float(realtime.get('price', 0)),
                        float(realtime.get('change_pct', 0)),
                        float(realtime.get('market_cap', 0)),
                        float(realtime.get('pe_ratio', 0)),
                        str(company.get('industry', '')),
                        code
                    ))
                conn.commit()
                print(f"  行情数据: 价格 {realtime.get('price')}, 涨跌幅 {realtime.get('change_pct')}%")
            except Exception as e:
                print(f"  行情数据更新失败: {e}")
        
        print("\n数据保存完成！")
        
    finally:
        db.close()


if __name__ == "__main__":
    save_workbuddy_data_to_db()
