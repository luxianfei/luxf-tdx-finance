from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 模拟API的双季度筛选逻辑
report_date = '20260331'
report_date2 = '20251231'
gross_margin_min2 = 9

# 第一步：获取第一个季度的数据和环比值
q1_sql = """
    SELECT qf.code, 
           qf.gross_margin, qf.revenue_yoy, qf.kfe_np_yoy,
           qf.kfe_np_ttm_w, qf.revenue_quarterly_w, qf.net_profit_attr_w, qf.eps_basic, qf.roe_diluted,
           qf.kfe_np_quarterly_w,
           LAG(qf.revenue_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_revenue,
           LAG(qf.kfe_np_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_kfe_np
    FROM quarterly_finance qf
    WHERE qf.report_date = %s
"""

# 第二步：获取第二个季度的数据
q2_sql = """
    SELECT qf.code, 
           qf.gross_margin, qf.revenue_yoy, qf.kfe_np_yoy,
           qf.kfe_np_ttm_w, qf.revenue_quarterly_w, qf.net_profit_attr_w, qf.eps_basic, qf.roe_diluted,
           qf.kfe_np_quarterly_w,
           LAG(qf.revenue_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_revenue,
           LAG(qf.kfe_np_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_kfe_np
    FROM quarterly_finance qf
    WHERE qf.report_date = %s
"""

# 构建主查询
sql = f"""
    SELECT q1.code, sl.name, 
           q1.gross_margin, q1.revenue_yoy, q1.kfe_np_yoy,
           q1.kfe_np_ttm_w, q1.revenue_quarterly_w, q1.net_profit_attr_w, q1.eps_basic, q1.roe_diluted,
           %s as report_date,
           q2.gross_margin as q2_gross_margin,  -- 添加Q2的毛利率用于验证
           -- 计算营收环比
           CASE WHEN q1.prev_revenue IS NULL OR q1.prev_revenue = 0 THEN NULL 
                ELSE (q1.revenue_quarterly_w - q1.prev_revenue) / q1.prev_revenue * 100 END AS revenue_qoq,
           -- 计算扣非环比
           CASE WHEN q1.prev_kfe_np IS NULL OR q1.prev_kfe_np = 0 THEN NULL 
                ELSE (q1.kfe_np_quarterly_w - q1.prev_kfe_np) / q1.prev_kfe_np * 100 END AS net_profit_qoq
    FROM ({q1_sql}) q1
    JOIN ({q2_sql}) q2 ON q1.code = q2.code
    JOIN stock_list sl ON q1.code = sl.code
    WHERE sl.status = 'active'
      AND q2.gross_margin >= %s
    ORDER BY q1.code ASC
    LIMIT 20
"""

params = [report_date, report_date2, report_date, gross_margin_min2]

results = db.query_all(sql, params)

print("=== 模拟API双季度筛选 ===")
print(f"SQL参数: {params}")
print(f"返回记录数: {len(results)}")

# 检查688456是否在结果中
found = any(row['code'] == '688456' for row in results)
print(f"688456是否在前20条: {found}")

# 如果没找到，检查Q2的数据
if not found:
    print("\n检查Q2数据:")
    sql_q2 = "SELECT code, gross_margin FROM quarterly_finance WHERE report_date = %s AND code = %s"
    result = db.query_one(sql_q2, [report_date2, '688456'])
    if result:
        print(f"Q2数据存在: code={result['code']}, gross_margin={result['gross_margin']}")
        print(f"gross_margin >= 9: {result['gross_margin'] >= 9}")

db.close()
