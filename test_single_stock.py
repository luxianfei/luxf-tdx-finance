#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单只股票更新
"""

import sys
sys.path.insert(0, '.')

from fetchers.incremental_updater import IncrementalUpdater

def main():
    updater = IncrementalUpdater()
    
    # 测试读取通达信数据
    test_codes = ['600000', '000001']
    print('测试通达信数据读取:')
    for code in test_codes:
        data = updater.read_latest_quote_from_tdx(code)
        if data:
            print(f'{code}: 收盘价={data["price"]}, 成交量={data["volume"]}')
        else:
            print(f'{code}: 未找到数据或数据无效')
    
    # 测试单只股票更新
    print('\n测试单只股票更新:')
    
    # 只更新前5只股票进行测试
    stocks = updater.get_stock_list()[:5]
    success_count = 0
    fail_count = 0
    
    for stock in stocks:
        code = stock['code']
        name = stock['name']
        try:
            quote_data = updater.read_latest_quote_from_tdx(code)
            if quote_data:
                # 获取昨日收盘价用于计算涨跌
                sql = "SELECT price FROM market_snapshot WHERE code = %s ORDER BY snapshot_time DESC LIMIT 1"
                prev_data = updater.db_client.query_one(sql, (code,))
                
                # 转换为float类型，避免Decimal和float类型不匹配问题
                prev_close = float(prev_data['price']) if prev_data else quote_data['price']
                change = round(quote_data['price'] - prev_close, 2)
                change_percent = round((change / prev_close) * 100, 2) if prev_close != 0 else 0
                
                # 获取市值数据
                sql = "SELECT market_cap FROM stock_list WHERE code = %s"
                basic_data = updater.db_client.query_one(sql, (code,))
                market_cap = float(basic_data['market_cap']) if basic_data and basic_data.get('market_cap') else 0
                
                # 更新数据（去掉name字段）
                sql = """
                    INSERT INTO market_snapshot 
                    (code, price, `change`, change_percent, market_cap, 
                     volume, amount, high, low, open, prev_close, snapshot_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE
                    price = VALUES(price), `change` = VALUES(`change`),
                    change_percent = VALUES(change_percent), market_cap = VALUES(market_cap),
                    volume = VALUES(volume), amount = VALUES(amount),
                    high = VALUES(high), low = VALUES(low), open = VALUES(open),
                    prev_close = VALUES(prev_close), snapshot_time = NOW()
                """
                params = (
                    code, quote_data['price'], change, change_percent, market_cap,
                    quote_data['volume'], quote_data['amount'],
                    quote_data['high'], quote_data['low'], quote_data['open'], prev_close
                )
                updater.db_client.execute(sql, params)
                success_count += 1
                print(f'成功: {code} {name}')
            else:
                fail_count += 1
                print(f'失败(无数据): {code} {name}')
        except Exception as e:
            fail_count += 1
            print(f'失败({e}): {code} {name}')
    
    updater.db_client.commit()
    print(f'\n测试完成: 成功 {success_count} 只，失败 {fail_count} 只')
    
    updater.close()

if __name__ == '__main__':
    main()
