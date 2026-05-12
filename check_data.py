#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from database import MySQLClient
from config import MYSQL_CONFIG

def check_finance_data(code):
    with MySQLClient(MYSQL_CONFIG) as client:
        # 查询原始财务数据
        sql = '''
        SELECT report_date, year, quarter, revenue_yoy, kfe_np_yoy, kfe_np_ttm_w 
        FROM quarterly_finance 
        WHERE code = %s 
        ORDER BY report_date DESC
        '''
        results = client.query_all(sql, (code,))
        
        print('原始财务数据:')
        for row in results:
            print(f"{row['year']}Q{row['quarter']} ({row['report_date']}):")
            print(f"  营收同比: {row['revenue_yoy']}")
            print(f"  扣非同比: {row['kfe_np_yoy']}")
            print(f"  扣非TTM: {row['kfe_np_ttm_w']}")
            print()

if __name__ == '__main__':
    check_finance_data('688456')