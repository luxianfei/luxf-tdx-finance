from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 检查688456的状态
sql = "SELECT * FROM stock_list WHERE code = %s"
result = db.query_one(sql, ['688456'])

print("=== 688456在stock_list中的信息 ===")
if result:
    print(f"code: {result['code']}")
    print(f"name: {result['name']}")
    print(f"status: {result['status']}")
    print(f"market: {result['market']}")
else:
    print("未找到688456")

# 检查688456在quarterly_finance中的数据
sql = "SELECT * FROM quarterly_finance WHERE code = %s AND report_date = %s"
result = db.query_one(sql, ['688456', '20260331'])

print("\n=== 688456在quarterly_finance中的2026Q1数据 ===")
if result:
    print(f"gross_margin: {result['gross_margin']}")
    print(f"revenue_yoy: {result['revenue_yoy']}")
    print(f"kfe_np_yoy: {result['kfe_np_yoy']}")
    print(f"kfe_np_ttm_w: {result['kfe_np_ttm_w']}")
else:
    print("未找到2026Q1数据")

db.close()
