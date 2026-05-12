#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试财务数据插入
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG
from fetchers.finance_collector import FinanceCollector

def test_insert():
    """测试单只股票财务数据插入"""
    db = MySQLClient(MYSQL_CONFIG)
    collector = FinanceCollector()
    
    code = '600725'
    print(f"测试采集股票 {code} 的财务数据...")
    
    try:
        df, total_shares = collector.collect(code, max_quarters=20)
        print(f"获取到 {len(df)} 条季度数据")
        
        if len(df) > 0:
            # 转换为数据库记录格式
            finance_data = []
            current_time = datetime.now()
            
            for _, row in df.iterrows():
                record = {
                    'code': code,
                    'report_date': int(row['报告期']),
                    'revenue': float(row.get('revenue_quarterly_w', 0) * 10000) if row.get('revenue_quarterly_w') else None,
                    'net_profit': float(row.get('net_profit_attr_w', 0) * 10000) if row.get('net_profit_attr_w') else None,
                    'eps': float(row.get('eps_basic', 0)) if row.get('eps_basic') else None,
                    'roe': float(row.get('roe_diluted', 0)) if row.get('roe_diluted') else None,
                    'roa': None,
                    'gross_margin': float(row.get('gross_margin', 0)) if row.get('gross_margin') else None,
                    'net_margin': None,
                    'debt_ratio': None,
                    'current_ratio': None,
                    'quick_ratio': None,
                    'operating_cash_flow': float(row.get('cashflow_ps', 0) * 10000) if row.get('cashflow_ps') else None,
                    'total_assets': None,
                    'total_liabilities': None,
                    'created_at': current_time,
                    'updated_at': current_time
                }
                finance_data.append(record)
            
            # 插入数据库
            conn = db.connect()
            with conn.cursor() as cursor:
                for data in finance_data:
                    sql = """
                    INSERT INTO quarterly_finance (
                        code, report_date, revenue, net_profit, eps,
                        roe, roa, gross_margin, net_margin,
                        debt_ratio, current_ratio, quick_ratio,
                        operating_cash_flow, total_assets, total_liabilities,
                        created_at, updated_at
                    ) VALUES (
                        %(code)s, %(report_date)s, %(revenue)s, %(net_profit)s, %(eps)s,
                        %(roe)s, %(roa)s, %(gross_margin)s, %(net_margin)s,
                        %(debt_ratio)s, %(current_ratio)s, %(quick_ratio)s,
                        %(operating_cash_flow)s, %(total_assets)s, %(total_liabilities)s,
                        %(created_at)s, %(updated_at)s
                    ) ON DUPLICATE KEY UPDATE
                        revenue = VALUES(revenue),
                        net_profit = VALUES(net_profit),
                        eps = VALUES(eps),
                        roe = VALUES(roe),
                        updated_at = VALUES(updated_at)
                    """
                    cursor.execute(sql, data)
                
                conn.commit()
                print(f"成功写入 {len(finance_data)} 条记录")
        
        # 检查数据库中的记录数
        result = db.query_one("SELECT COUNT(*) as total FROM quarterly_finance")
        print(f"数据库中季度财务记录总数: {result['total']}")
        
        # 检查该股票的记录数
        result = db.query_one("SELECT COUNT(*) as cnt FROM quarterly_finance WHERE code = %s", (code,))
        print(f"股票 {code} 的季度记录数: {result['cnt']}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    test_insert()