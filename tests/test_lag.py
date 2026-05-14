from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 测试LAG函数的影响
print("=== 测试LAG函数的影响 ===")

# 查询1: 使用LAG函数的子查询获取Q1数据
sql_q1 = """
    SELECT qf.code, qf.revenue_yoy,
           LAG(qf.revenue_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_revenue
    FROM quarterly_finance qf
    WHERE qf.report_date = '20260331'
"""
results_q1 = db.query_all(sql_q1)
print(f"Q1子查询返回记录数: {len(results_q1)}")

# 检查688456是否在Q1子查询中
found_q1 = any(row['code'] == '688456' for row in results_q1)
print(f"688456在Q1子查询中: {found_q1}")

# 查询2: 使用LAG函数的子查询获取Q2数据
sql_q2 = """
    SELECT qf.code, qf.gross_margin,
           LAG(qf.revenue_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_revenue
    FROM quarterly_finance qf
    WHERE qf.report_date = '20251231'
"""
results_q2 = db.query_all(sql_q2)
print(f"\nQ2子查询返回记录数: {len(results_q2)}")

# 检查688456是否在Q2子查询中
found_q2 = any(row['code'] == '688456' for row in results_q2)
print(f"688456在Q2子查询中: {found_q2}")

# 查询3: 组合查询（带LAG）
sql_combined = """
    SELECT q1.code, sl.name, q1.revenue_yoy
    FROM (
        SELECT qf.code, qf.revenue_yoy,
               LAG(qf.revenue_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_revenue
        FROM quarterly_finance qf
        WHERE qf.report_date = '20260331'
    ) q1
    JOIN (
        SELECT qf.code, qf.gross_margin,
               LAG(qf.revenue_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_revenue
        FROM quarterly_finance qf
        WHERE qf.report_date = '20251231'
    ) q2 ON q1.code = q2.code
    JOIN stock_list sl ON q1.code = sl.code
    WHERE sl.status = 'active'
      AND q1.revenue_yoy >= 58
    ORDER BY q1.code DESC
"""
results_combined = db.query_all(sql_combined)
print(f"\n组合查询返回记录数: {len(results_combined)}")

# 检查688456是否在组合查询中
found_combined = any(row['code'] == '688456' for row in results_combined)
print(f"688456在组合查询中: {found_combined}")

db.close()
