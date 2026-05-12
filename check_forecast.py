from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 检查profit_forecast表中是否有688456的数据
result = db.query_all("SELECT * FROM profit_forecast WHERE code = '688456' ORDER BY year DESC")
print("=== profit_forecast 表中688456的数据 ===")
if result:
    print(f"共 {len(result)} 条记录")
    for row in result:
        print(f"\n年份: {row['year']}, 季度: {row['quarter']}")
        print(f"每股收益: {row['eps']}")
        print(f"营业收入: {row['revenue']}")
        print(f"净利润: {row['net_profit']}")
        print(f"ROE: {row['roe']}")
        print(f"市盈率: {row['pe']}")
        print(f"每股净资产: {row['book_value_ps']}")
else:
    print("没有找到数据")

db.close()
