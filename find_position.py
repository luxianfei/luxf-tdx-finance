from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

report_date = '20260331'
report_date2 = '20251231'
gross_margin_min2 = 9

# 检查688456的位置
sql_pos = """
    SELECT COUNT(*) as cnt
    FROM (
        SELECT qf.code, 
               qf.gross_margin, qf.revenue_yoy, qf.kfe_np_yoy,
               qf.kfe_np_ttm_w, qf.revenue_quarterly_w, qf.net_profit_attr_w, qf.eps_basic, qf.roe_diluted,
               qf.kfe_np_quarterly_w,
               LAG(qf.revenue_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_revenue,
               LAG(qf.kfe_np_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_kfe_np
        FROM quarterly_finance qf
        WHERE qf.report_date = %s
    ) q1
    JOIN (
        SELECT qf.code, 
               qf.gross_margin, qf.revenue_yoy, qf.kfe_np_yoy,
               qf.kfe_np_ttm_w, qf.revenue_quarterly_w, qf.net_profit_attr_w, qf.eps_basic, qf.roe_diluted,
               qf.kfe_np_quarterly_w,
               LAG(qf.revenue_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_revenue,
               LAG(qf.kfe_np_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_kfe_np
        FROM quarterly_finance qf
        WHERE qf.report_date = %s
    ) q2 ON q1.code = q2.code
    JOIN stock_list sl ON q1.code = sl.code
    WHERE sl.status = 'active'
      AND q2.gross_margin >= %s
      AND q1.code < %s
"""

result = db.query_one(sql_pos, [report_date, report_date2, gross_margin_min2, '688456'])

if result:
    position = result['cnt'] + 1
    page = (position - 1) // 20 + 1
    print(f"688456的位置: 第{position}条，第{page}页")

# 检查总记录数
sql_count = """
    SELECT COUNT(*) as cnt
    FROM (
        SELECT qf.code
        FROM quarterly_finance qf
        WHERE qf.report_date = %s
    ) q1
    JOIN (
        SELECT qf.code
        FROM quarterly_finance qf
        WHERE qf.report_date = %s AND qf.gross_margin >= %s
    ) q2 ON q1.code = q2.code
    JOIN stock_list sl ON q1.code = sl.code
    WHERE sl.status = 'active'
"""

result = db.query_one(sql_count, [report_date, report_date2, gross_margin_min2])
if result:
    print(f"总记录数: {result['cnt']}")

db.close()
