from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 简化查询，不使用LAG函数
sql = """
    SELECT q1.code, sl.name, q1.revenue_yoy
    FROM quarterly_finance q1
    JOIN quarterly_finance q2 ON q1.code = q2.code
    JOIN stock_list sl ON q1.code = sl.code
    WHERE q1.report_date = '20260331'
      AND q2.report_date = '20251231'
      AND sl.status = 'active'
      AND q1.revenue_yoy >= 58
    ORDER BY q1.code DESC
"""

results = db.query_all(sql)
print(f"查询结果数: {len(results)}")

found = any(row['code'] == '688456' for row in results)
print(f"688456是否在结果中: {found}")

# 打印前5个结果
print("\n前5个结果:")
for row in results[:5]:
    print(f"  {row['code']} - {row['name']}: 营收同比={row['revenue_yoy']}")

db.close()
