from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 测试SQL查询 - 不排序，只筛选
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
"""

results = db.query_all(sql, ['20260331', 7])

print("=== SQL查询结果 ===")
print(f"记录数: {len(results)}")

# 检查688456是否在结果中
found = None
for row in results:
    if row['code'] == '688456':
        found = row
        break

if found:
    print(f"\n✓ 找到688456:")
    print(f"  code: {found['code']}")
    print(f"  name: {found['name']}")
    print(f"  毛利率: {found['gross_margin']}%")
else:
    print(f"\n✗ 688456不在结果中")

db.close()
