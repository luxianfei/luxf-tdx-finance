from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

db = MySQLClient(MYSQL_CONFIG)

tables = ['company_profile', 'stock_list', 'stock_market_data', 'tech_sector_stocks']

for table_name in tables:
    print(f"\n=== {table_name} ===")
    
    # 获取字段结构
    columns = db.query_all(f'DESCRIBE {table_name}')
    industry_col = None
    for col in columns:
        if col['Field'] == 'industry':
            industry_col = col
            break
    
    if industry_col:
        print(f"字段类型: {industry_col['Type']}, 是否可为空: {industry_col['Null']}")
    
    # 获取前5条数据的industry字段
    rows = db.query_all(f'SELECT industry FROM {table_name} WHERE industry IS NOT NULL LIMIT 5')
    print(f"前5条行业数据:")
    for r in rows:
        print(f"  - {repr(r['industry'])}")
    
    # 获取不同的行业值数量
    distinct_count = db.query_one(f'SELECT COUNT(DISTINCT industry) as cnt FROM {table_name} WHERE industry IS NOT NULL')
    print(f"不同行业值数量: {distinct_count['cnt']}")

db.close()