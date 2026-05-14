#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 market_snapshot 表结构
"""

import sys
sys.path.insert(0, '.')

from database import MySQLClient
from config import MYSQL_CONFIG

def main():
    db = MySQLClient(MYSQL_CONFIG)
    
    # 检查 market_snapshot 表结构
    print("检查 market_snapshot 表结构:")
    sql = "DESCRIBE market_snapshot"
    results = db.query_all(sql)
    for row in results:
        print(f"  {row['Field']} - {row['Type']}")
    
    db.close()

if __name__ == '__main__':
    main()
