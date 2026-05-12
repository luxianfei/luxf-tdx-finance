from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 查询688456的实际数据
sql = """
    SELECT * FROM quarterly_finance 
    WHERE code = '688456' 
    ORDER BY report_date DESC
"""
results = db.query_all(sql)

print("688456 有研粉材的财务数据:")
for row in results:
    print(f"\n报告期: {row['report_date']}")
    print(f"  毛利率: {row['gross_margin']}%")
    print(f"  营收同比: {row['revenue_yoy']}%")
    print(f"  扣非同比: {row['kfe_np_yoy']}%")
    print(f"  扣非TTM: {row['kfe_np_ttm_w']}")
    print(f"  季度营收: {row['revenue_quarterly_w']}")
    print(f"  季度扣非: {row['kfe_np_quarterly_w']}")

db.close()
