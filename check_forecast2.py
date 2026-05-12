from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 检查表结构
result = db.query_all("DESCRIBE profit_forecast")
print("=== profit_forecast 表结构 ===")
for row in result:
    print(f"{row['Field']}: {row['Type']}")

# 检查数据
result = db.query_all("SELECT * FROM profit_forecast WHERE code = '688456' ORDER BY year DESC")
print("\n=== 688456 盈利预测数据 ===")
if result:
    print(f"共 {len(result)} 条记录")
    for row in result:
        print(f"\n所有字段: {list(row.keys())}")
        print(f"数据值: {row}")

db.close()
