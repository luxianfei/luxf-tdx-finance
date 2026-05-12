#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试批量采集脚本
"""

import sys
sys.path.insert(0, '.')

from fetchers.batch_collect_local import get_stock_codes_from_local, init_stock_list, batch_collect_finance_data
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

# 获取股票列表
codes = get_stock_codes_from_local()
print(f'共发现 {len(codes)} 只股票')

# 使用前10只测试
test_codes = codes[:10]
print(f'测试采集: {test_codes}')

# 创建数据库客户端
db_client = MySQLClient(MYSQL_CONFIG)

try:
    # 初始化股票列表
    init_stock_list(db_client, test_codes)
    
    # 批量采集（不采集盈利预测）
    stats = batch_collect_finance_data(db_client, test_codes, fetch_forecast=False)
    
    print('采集结果:')
    print(f"财务数据: {stats['finance_success']}/{stats['total']} 成功")
    print(f"公司概况: {stats['profile_success']}/{stats['total']} 成功")
finally:
    db_client.close()
