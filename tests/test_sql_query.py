from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 测试SQL查询
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
    ORDER BY qf.gross_margin DESC
    LIMIT 20
"""

results = db.query_all(sql, ['20260331', 7])

print("=== SQL查询结果 ===")
print(f"记录数: {len(results)}")
print("\n股票列表:")
for row in results:
    print(f"  {row['code']} - {row['name']} - 毛利率: {row['gross_margin']}%")

# 检查688456是否在结果中
found = any(row['code'] == '688456' for row in results)
print(f"\n688456是否在结果中: {found}")

db.close()
