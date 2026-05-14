from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 检查market_snapshot表结构
result = db.query_all("DESCRIBE market_snapshot")
print("=== market_snapshot 表结构 ===")
for row in result:
    print(f"{row['Field']}: {row['Type']}")

# 检查688456的市场快照和stock_list数据
result = db.query_all("SELECT * FROM market_snapshot WHERE code = '688456' ORDER BY snapshot_time DESC LIMIT 1")
print("\n=== 688456 市场快照 ===")
if result:
    for key, value in result[0].items():
        print(f"  {key}: {value}")

result = db.query_all("SELECT code, name, market_cap FROM stock_list WHERE code = '688456'")
print("\n=== 688456 stock_list ===")
if result:
    print(f"market_cap: {result[0]['market_cap']}")

db.close()
