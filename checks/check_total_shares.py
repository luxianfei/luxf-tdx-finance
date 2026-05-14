from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 检查quarterly_finance表是否有总股本字段
result = db.query_all("DESCRIBE quarterly_finance")
print("=== quarterly_finance 表结构 ===")
for row in result:
    print(f"{row['Field']}: {row['Type']}")

# 检查688456的总股本数据
result = db.query_all("SELECT total_shares FROM quarterly_finance WHERE code = '688456' ORDER BY report_date DESC LIMIT 1")
print("\n=== 688456 总股本 ===")
if result:
    print(f"total_shares: {result[0]['total_shares']}")

db.close()
