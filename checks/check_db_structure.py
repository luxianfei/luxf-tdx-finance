#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

db = MySQLClient(MYSQL_CONFIG)

print('=== stock_list 表结构 ===')
sql = 'DESCRIBE stock_list'
for row in db.query_all(sql):
    print(f'  {row["Field"]}: {row["Type"]}')

print('\n=== company_profile 表结构 ===')
sql = 'DESCRIBE company_profile'
for row in db.query_all(sql):
    print(f'  {row["Field"]}: {row["Type"]}')

db.close()
