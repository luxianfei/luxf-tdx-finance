from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 测试双季度筛选 - 年度毛利率 >= 9%
print("=== 双季度筛选测试 - 年度毛利率 >= 9% ===")
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
        WHERE qf.report_date = %s
    ) q2 ON q1.code = q2.code
    WHERE q2.gross_margin >= %s
    ORDER BY q1.code ASC
    LIMIT 20
"""

results = db.query_all(sql, ['20260331', '20251231', 9])

print(f"记录数(前20条): {len(results)}")

# 检查688456是否在前20条
found = any(row['code'] == '688456' for row in results)
print(f"688456是否在前20条: {found}")

# 检查688456的具体数据
sql_check = """
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
        WHERE qf.report_date = %s
    ) q2 ON q1.code = q2.code
    WHERE q1.code = %s
"""
result = db.query_one(sql_check, ['20260331', '20251231', '688456'])

if result:
    print(f"\n688456的双季度数据:")
    print(f"  Q1毛利率: {result['q1_gross_margin']}%")
    print(f"  年度毛利率: {result['q2_gross_margin']}%")
    print(f"  年度毛利率 >= 9%: {result['q2_gross_margin'] >= 9}")

# 检查总数
sql_count = """
    SELECT COUNT(*) as cnt
    FROM (
        SELECT qf.code
        FROM quarterly_finance qf
        JOIN stock_list sl ON qf.code = sl.code
        WHERE qf.report_date = %s AND sl.status = 'active'
    ) q1
    JOIN (
        SELECT qf.code, qf.gross_margin
        FROM quarterly_finance qf
        WHERE qf.report_date = %s
    ) q2 ON q1.code = q2.code
    WHERE q2.gross_margin >= %s
"""
result = db.query_one(sql_count, ['20260331', '20251231', 9])
if result:
    total = result['cnt']
    print(f"\n总记录数: {total}")

    # 检查688456的位置
    sql_pos = """
        SELECT COUNT(*) as cnt
        FROM (
            SELECT qf.code
            FROM quarterly_finance qf
            JOIN stock_list sl ON qf.code = sl.code
            WHERE qf.report_date = %s AND sl.status = 'active'
        ) q1
        JOIN (
            SELECT qf.code, qf.gross_margin
            FROM quarterly_finance qf
            WHERE qf.report_date = %s
        ) q2 ON q1.code = q2.code
        WHERE q2.gross_margin >= %s AND q1.code < %s
    """
    pos_result = db.query_one(sql_pos, ['20260331', '20251231', 9, '688456'])
    if pos_result:
        position = pos_result['cnt'] + 1
        page = (position - 1) // 20 + 1
        print(f"688456的位置: 第{position}条，第{page}页")

db.close()
