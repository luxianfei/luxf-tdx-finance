import requests

# 测试查看数据类型
response = requests.get('http://localhost:9528/api/stocks/filter', {
    'report_date': '20260331',
    'gross_margin_min': 7
})

print("=== API响应 ===")
if response.status_code == 200:
    data = response.json()
    items = data.get('data', {}).get('items', [])
    
    # 检查第一条数据的类型
    if items:
        first_item = items[0]
        print("第一条数据:")
        print(f"  code: {first_item['code']}")
        print(f"  name: {first_item['name']}")
        print(f"  gross_margin: {first_item['gross_margin']} (类型: {type(first_item['gross_margin'])})")
        print(f"  revenue_yoy: {first_item['revenue_yoy']} (类型: {type(first_item['revenue_yoy'])})")
        print(f"  net_profit_yoy: {first_item['net_profit_yoy']} (类型: {type(first_item['net_profit_yoy'])})")

else:
    print(f"HTTP错误: {response.status_code}")
    print(response.text)
