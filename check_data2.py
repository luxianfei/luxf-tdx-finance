#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import MySQLClient
from config import MYSQL_CONFIG

def check_finance_data(code):
    with MySQLClient(MYSQL_CONFIG) as client:
        # 查询原始财务数据（包括基础数据）
        sql = '''
        SELECT report_date, year, quarter, revenue_quarterly_w, revenue_yoy, 
               kfe_np_quarterly_w, kfe_np_yoy, kfe_np_ttm_w, net_profit_attr_w
        FROM quarterly_finance 
        WHERE code = %s 
        ORDER BY report_date DESC
        '''
        results = client.query_all(sql, (code,))
        
        print('原始财务数据:')
        print(f"{'报告期':<12} {'营收(万)':<12} {'营收同比(%)':<12} {'扣非(万)':<12} {'扣非同比(%)':<12} {'净利润(万)':<12}")
        print('-' * 80)
        for row in results:
            print(f"{row['year']}Q{row['quarter']:<4} {row['revenue_quarterly_w']:<12} {str(row['revenue_yoy']):<12} {row['kfe_np_quarterly_w']:<12} {str(row['kfe_np_yoy']):<12} {row['net_profit_attr_w']:<12}")

if __name__ == '__main__':
    check_finance_data('688456')