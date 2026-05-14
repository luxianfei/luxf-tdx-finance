from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

db = MySQLClient(MYSQL_CONFIG)

# 测试简单查询
print('=== 测试1: 检查有市值的股票 ===')
result = db.query_all('SELECT sl.code, sl.name, smd.market_cap FROM stock_list sl LEFT JOIN stock_market_data smd ON sl.code = smd.code WHERE sl.status = %s AND smd.market_cap > 0 LIMIT 3', ['active'])
print(f'结果数: {len(result)}')
for r in result:
    print(f'{r["code"]} {r["name"]} 市值:{r["market_cap"]}')

print('\n=== 测试2: 检查有营收的股票 ===')
result = db.query_all('SELECT sl.code, sl.name, qf.revenue_quarterly_w FROM stock_list sl LEFT JOIN quarterly_finance qf ON sl.code = qf.code WHERE sl.status = %s AND qf.revenue_quarterly_w > 0 LIMIT 3', ['active'])
print(f'结果数: {len(result)}')
for r in result:
    print(f'{r["code"]} {r["name"]} 营收:{r["revenue_quarterly_w"]}')

print('\n=== 测试3: 检查同时有市值和营收的股票 ===')
result = db.query_all('SELECT sl.code, sl.name, smd.market_cap, qf.revenue_quarterly_w FROM stock_list sl LEFT JOIN stock_market_data smd ON sl.code = smd.code LEFT JOIN quarterly_finance qf ON sl.code = qf.code WHERE sl.status = %s AND smd.market_cap > 0 AND qf.revenue_quarterly_w > 0 LIMIT 3', ['active'])
print(f'结果数: {len(result)}')
for r in result:
    print(f'{r["code"]} {r["name"]} 市值:{r["market_cap"]} 营收:{r["revenue_quarterly_w"]}')

print('\n=== 测试4: 使用子查询获取最新季度数据 ===')
sql = """
SELECT 
    sl.code, 
    sl.name, 
    smd.market_cap,
    qf.revenue_quarterly_w
FROM stock_list sl
LEFT JOIN stock_market_data smd ON sl.code = smd.code
LEFT JOIN (
    SELECT code, revenue_quarterly_w
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
LIMIT 3
"""
result = db.query_all(sql)
print(f'结果数: {len(result)}')
for r in result:
    print(f'{r["code"]} {r["name"]} 市值:{r["market_cap"]} 营收:{r["revenue_quarterly_w"]}')

db.close()