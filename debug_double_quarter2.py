from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 测试双季度筛选的各种条件
print("=== 测试双季度筛选条件 ===")

# 测试1: 年度毛利率 >= 9%
print("\n【测试1】年度毛利率 >= 9%")
sql = """
    SELECT q1.code, q1.name, q1.gross_margin as q1_gross_margin, q2.gross_margin as q2_gross_margin
    FROM (
        SELECT qf.code, sl.name, qf.gross_margin
        FROM quarterly_finance qf
        JOIN stock_list sl ON qf.code = sl.code
        WHERE qf.report_date = %s AND sl.status = 'active'
    ) q1
    JOIN (
        SELECT qf.code, qf.gross_margin
        FROM quarterly_finance qf
        WHERE qf.report_date = %s AND qf.gross_margin >= %s
    ) q2 ON q1.code = q2.code
    WHERE q1.code = %s
"""
result = db.query_one(sql, ['20260331', '20251231', 9, '688456'])
if result:
    print(f"✓ 找到688456: Q1毛利率={result['q1_gross_margin']}%, 年度毛利率={result['q2_gross_margin']}%")
else:
    print("✗ 未找到688456")

# 测试2: Q1营收同比 >= 58%
print("\n【测试2】Q1营收同比 >= 58%")
sql = """
    SELECT q1.code, q1.name, q1.revenue_yoy as q1_revenue_yoy, q2.revenue_yoy as q2_revenue_yoy
    FROM (
        SELECT qf.code, sl.name, qf.revenue_yoy
        FROM quarterly_finance qf
        JOIN stock_list sl ON qf.code = sl.code
        WHERE qf.report_date = %s AND sl.status = 'active' AND qf.revenue_yoy >= %s
    ) q1
    JOIN (
        SELECT qf.code, qf.revenue_yoy
        FROM quarterly_finance qf
        WHERE qf.report_date = %s
    ) q2 ON q1.code = q2.code
    WHERE q1.code = %s
"""
result = db.query_one(sql, ['20260331', 58, '20251231', '688456'])
if result:
    print(f"✓ 找到688456: Q1营收同比={result['q1_revenue_yoy']}%, 年度营收同比={result['q2_revenue_yoy']}%")
else:
    print("✗ 未找到688456")

# 测试3: Q1扣非同比 >= 200%
print("\n【测试3】Q1扣非同比 >= 200%")
sql = """
    SELECT q1.code, q1.name, q1.kfe_np_yoy as q1_kfe_np_yoy, q2.kfe_np_yoy as q2_kfe_np_yoy
    FROM (
        SELECT qf.code, sl.name, qf.kfe_np_yoy
        FROM quarterly_finance qf
        JOIN stock_list sl ON qf.code = sl.code
        WHERE qf.report_date = %s AND sl.status = 'active' AND qf.kfe_np_yoy >= %s
    ) q1
    JOIN (
        SELECT qf.code, qf.kfe_np_yoy
        FROM quarterly_finance qf
        WHERE qf.report_date = %s
    ) q2 ON q1.code = q2.code
    WHERE q1.code = %s
"""
result = db.query_one(sql, ['20260331', 200, '20251231', '688456'])
if result:
    print(f"✓ 找到688456: Q1扣非同比={result['q1_kfe_np_yoy']}%, 年度扣非同比={result['q2_kfe_np_yoy']}%")
else:
    print("✗ 未找到688456")

# 测试4: Q1毛利率>7% + 年度毛利率>9%
print("\n【测试4】Q1毛利率>7% + 年度毛利率>9%")
sql = """
    SELECT q1.code, q1.name, q1.gross_margin as q1_gross_margin, q2.gross_margin as q2_gross_margin
    FROM (
        SELECT qf.code, sl.name, qf.gross_margin
        FROM quarterly_finance qf
        JOIN stock_list sl ON qf.code = sl.code
        WHERE qf.report_date = %s AND sl.status = 'active' AND qf.gross_margin >= %s
    ) q1
    JOIN (
        SELECT qf.code, qf.gross_margin
        FROM quarterly_finance qf
        WHERE qf.report_date = %s AND qf.gross_margin >= %s
    ) q2 ON q1.code = q2.code
    WHERE q1.code = %s
"""
result = db.query_one(sql, ['20260331', 7, '20251231', 9, '688456'])
if result:
    print(f"✓ 找到688456: Q1毛利率={result['q1_gross_margin']}%, 年度毛利率={result['q2_gross_margin']}%")
else:
    print("✗ 未找到688456")

db.close()
