import requests

# 测试单个筛选条件并打印结果
response = requests.get('http://localhost:9528/api/stocks/filter', {
    'report_date': '20260331',
    'gross_margin_min': 7
})

print("=== API响应 ===")
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"成功: {data.get('success')}")
    items = data.get('data', {}).get('items', [])
    print(f"记录数: {len(items)}")
    print(f"分页: {data.get('data', {}).get('pagination', {})}")
    print("\n返回的股票代码:")
    for item in items:
        print(f"  {item['code']} - {item['name']} - 毛利率: {item['gross_margin']}%")
    
    print("\n688456是否在结果中:", any(item['code'] == '688456' for item in items))
else:
    print(f"错误: {response.text}")
