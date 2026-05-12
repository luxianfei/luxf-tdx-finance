import json

# 读取 workbuddy 数据
with open('workbuddy/stock_report_data.json', 'r', encoding='utf-8') as f:
    content = f.read()
    # 尝试解析为JSON
    try:
        data = json.loads(content)
        print(f"数据类型: {type(data)}")
        if isinstance(data, dict):
            print(f"键: {list(data.keys())[:10]}")
            # 查找包含688456的数据
            for key, value in data.items():
                if isinstance(value, dict) and value.get('code') == '688456':
                    print(f"\n=== 688456 workbuddy 数据 ===")
                    print(f"总股本: {value.get('total_shares')}")
                    total_shares = value.get('total_shares')
                    if total_shares:
                        print(f"总股本(万股): {total_shares / 10000}")
                        current_price = 81.5
                        market_cap = current_price * total_shares / 100000000
                        print(f"计算市值: {market_cap:.2f} 亿元")
                    break
        elif isinstance(data, list):
            print(f"列表长度: {len(data)}")
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        print(f"内容预览: {content[:500]}")
