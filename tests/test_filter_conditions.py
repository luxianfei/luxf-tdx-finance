import requests

BASE_URL = 'http://localhost:9528/api/stocks/filter'

def test_filter_condition(condition_name, params, expected_code='688456'):
    """测试单个筛选条件 - 检查所有页面"""
    try:
        # 先获取总页数
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                total = data.get('data', {}).get('pagination', {}).get('total_items', 0)
                total_pages = data.get('data', {}).get('pagination', {}).get('total_pages', 1)
                limit = data.get('data', {}).get('pagination', {}).get('limit', 20)
                
                found = False
                found_page = -1
                
                # 遍历所有页面查找（最多检查300页，避免过多请求）
                max_pages = min(total_pages + 1, 301)
                for page in range(1, max_pages):  # 检查所有页面
                    page_params = params.copy()
                    page_params['page'] = page
                    response = requests.get(BASE_URL, params=page_params)
                    if response.status_code == 200:
                        page_data = response.json()
                        if page_data.get('success'):
                            items = page_data.get('data', {}).get('items', [])
                            codes = [item['code'] for item in items]
                            if expected_code in codes:
                                found = True
                                found_page = page
                                break
                
                status = "✓" if found else "✗"
                if found:
                    print(f"{status} {condition_name}: 找到(第{found_page}页, 共{total}条)")
                else:
                    print(f"{status} {condition_name}: 未找到(共{total}条)")
                return found, total
            else:
                print(f"✗ {condition_name}: API返回失败 - {data.get('message')}")
                return False, 0
        else:
            print(f"✗ {condition_name}: HTTP错误 {response.status_code}")
            return False, 0
    except Exception as e:
        print(f"✗ {condition_name}: 请求异常 - {e}")
        return False, 0

print("=== 测试688456有研粉材筛选条件 ===")
print("数据库实际数据 (2026Q1):")
print("  毛利率: 7.4561%")
print("  营收同比: 58.9977%")
print("  扣非同比: 211.2449%")
print("  扣非TTM: 6927.63")
print()

# 测试1: 毛利率筛选（2026Q1）
print("【单季度筛选 - 2026Q1】")
# 添加 sort_field=code 和 sort_order=desc 确保688开头的股票出现在前面
test_filter_condition("毛利率 >= 7%", {
    'report_date': '20260331',
    'gross_margin_min': 7,
    'sort_field': 'code',
    'sort_order': 'desc'
})

test_filter_condition("毛利率 <= 8%", {
    'report_date': '20260331',
    'gross_margin_max': 8,
    'sort_field': 'code',
    'sort_order': 'desc'
})

test_filter_condition("毛利率 7-8%", {
    'report_date': '20260331',
    'gross_margin_min': 7,
    'gross_margin_max': 8,
    'sort_field': 'code',
    'sort_order': 'desc'
})

print()

# 测试2: 营收同比筛选
test_filter_condition("营收同比 >= 58%", {
    'report_date': '20260331',
    'revenue_yoy_min': 58,
    'sort_field': 'code',
    'sort_order': 'desc'
})

test_filter_condition("营收同比 <= 60%", {
    'report_date': '20260331',
    'revenue_yoy_max': 60,
    'sort_field': 'code',
    'sort_order': 'desc'
})

test_filter_condition("营收同比 58-60%", {
    'report_date': '20260331',
    'revenue_yoy_min': 58,
    'revenue_yoy_max': 60,
    'sort_field': 'code',
    'sort_order': 'desc'
})

print()

# 测试3: 扣非同比筛选
test_filter_condition("扣非同比 >= 200%", {
    'report_date': '20260331',
    'net_profit_yoy_min': 200,
    'sort_field': 'code',
    'sort_order': 'desc'
})

test_filter_condition("扣非同比 <= 220%", {
    'report_date': '20260331',
    'net_profit_yoy_max': 220,
    'sort_field': 'code',
    'sort_order': 'desc'
})

test_filter_condition("扣非同比 200-220%", {
    'report_date': '20260331',
    'net_profit_yoy_min': 200,
    'net_profit_yoy_max': 220,
    'sort_field': 'code',
    'sort_order': 'desc'
})

print()

# 测试4: 扣非TTM筛选（单位：万元）
test_filter_condition("扣非TTM >= 6900万", {
    'report_date': '20260331',
    'net_profit_ttm_min': 6900,
    'sort_field': 'code',
    'sort_order': 'desc'
})

test_filter_condition("扣非TTM <= 7000万", {
    'report_date': '20260331',
    'net_profit_ttm_max': 7000,
    'sort_field': 'code',
    'sort_order': 'desc'
})

print()
print("【双季度筛选 - 2026Q1 vs 2025年度】")
print("2025年度数据:")
print("  毛利率: 9.0611%")
print("  营收同比: 21.1411%")
print("  扣非同比: 167.8924%")
print()

# 测试5: 双季度筛选 - Q1毛利率条件
test_filter_condition("Q1毛利率 >= 7%", {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'gross_margin_min': 7,
    'sort_field': 'code',
    'sort_order': 'desc'
})

# 测试6: 双季度筛选 - Q2毛利率条件
test_filter_condition("年度毛利率 >= 9%", {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'gross_margin_min2': 9,
    'sort_field': 'code',
    'sort_order': 'desc'
})

# 测试7: 双季度筛选 - Q1营收同比条件
test_filter_condition("Q1营收同比 >= 58%", {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'revenue_yoy_min': 58,
    'sort_field': 'code',
    'sort_order': 'desc'
})

# 测试8: 双季度筛选 - Q2营收同比条件
test_filter_condition("年度营收同比 >= 20%", {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'revenue_yoy_min2': 20,
    'sort_field': 'code',
    'sort_order': 'desc'
})

# 测试9: 双季度筛选 - Q1扣非同比条件
test_filter_condition("Q1扣非同比 >= 200%", {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'net_profit_yoy_min': 200,
    'sort_field': 'code',
    'sort_order': 'desc'
})

# 测试10: 双季度筛选 - Q2扣非同比条件
test_filter_condition("年度扣非同比 >= 160%", {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'net_profit_yoy_min2': 160,
    'sort_field': 'code',
    'sort_order': 'desc'
})

# 测试11: 双季度组合条件
test_filter_condition("Q1毛利率>7% + 年度毛利率>9%", {
    'quarter_type': 'two',
    'report_date': '20260331',
    'report_date2': '20251231',
    'gross_margin_min': 7,
    'gross_margin_min2': 9,
    'sort_field': 'code',
    'sort_order': 'desc'
})

print()
print("=== 测试完成 ===")
