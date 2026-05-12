import requests

BASE_URL = 'http://localhost:9528/api/stocks/filter'

# 测试年度毛利率 >= 9%，直接检查第209页
response = requests.get(BASE_URL, {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'gross_margin_min2': 9,
    'sort_field': 'code',
    'page': 209
})

print("=== 检查第209页 ===")
if response.status_code == 200:
    data = response.json()
    items = data.get('data', {}).get('items', [])
    print(f"第209页记录数: {len(items)}")
    
    # 打印该页的所有股票代码
    print("\n第209页的股票代码:")
    for item in items:
        print(f"  {item['code']} - {item['name']}")
    
    # 检查是否有688456
    found = any(item['code'] == '688456' for item in items)
    print(f"\n688456是否在第209页: {found}")
else:
    print(f"HTTP错误: {response.status_code}")

# 测试Q1营收同比 >= 58%，检查688456的位置
print("\n\n=== 测试Q1营收同比 >= 58% ===")
response = requests.get(BASE_URL, {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'revenue_yoy_min': 58,
    'sort_field': 'code'
})

if response.status_code == 200:
    data = response.json()
    total_pages = data.get('data', {}).get('pagination', {}).get('total_pages', 1)
    print(f"总页数: {total_pages}")
    
    # 检查688456应该在第几页
    # 688456是688开头，应该在后面的页面
    for page in range(total_pages, max(total_pages - 5, 1), -1):
        response = requests.get(BASE_URL, {
            'quarter_type': 'two',
            'report_date': '20260331',
            'report_date2': '20251231',
            'revenue_yoy_min': 58,
            'sort_field': 'code',
            'page': page
        })
        if response.status_code == 200:
            page_data = response.json()
            items = page_data.get('data', {}).get('items', [])
            codes = [item['code'] for item in items]
            if '688456' in codes:
                print(f"找到688456在第{page}页")
                break
else:
    print(f"HTTP错误: {response.status_code}")
