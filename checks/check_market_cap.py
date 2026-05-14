from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 检查stock_list中是否有总股本字段
result = db.query_all("DESCRIBE stock_list")
print("=== stock_list 表结构 ===")
for row in result:
    print(f"{row['Field']}: {row['Type']}")

# 检查688456的总股本和市值
result = db.query_all("SELECT code, name, market_cap, total_shares FROM stock_list WHERE code = '688456'")
print("\n=== 688456 数据 ===")
if result:
    print(f"market_cap: {result[0]['market_cap']}")
    print(f"total_shares: {result[0]['total_shares']}")

db.close()
