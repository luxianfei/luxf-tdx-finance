from fetchers.finance_collector import FinanceCollector

collector = FinanceCollector()

# 测试获取总股本
total_shares = collector._get_total_shares_from_base_dbf('688456')
print(f"从base.dbf获取的总股本: {total_shares} 万股")

# 测试采集数据
df, total_shares = collector.collect('688456', max_quarters=1)
print(f"\n采集到的总股本: {total_shares} 万股")
print(f"DataFrame 中的 total_shares: {df['total_shares'].iloc[0] if len(df) > 0 else 'N/A'}")
