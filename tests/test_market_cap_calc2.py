from fetchers.incremental_updater import IncrementalUpdater

updater = IncrementalUpdater()

# 手动更新688456
quote_data = updater.read_latest_quote_from_tdx('688456')
print(f'行情数据: {quote_data}')

if quote_data:
    prev_close = quote_data.get('prev_close') or quote_data['price']
    change = round(quote_data['price'] - prev_close, 2)
    change_percent = round((change / prev_close) * 100, 2) if prev_close != 0 else 0
    
    print(f'当前价格: {quote_data["price"]}')
    print(f'前收盘价: {prev_close}')
    print(f'涨跌金额: {change}')
    print(f'涨跌幅: {change_percent}%')
    
    # 使用新方法从base.dbf获取总股本
    total_shares = updater._get_total_shares_from_base_dbf('688456')
    if total_shares:
        print(f'总股本: {total_shares} 万股')
        market_cap = quote_data['price'] * total_shares / 10000
        print(f'计算市值: {market_cap:.2f} 亿元')
    else:
        print('无法从base.dbf获取总股本')
    
updater.db_client.close()
