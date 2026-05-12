from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 检查688456的最新市场快照
result = db.query_all("SELECT * FROM market_snapshot WHERE code = '688456' ORDER BY snapshot_time DESC LIMIT 1")
print("=== 688456 市场快照 ===")
if result:
    data = result[0]
    print(f"价格: {data['price']}")
    print(f"涨跌金额: {data['change']}")
    print(f"涨跌幅: {data['change_percent']}%")
    print(f"市值(亿元): {data['market_cap']}")
    print(f"成交量: {data['volume']}")
    print(f"成交额: {data['amount']}万元")
    print(f"最高价: {data['high']}")
    print(f"最低价: {data['low']}")
    print(f"开盘价: {data['open']}")
    print(f"前收盘价: {data['prev_close']}")
    print(f"更新时间: {data['snapshot_time']}")

db.close()
