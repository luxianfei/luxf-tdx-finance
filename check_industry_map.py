import pymysql
from config import MYSQL_CONFIG

conn = pymysql.connect(**MYSQL_CONFIG)
cursor = conn.cursor(pymysql.cursors.DictCursor)

# 查询行业映射表
cursor.execute('SELECT * FROM industry_map ORDER BY code')
industries = cursor.fetchall()

print('当前行业映射表内容:')
for row in industries:
    print(f"{row['code']}: {row['name']}")

conn.close()
