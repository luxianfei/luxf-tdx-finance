import requests

BASE_URL = 'http://localhost:9528/api/stocks/filter'

# 测试不同排序方式
print("=== 测试排序 ===")

# 测试1: sort_order=desc（应该按代码降序）
print("\n【测试1】sort_order=desc")
response = requests.get(BASE_URL, {
    'report_date': '20260331',
    'gross_margin_min': 7,
    'sort_field': 'code',
    'sort_order': 'desc',
    'page': 1
})
if response.status_code == 200:
    data = response.json()
    items = data.get('data', {}).get('items', [])
    print("第一页股票代码:")
    for item in items[:5]:
        print(f"  {item['code']}")

# 测试2: sort_order=asc（应该按代码升序）
print("\n【测试2】sort_order=asc")
response = requests.get(BASE_URL, {
    'report_date': '20260331',
    'gross_margin_min': 7,
    'sort_field': 'code',
    'sort_order': 'asc',
    'page': 1
})
if response.status_code == 200:
    data = response.json()
    items = data.get('data', {}).get('items', [])
    print("第一页股票代码:")
    for item in items[:5]:
        print(f"  {item['code']}")

# 测试3: 不指定sort_order（默认应该是desc）
print("\n【测试3】不指定sort_order")
response = requests.get(BASE_URL, {
    'report_date': '20260331',
    'gross_margin_min': 7,
    'sort_field': 'code',
    'page': 1
})
if response.status_code == 200:
    data = response.json()
    items = data.get('data', {}).get('items', [])
    print("第一页股票代码:")
    for item in items[:5]:
        print(f"  {item['code']}")
