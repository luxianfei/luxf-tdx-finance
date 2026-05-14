import json

# 读取 workbuddy 数据
with open('workbuddy/stock_report_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 查找688456的数据
for item in data:
    if item.get('code') == '688456':
        print("=== 688456 workbuddy 数据 ===")
        print(f"总股本: {item.get('total_shares')}")
        print(f"总股本(万股): {item.get('total_shares') / 10000}")
        
        # 计算市值
        current_price = 81.5
        market_cap = current_price * item.get('total_shares') / 100000000
        print(f"计算市值: {market_cap:.2f} 亿元")
        break
