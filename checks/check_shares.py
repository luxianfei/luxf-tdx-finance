# 计算期望的总股本
expected_market_cap = 84.5  # 亿元
current_price = 81.5  # 元

# 市值 = 价格 × 总股本(万股) / 10000
# 总股本(万股) = 市值 × 10000 / 价格
expected_total_shares = expected_market_cap * 10000 / current_price
print(f"期望总股本: {expected_total_shares:.2f} 万股")

# 当前数据库中的总股本
current_total_shares = 8877.43
print(f"当前总股本: {current_total_shares} 万股")

# 差异
print(f"差异: {expected_total_shares - current_total_shares:.2f} 万股")

# 检查是否有其他表存储总股本
from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 检查stock_list表是否有总股本字段
result = db.query_all("DESCRIBE stock_list")
print("\n=== stock_list 表字段 ===")
for row in result:
    print(f"{row['Field']}")

# 检查是否有其他表
result = db.query_all("SHOW TABLES")
print("\n=== 所有表 ===")
for row in result:
    print(row)

db.close()
