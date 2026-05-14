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
"""

params = []

# 添加PS倍数筛选
if ps_min is not None:
    sql += " AND (smd.market_cap / (qf.revenue_quarterly_w / 10000) * 4) >= %s"
    params.append(ps_min)
if ps_max is not None:
    sql += " AND (smd.market_cap / (qf.revenue_quarterly_w / 10000) * 4) <= %s"
    params.append(ps_max)

# 添加排序
sql += " ORDER BY ps_ratio ASC"

# 添加分页
sql += " LIMIT %s OFFSET %s"
params.extend([limit, offset])

print(f"SQL: {sql}")
print(f"参数: {params}")

try:
    result = db.query_all(sql, params)
    print(f"\n查询结果数: {len(result)}")
    if result:
        for r in result[:3]:
            print(f"{r['code']} {r['name']} 市值:{r['market_cap']} 营收:{r['revenue_quarterly_w']} PS:{r['ps_ratio']}")
except Exception as e:
    print(f"查询失败: {e}")

db.close()