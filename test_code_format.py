from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

db = MySQLClient(MYSQL_CONFIG)

print('=== 检查股票代码格式 ===')

# 获取stock_list中的代码格式
result1 = db.query_all('SELECT code FROM stock_list LIMIT 3')
print('stock_list代码格式:')
for r in result1:
    print(f"  '{r['code']}' (长度:{len(r['code'])})")

# 获取quarterly_finance中的代码格式
result2 = db.query_all('SELECT code FROM quarterly_finance LIMIT 3')
print('\nquarterly_finance代码格式:')
for r in result2:
    print(f"  '{r['code']}' (长度:{len(r['code'])})")

# 获取stock_market_data中的代码格式
result3 = db.query_all('SELECT code FROM stock_market_data LIMIT 3')
print('\nstock_market_data代码格式:')
for r in result3:
    print(f"  '{r['code']}' (长度:{len(r['code'])})")

# 测试不同代码格式之间的匹配
print('\n=== 测试代码匹配 ===')
# 从stock_list取一个代码
stock_list_code = result1[0]['code']
print(f"从stock_list取的代码: '{stock_list_code}'")

# 查询该代码在quarterly_finance中是否存在
result4 = db.query_all('SELECT COUNT(*) as cnt FROM quarterly_finance WHERE code = %s', [stock_list_code])
print(f"在quarterly_finance中找到: {result4[0]['cnt']}条")

# 查询该代码在stock_market_data中是否存在
result5 = db.query_all('SELECT COUNT(*) as cnt FROM stock_market_data WHERE code = %s', [stock_list_code])
print(f"在stock_market_data中找到: {result5[0]['cnt']}条")

# 尝试用trim后的代码查询
trimmed_code = stock_list_code.strip()
print(f"\n去除空格后的代码: '{trimmed_code}'")
result6 = db.query_all('SELECT COUNT(*) as cnt FROM quarterly_finance WHERE code = %s', [trimmed_code])
print(f"去除空格后在quarterly_finance中找到: {result6[0]['cnt']}条")

db.close()