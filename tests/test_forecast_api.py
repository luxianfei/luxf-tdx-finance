import requests

# 测试盈利预测API
r = requests.get('http://localhost:9528/api/stock/688456/f10/forecast')
result = r.json()
print(f"API响应:")
print(f"success: {result.get('success')}")
print(f"data: {result.get('data')}")
