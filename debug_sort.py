import requests

# 测试排序是否生效
response = requests.get('http://localhost:9528/api/stocks/filter', {
    'report_date': '20260331',
    'gross_margin_min': 7,
    'gross_margin_max': 8,
    'sort_field': 'code',
    'sort_order': 'asc'
})

print("=== 测试排序 ===")
if response.status_code == 200:
    data = response.json()
    items = data.get('data', {}).get('items', [])
    print(f"记录数: {len(items)}")
    print("\n第一页股票代码:")
    for item in items:
        print(f"  {item['code']} - {item['name']}")
    
    print(f"\n688456是否在第一页: {any(item['code'] == '688456' for item in items)}")
else:
    print(f"HTTP错误: {response.status_code}")
