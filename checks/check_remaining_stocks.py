#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查未更新的股票
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def check_remaining():
    """检查未更新的股票"""
    db = MySQLClient(MYSQL_CONFIG)

    try:
        sql = "SELECT code, name FROM stock_list WHERE name LIKE '股票%'"
        results = db.query_all(sql)

        print(f'未更新名称的股票 ({len(results)} 只):')
        for r in results:
            print(f'  {r["code"]}: {r["name"]}')

        # 统计未更新股票的市场分布
        sh_count = len([r for r in results if r['code'].startswith(('6', '5'))])
        sz_count = len([r for r in results if r['code'].startswith(('0', '3'))])
        bj_count = len([r for r in results if r['code'].startswith(('4', '8', '9'))])

        print(f'\n市场分布:')
        print(f'  上海: {sh_count} 只')
        print(f'  深圳: {sz_count} 只')
        print(f'  北京: {bj_count} 只')

    finally:
        db.close()


if __name__ == '__main__':
    check_remaining()