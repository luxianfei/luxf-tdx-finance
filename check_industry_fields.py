from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

db = MySQLClient(MYSQL_CONFIG)

# 获取所有表
tables = db.query_all('SHOW TABLES')

# 检查每个表的字段
tables_with_industry = []
for t in tables:
    table_name = list(t.values())[0]
    columns = db.query_all(f'DESCRIBE {table_name}')
    
    # 检查是否包含行业相关字段
    has_industry = False
    industry_fields = []
    for col in columns:
        field_name = col['Field'].lower()
        if 'industry' in field_name or 'hangye' in field_name or 'hy' in field_name:
            has_industry = True
            industry_fields.append(col['Field'])
    
    if has_industry:
        tables_with_industry.append({
            'table': table_name,
            'fields': industry_fields
        })
        print(f"表 {table_name} 包含行业字段: {', '.join(industry_fields)}")

print(f"\n共找到 {len(tables_with_industry)} 个包含行业字段的表")

db.close()