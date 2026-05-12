#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试增量更新功能
"""

import sys
sys.path.insert(0, '.')

from config import TDX_DIR, MYSQL_CONFIG
from database import MySQLClient
from fetchers.incremental_updater import IncrementalUpdater

def main():
    print("=== 调试增量更新 ===")
    
    # 1. 检查股票列表
    print("\n1. 检查股票列表:")
    db = MySQLClient(MYSQL_CONFIG)
    sql = "SELECT code, name FROM stock_list WHERE status = 'L' LIMIT 5"
    results = db.query_all(sql)
    print(f"查询到 {len(results)} 条记录")
    for row in results:
        print(f"  {row['code']} - {row['name']}")
    db.close()
    
    # 2. 检查通达信数据文件
    print("\n2. 检查通达信数据文件:")
    import os
    vipdoc_dir = os.path.join(TDX_DIR, "vipdoc")
    sh_lday = os.path.join(vipdoc_dir, "sh", "lday")
    sz_lday = os.path.join(vipdoc_dir, "sz", "lday")
    
    print(f"  上海市场目录: {sh_lday}")
    print(f"  存在: {os.path.exists(sh_lday)}")
    
    print(f"  深圳市场目录: {sz_lday}")
    print(f"  存在: {os.path.exists(sz_lday)}")
    
    # 3. 测试读取通达信数据
    print("\n3. 测试读取通达信数据:")
    updater = IncrementalUpdater()
    
    test_codes = ['600000', '600001', '000001', '000002']
    for code in test_codes:
        data = updater.read_latest_quote_from_tdx(code)
        if data:
            print(f"  {code}: 收盘价={data['close_price']}, 成交量={data['volume']}")
        else:
            print(f"  {code}: 未找到数据")
    
    updater.close()

if __name__ == '__main__':
    main()
