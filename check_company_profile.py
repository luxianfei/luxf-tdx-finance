from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

db = MySQLClient(MYSQL_CONFIG)

# 查看company_profile表结构
columns = db.query_all('DESCRIBE company_profile')
print('company_profile表结构:')
for col in columns:
    print(f"  {col['Field']}: {col['Type']}")

db.close()