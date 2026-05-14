from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

db = MySQLClient(MYSQL_CONFIG)

# 测试子查询
print('=== 测试子查询获取最新季度数据 ===')

# 先测试子查询是否能获取数据
sql = """
    SELECT code, revenue_quarterly_w, revenue_yoy, report_date
    FROM quarterly_finance
    WHERE report_date = (
        SELECT MAX(report_date) FROM quarterly_finance q2 WHERE q2.code = quarterly_finance.code
    )
    LIMIT 5
"""
result = db.query_all(sql)
print(f"子查询结果数: {len(result)}")
if result:
    for r in result[:3]:
        print(f"{r['code']} 营收:{r['revenue_quarterly_w']} 增速:{r['revenue_yoy']} 日期:{r['report_date']}")

print('\n=== 测试主查询但不使用子查询 ===')
sql2 = """
    SELECT 
        sl.code, 
        sl.name, 
        smd.market_cap,
        qf.revenue_quarterly_w,
        smd.market_cap / (qf.revenue_quarterly_w / 10000) * 4 AS ps_ratio
    FROM stock_list sl
    LEFT JOIN stock_market_data smd ON sl.code = smd.code
    LEFT JOIN quarterly_finance qf ON sl.code = qf.code
    WHERE sl.status = 'active'
        AND smd.market_cap > 0
        AND qf.revenue_quarterly_w > 0
    LIMIT 5
"""
result2 = db.query_all(sql2)
print(f"简单查询结果数: {len(result2)}")
if result2:
    for r in result2[:3]:
        print(f"{r['code']} {r['name']} 市值:{r['market_cap']} 营收:{r['revenue_quarterly_w']} PS:{r['ps_ratio']}")

print('\n=== 测试子查询中的股票是否在stock_market_data中 ===')
sql3 = """
    SELECT qf.code, qf.revenue_quarterly_w, smd.market_cap
    FROM (
        SELECT code, revenue_quarterly_w
        FROM quarterly_finance
        WHERE report_date = (
            SELECT MAX(report_date) FROM quarterly_finance q2 WHERE q2.code = quarterly_finance.code
        )
    ) qf
    LEFT JOIN stock_market_data smd ON qf.code = smd.code
    WHERE smd.market_cap IS NOT NULL
    LIMIT 5
"""
result3 = db.query_all(sql3)
print(f"子查询+市值结果数: {len(result3)}")
if result3:
    for r in result3[:3]:
        print(f"{r['code']} 营收:{r['revenue_quarterly_w']} 市值:{r['market_cap']}")

db.close()