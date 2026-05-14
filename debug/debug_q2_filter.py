import requests

BASE_URL = 'http://localhost:9528/api/stocks/filter'

# 测试双季度筛选，使用Q2的条件
print("=== 测试年度毛利率 >= 9% ===")
response = requests.get(BASE_URL, {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'gross_margin_min2': 9,
    'sort_field': 'code',
    'sort_order': 'desc',
    'page': 1,
    'limit': 30
})

if response.status_code == 200:
    data = response.json()
    items = data.get('data', {}).get('items', [])
    print(f"第一页记录数: {len(items)}")
    
    # 打印前10条记录
    print("\n前10条记录:")
    for item in items[:10]:
        print(f"  {item['code']} - {item['name']}: 毛利率={item['gross_margin']}%")
    
    # 检查是否有688456
    found = any(item['code'] == '688456' for item in items)
    print(f"\n688456是否在第一页: {found}")
else:
    print(f"HTTP错误: {response.status_code}")
    print(response.text)
