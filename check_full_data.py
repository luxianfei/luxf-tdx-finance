from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 检查688456的完整数据
sql = "SELECT * FROM quarterly_finance WHERE code = '688456' AND report_date = '20260331'"
result = db.query_one(sql)

print("=== 688456 2026Q1完整数据 ===")
if result:
    for key, value in result.items():
        print(f"  {key}: {value}")

db.close()
