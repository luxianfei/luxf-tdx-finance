from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 检查688456在两个季度是否都有数据
sql_q1 = "SELECT * FROM quarterly_finance WHERE code = '688456' AND report_date = '20260331'"
sql_q2 = "SELECT * FROM quarterly_finance WHERE code = '688456' AND report_date = '20251231'"

result_q1 = db.query_one(sql_q1)
result_q2 = db.query_one(sql_q2)

print("=== 检查688456的数据存在性 ===")
print(f"2026Q1数据存在: {result_q1 is not None}")
print(f"2025年度数据存在: {result_q2 is not None}")

if result_q1:
    print("\n2026Q1数据:")
    print(f"  营收同比: {result_q1.get('revenue_yoy')}")
    print(f"  毛利率: {result_q1.get('gross_margin')}")
    print(f"  扣非同比: {result_q1.get('kfe_np_yoy')}")

if result_q2:
    print("\n2025年度数据:")
    print(f"  营收同比: {result_q2.get('revenue_yoy')}")
    print(f"  毛利率: {result_q2.get('gross_margin')}")
    print(f"  扣非同比: {result_q2.get('kfe_np_yoy')}")

# 检查stock_list中的状态
sql_stock = "SELECT * FROM stock_list WHERE code = '688456'"
result_stock = db.query_one(sql_stock)
print(f"\nstock_list中状态: {result_stock.get('status') if result_stock else '不存在'}")

db.close()
