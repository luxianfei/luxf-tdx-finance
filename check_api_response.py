import requests

BASE_URL = 'http://localhost:9528/api/stocks/filter'

# 获取第一页数据，检查返回的内容
response = requests.get(BASE_URL, {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'revenue_yoy_min': 58,
    'sort_field': 'code',
    'sort_order': 'desc',
    'page': 1,
    'limit': 50
})

if response.status_code == 200:
    data = response.json()
    items = data.get('data', {}).get('items', [])
    print(f"第一页记录数: {len(items)}")
    
    # 打印前10条记录的代码和营收同比
    print("\n前10条记录:")
    for item in items[:10]:
        print(f"  {item['code']} - {item['name']}: 营收同比={item['revenue_yoy']}%")
    
    # 检查是否有688开头的股票
    print("\n688开头的股票:")
    count_688 = 0
    for item in items:
        if item['code'].startswith('688'):
            print(f"  {item['code']} - {item['name']}: 营收同比={item['revenue_yoy']}%")
            count_688 += 1
    print(f"\n第一页共有{count_688}只688开头的股票")
else:
    print(f"HTTP错误: {response.status_code}")
    print(response.text)
