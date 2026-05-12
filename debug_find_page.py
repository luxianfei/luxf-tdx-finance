import requests

BASE_URL = 'http://localhost:9528/api/stocks/filter'

# 测试特定条件
def find_stock_page(condition_name, params, expected_code='688456'):
    """查找股票所在的页面"""
    try:
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                total = data.get('data', {}).get('pagination', {}).get('total_items', 0)
                total_pages = data.get('data', {}).get('pagination', {}).get('total_pages', 1)
                limit = data.get('data', {}).get('pagination', {}).get('limit', 20)
                
                # 计算理论位置（按代码排序）
                # 688开头的股票在000, 001, 002, 300, 600, 601, 603之后
                # 估算大约在第24-30页左右（每页20条）
                # 为了测试，检查所有页面
                
                for page in range(1, total_pages + 1):
                    page_params = params.copy()
                    page_params['page'] = page
                    response = requests.get(BASE_URL, params=page_params)
                    if response.status_code == 200:
                        page_data = response.json()
                        if page_data.get('success'):
                            items = page_data.get('data', {}).get('items', [])
                            codes = [item['code'] for item in items]
                            if expected_code in codes:
                                return page, total
                return -1, total
            else:
                return -1, 0
        else:
            return -1, 0
    except Exception as e:
        return -1, 0

print("=== 分析筛选条件问题 ===")

# 测试问题条件
test_cases = [
    ("毛利率 >= 7%", {'report_date': '20260331', 'gross_margin_min': 7, 'sort_field': 'code'}),
    ("营收同比 <= 60%", {'report_date': '20260331', 'revenue_yoy_max': 60, 'sort_field': 'code'}),
    ("扣非同比 <= 220%", {'report_date': '20260331', 'net_profit_yoy_max': 220, 'sort_field': 'code'}),
]

for condition_name, params in test_cases:
    page, total = find_stock_page(condition_name, params)
    if page > 0:
        print(f"✓ {condition_name}: 688456在第{page}页 (共{total}条)")
    else:
        print(f"✗ {condition_name}: 未找到688456 (共{total}条)")
