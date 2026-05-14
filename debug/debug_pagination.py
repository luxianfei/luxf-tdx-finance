import requests

BASE_URL = 'http://localhost:9528/api/stocks/filter'

# 测试Q1营收同比 >= 58%，检查所有页面
print("=== 测试Q1营收同比 >= 58% ===")
response = requests.get(BASE_URL, {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'revenue_yoy_min': 58,
    'sort_field': 'code',
    'sort_order': 'desc',
    'page': 1
})

if response.status_code == 200:
    data = response.json()
    total_pages = data.get('data', {}).get('pagination', {}).get('total_pages', 1)
    total_items = data.get('data', {}).get('pagination', {}).get('total_items', 0)
    print(f"总记录数: {total_items}, 总页数: {total_pages}")
    
    # 检查所有页面
    found = False
    found_page = -1
    for page in range(1, total_pages + 1):
        response = requests.get(BASE_URL, {
            'quarter_type': 'two',
            'report_date': '20260331',
            'report_date2': '20251231',
            'revenue_yoy_min': 58,
            'sort_field': 'code',
            'sort_order': 'desc',
            'page': page
        })
        if response.status_code == 200:
            page_data = response.json()
            items = page_data.get('data', {}).get('items', [])
            codes = [item['code'] for item in items]
            if '688456' in codes:
                found = True
                found_page = page
                break
    
    if found:
        print(f"✓ 找到688456在第{found_page}页")
    else:
        print("✗ 未找到688456")
else:
    print(f"✗ HTTP错误: {response.status_code}")

# 测试简化查询（不带排序）
print("\n\n=== 测试不带排序的查询 ===")
response = requests.get(BASE_URL, {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'revenue_yoy_min': 58
})

if response.status_code == 200:
    data = response.json()
    total_pages = data.get('data', {}).get('pagination', {}).get('total_pages', 1)
    total_items = data.get('data', {}).get('pagination', {}).get('total_items', 0)
    print(f"总记录数: {total_items}, 总页数: {total_pages}")
    
    # 检查所有页面
    found = False
    for page in range(1, min(total_pages + 1, 10)):  # 只检查前10页
        response = requests.get(BASE_URL, {
            'quarter_type': 'two',
            'report_date': '20260331',
            'report_date2': '20251231',
            'revenue_yoy_min': 58,
            'page': page
        })
        if response.status_code == 200:
            page_data = response.json()
            items = page_data.get('data', {}).get('items', [])
            codes = [item['code'] for item in items]
            if '688456' in codes:
                found = True
                break
    
    if found:
        print("✓ 不带排序时找到688456")
    else:
        print("✗ 不带排序时也未找到688456")
else:
    print(f"✗ HTTP错误: {response.status_code}")
