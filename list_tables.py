from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

db = MySQLClient(MYSQL_CONFIG)

# 获取所有表
tables = db.query_all('SHOW TABLES')
print('数据库中的表:')
for t in tables:
    print(f"  - {list(t.values())[0]}")

db.close()