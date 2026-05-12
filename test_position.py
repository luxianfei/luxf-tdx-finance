from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 测试筛选条件 - 使用代码排序
sql = """
    SELECT qf.code, sl.name, qf.gross_margin
    FROM quarterly_finance qf
    LEFT JOIN quarterly_finance prev 
        ON qf.code = prev.code AND prev.report_date = (
            SELECT MAX(report_date) FROM quarterly_finance 
            WHERE code = qf.code AND report_date < qf.report_date
        )
    JOIN stock_list sl ON qf.code = sl.code
    WHERE sl.status = 'active'
      AND qf.report_date = %s
      AND qf.gross_margin >= %s
      AND qf.gross_margin <= %s
    ORDER BY qf.code ASC
    LIMIT 30
"""

results = db.query_all(sql, ['20260331', 7, 8])

print("=== SQL查询结果（代码升序）===")
print(f"记录数: {len(results)}")
print("\n股票列表:")
for row in results:
    print(f"  {row['code']} - {row['name']} - 毛利率: {row['gross_margin']}%")

# 检查688456是否在结果中
found = any(row['code'] == '688456' for row in results)
print(f"\n688456是否在第一页(30条): {found}")

# 检查688456在第几页
sql_count = """
    SELECT COUNT(*) as cnt
    FROM quarterly_finance qf
    JOIN stock_list sl ON qf.code = sl.code
    WHERE sl.status = 'active'
      AND qf.report_date = %s
      AND qf.gross_margin >= %s
      AND qf.gross_margin <= %s
      AND qf.code < %s
"""
result = db.query_one(sql_count, ['20260331', 7, 8, '688456'])
if result:
    position = result['cnt'] + 1
    page = (position - 1) // 20 + 1
    print(f"688456的位置: 第{position}条，第{page}页")

db.close()
