from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

db = MySQLClient(MYSQL_CONFIG)

# 模拟API的查询方式
print('=== 测试API查询方式 ===')

# 参数
ps_min = 1.0
ps_max = 100.0
page = 1
limit = 5
offset = (page - 1) * limit

# 构建SQL（与API相同）
sql = """
    SELECT 
        sl.code, 
        sl.name, 
        sl.industry,
        smd.current_price,
        smd.market_cap,
        smd.pe_ttm,
        qf.revenue_quarterly_w,
        qf.revenue_yoy,
        CASE 
            WHEN qf.revenue_quarterly_w IS NULL OR qf.revenue_quarterly_w = 0 THEN NULL
            ELSE (smd.market_cap / 100000000) / qf.revenue_quarterly_w * 4
        END AS ps_ratio,
        qf.report_date
    FROM stock_list sl
    LEFT JOIN stock_market_data smd ON sl.code = smd.code
    LEFT JOIN (
        SELECT code, revenue_quarterly_w, revenue_yoy, report_date
        FROM quarterly_finance
        WHERE report_date = (
            SELECT MAX(report_date) FROM quarterly_finance q2 WHERE q2.code = quarterly_finance.code
        )
    ) qf ON sl.code = qf.code
    WHERE sl.status = 'active'
        AND smd.market_cap IS NOT NULL
        AND smd.market_cap > 0
        AND qf.revenue_quarterly_w IS NOT NULL
        AND qf.revenue_quarterly_w > 0
        AND ((smd.market_cap / 100000000) / qf.revenue_quarterly_w * 4) >= %s
        AND ((smd.market_cap / 100000000) / qf.revenue_quarterly_w * 4) <= %s
    ORDER BY ps_ratio ASC
    LIMIT %s OFFSET %s
"""

params = [ps_min, ps_max, limit, offset]

print(f"SQL: {sql}")
print(f"参数: {params}")

try:
    results = db.query_all(sql, params)
    print(f"\n查询结果数: {len(results)}")
    
    if results:
        # 获取盈利预测数据
        stock_codes = [row['code'] for row in results if row['code']]
        print(f"\n股票代码列表: {stock_codes}")
        
        # 查询盈利预测
        if stock_codes:
            placeholders = ",".join(["%s"] * len(stock_codes))
            forecast_sql = f"""
                SELECT code, year, revenue 
                FROM profit_forecast 
                WHERE code IN ({placeholders}) AND forecast_type = 'forecast'
                ORDER BY code, year ASC
            """
            forecasts = db.query_all(forecast_sql, tuple(stock_codes))
            print(f"\n盈利预测数据: {len(forecasts)}条")
            
            # 处理结果
            items = []
            for row in results:
                code = row['code']
                
                # 计算预测PS倍数
                ps_forecasts = []
                market_cap = float(row['market_cap']) if row['market_cap'] else 0
                print(f"\n处理股票: {code} 市值: {market_cap}")
                
                # 查找该股票的预测数据
                stock_forecasts = [f for f in forecasts if f['code'] == code]
                print(f"  预测数据: {stock_forecasts}")
                
                for f in stock_forecasts:
                    print(f"  年: {f['year']} 营收: {f['revenue']}")
                    revenue = float(f['revenue']) / 100 if f['revenue'] else None
                    if revenue and revenue > 0 and market_cap > 0:
                        ps_val = (market_cap / 100000000) / revenue
                        ps_forecasts.append(f"{f['year']}: {ps_val:.2f}x")
                
                print(f"  PS预测: {ps_forecasts}")
                
                items.append({
                    'code': code,
                    'name': row['name'],
                    'industry': row['industry'],
                    'current_price': float(row['current_price']) if row['current_price'] else None,
                    'market_cap': float(row['market_cap']) if row['market_cap'] else None,
                    'pe': float(row['pe_ttm']) if row['pe_ttm'] else None,
                    'revenue_growth': round(float(row['revenue_yoy']), 2) if row['revenue_yoy'] else None,
                    'ps_ratio': round(float(row['ps_ratio']), 2) if row['ps_ratio'] else None,
                    'ps_forecast': "; ".join(ps_forecasts),
                    'report_count': 0,
                    'best_ps': min([float(p.split(':')[1].strip().replace('x', '')) for p in ps_forecasts]) if ps_forecasts else None
                })
            
            print(f"\n最终结果数: {len(items)}")
            
            # 计算统计信息
            if items:
                avg_ps = sum(item['ps_ratio'] for item in items if item['ps_ratio']) / len([item for item in items if item['ps_ratio']])
                print(f"平均PS: {avg_ps}")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()

db.close()