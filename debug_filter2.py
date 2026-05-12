import requests

# 测试查看完整的SQL查询参数
response = requests.get('http://localhost:9528/api/stocks/filter', {
    'report_date': '20260331',
    'gross_margin_min': 7
})

print("=== API响应 ===")
if response.status_code == 200:
    data = response.json()
    print(f"成功: {data.get('success')}")
    print(f"消息: {data.get('message')}")
    items = data.get('data', {}).get('items', [])
    
    # 检查所有返回的股票的毛利率
    print(f"\n返回的{len(items)}条记录的毛利率范围:")
    margins = [item['gross_margin'] for item in items if item['gross_margin'] is not None]
    if margins:
        print(f"  最小值: {min(margins):.2f}%")
        print(f"  最大值: {max(margins):.2f}%")
    
    # 检查688456的毛利率
    print("\n688456的毛利率: 7.4561%")
    print(f"是否 >= 7%: {7.4561 >= 7}")
    print(f"是否 <= 8%: {7.4561 <= 8}")

else:
    print(f"HTTP错误: {response.status_code}")
    print(response.text)
