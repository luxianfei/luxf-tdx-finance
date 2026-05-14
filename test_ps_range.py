from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

db = MySQLClient(MYSQL_CONFIG)

# 逐步测试完整查询
print('=== 测试完整查询（移除PS筛选） ===')

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
            ELSE smd.market_cap / (qf.revenue_quarterly_w / 10000) * 4
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
    ORDER BY ps_ratio ASC
    LIMIT 5
"""

result = db.query_all(sql)
print(f"查询结果数（无PS筛选）: {len(result)}")
if result:
    for r in result[:3]:
        ps_ratio = r['ps_ratio']
        print(f"{r['code']} {r['name']} 市值:{r['market_cap']} 营收:{r['revenue_quarterly_w']} PS:{ps_ratio}")

print('\n=== 检查PS值范围 ===')
sql2 = """
    SELECT 
        MIN(smd.market_cap / (qf.revenue_quarterly_w / 10000) * 4) as min_ps,
        MAX(smd.market_cap / (qf.revenue_quarterly_w / 10000) * 4) as max_ps,
        AVG(smd.market_cap / (qf.revenue_quarterly_w / 10000) * 4) as avg_ps
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
"""

result2 = db.query_all(sql2)
if result2:
    print(f"PS最小值: {result2[0]['min_ps']}")
    print(f"PS最大值: {result2[0]['max_ps']}")
    print(f"PS平均值: {result2[0]['avg_ps']}")

db.close()