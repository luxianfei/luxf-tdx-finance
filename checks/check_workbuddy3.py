import json

# 读取 workbuddy 数据
with open('workbuddy/stock_report_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    
print(f"code: {data.get('code')}")
print(f"\n=== company 数据 ===")
company = data.get('company', {})
for key, value in company.items():
    print(f"{key}: {value}")

# 计算市值
total_shares = company.get('total_shares')
if total_shares:
    current_price = 81.5
    market_cap = current_price * total_shares / 100000000
    print(f"\n计算市值（{current_price} × {total_shares} / 1e8）: {market_cap:.2f} 亿元")
