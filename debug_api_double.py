import requests

BASE_URL = 'http://localhost:9528/api/stocks/filter'

# 测试双季度筛选的各种条件
print("=== 测试双季度筛选API ===")

# 测试1: 年度毛利率 >= 9%
print("\n【测试1】年度毛利率 >= 9%")
response = requests.get(BASE_URL, {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'gross_margin_min2': 9,
    'sort_field': 'code'
})
if response.status_code == 200:
    data = response.json()
    total = data.get('data', {}).get('pagination', {}).get('total_items', 0)
    total_pages = data.get('data', {}).get('pagination', {}).get('total_pages', 1)
    print(f"总记录数: {total}, 总页数: {total_pages}")
    
    # 检查所有页面
    found = False
    found_page = -1
    for page in range(1, min(total_pages + 1, 100)):  # 最多检查100页
        response = requests.get(BASE_URL, {
            'quarter_type': 'two',
            'report_date': '20260331',
            'report_date2': '20251231',
            'gross_margin_min2': 9,
            'sort_field': 'code',
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

# 测试2: Q1营收同比 >= 58%
print("\n【测试2】Q1营收同比 >= 58%")
response = requests.get(BASE_URL, {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'revenue_yoy_min': 58,
    'sort_field': 'code'
})
if response.status_code == 200:
    data = response.json()
    total = data.get('data', {}).get('pagination', {}).get('total_items', 0)
    total_pages = data.get('data', {}).get('pagination', {}).get('total_pages', 1)
    print(f"总记录数: {total}, 总页数: {total_pages}")
    
    found = False
    found_page = -1
    for page in range(1, min(total_pages + 1, 100)):
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
                found = True
                found_page = page
                break
    
    if found:
        print(f"✓ 找到688456在第{found_page}页")
    else:
        print("✗ 未找到688456")
else:
    print(f"✗ HTTP错误: {response.status_code}")

# 测试3: Q1扣非同比 >= 200%
print("\n【测试3】Q1扣非同比 >= 200%")
response = requests.get(BASE_URL, {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'net_profit_yoy_min': 200,
    'sort_field': 'code'
})
if response.status_code == 200:
    data = response.json()
    total = data.get('data', {}).get('pagination', {}).get('total_items', 0)
    total_pages = data.get('data', {}).get('pagination', {}).get('total_pages', 1)
    print(f"总记录数: {total}, 总页数: {total_pages}")
    
    found = False
    found_page = -1
    for page in range(1, min(total_pages + 1, 100)):
        response = requests.get(BASE_URL, {
            'quarter_type': 'two',
            'report_date': '20260331',
            'report_date2': '20251231',
            'net_profit_yoy_min': 200,
            'sort_field': 'code',
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
