#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的增量更新功能
"""

import sys
sys.path.insert(0, '.')

from fetchers.incremental_updater import IncrementalUpdater

def main():
    updater = IncrementalUpdater()
    
    # 测试获取股票列表
    stocks = updater.get_stock_list()
    print(f'股票列表数量: {len(stocks)}')
    if stocks:
        print('前5只股票:')
        for s in stocks[:5]:
            print(f'  {s["code"]} - {s["name"]}')
    
    # 测试读取通达信数据
    test_codes = ['600000', '000001']
    print('\n测试通达信数据读取:')
    for code in test_codes:
        data = updater.read_latest_quote_from_tdx(code)
        if data:
            print(f'{code}: 收盘价={data["close_price"]}, 成交量={data["volume"]}')
        else:
            print(f'{code}: 未找到数据或数据无效')
    
    updater.close()

if __name__ == '__main__':
    main()
