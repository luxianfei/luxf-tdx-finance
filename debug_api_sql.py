from config import MYSQL_CONFIG
from database import MySQLClient

db = MySQLClient(MYSQL_CONFIG)

# 模拟API的参数解析
report_date = '20260331'
report_date2 = '20251231'

# 模拟从请求获取的筛选条件
filters_q1 = {'revenue_yoy': {'min': 58, 'max': None}}  # Q1营收同比 >= 58%
filters_q2 = {}

# 构建SQL（完全复制API中的逻辑）
q1_sql = """
    SELECT qf.code, 
           qf.gross_margin, qf.revenue_yoy, qf.kfe_np_yoy,
           qf.kfe_np_ttm_w, qf.revenue_quarterly_w, qf.net_profit_attr_w, qf.eps_basic, qf.roe_diluted,
           qf.kfe_np_quarterly_w,
           LAG(qf.revenue_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_revenue,
           LAG(qf.kfe_np_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_kfe_np
    FROM quarterly_finance qf
    WHERE qf.report_date = %s
"""

q2_sql = """
    SELECT qf.code, 
           qf.gross_margin, qf.revenue_yoy, qf.kfe_np_yoy,
           qf.kfe_np_ttm_w, qf.revenue_quarterly_w, qf.net_profit_attr_w, qf.eps_basic, qf.roe_diluted,
           qf.kfe_np_quarterly_w,
           LAG(qf.revenue_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_revenue,
           LAG(qf.kfe_np_quarterly_w) OVER (PARTITION BY qf.code ORDER BY qf.report_date) AS prev_kfe_np
    FROM quarterly_finance qf
    WHERE qf.report_date = %s
"""

sql = f"""
    SELECT q1.code, sl.name, 
           q1.gross_margin, q1.revenue_yoy, q1.kfe_np_yoy,
           q1.kfe_np_ttm_w, q1.revenue_quarterly_w, q1.net_profit_attr_w, q1.eps_basic, q1.roe_diluted,
           %s as report_date,
           -- 计算营收环比
           CASE WHEN q1.prev_revenue IS NULL OR q1.prev_revenue = 0 THEN NULL 
                ELSE (q1.revenue_quarterly_w - q1.prev_revenue) / q1.prev_revenue * 100 END AS revenue_qoq,
           -- 计算扣非环比
           CASE WHEN q1.prev_kfe_np IS NULL OR q1.prev_kfe_np = 0 THEN NULL 
                ELSE (q1.kfe_np_quarterly_w - q1.prev_kfe_np) / q1.prev_kfe_np * 100 END AS net_profit_qoq
    FROM ({q1_sql}) q1
    JOIN ({q2_sql}) q2 ON q1.code = q2.code
    JOIN stock_list sl ON q1.code = sl.code
    WHERE sl.status = 'active'
"""
params = [report_date, report_date2, report_date]

# 添加Q1筛选条件
for field, range_vals in filters_q1.items():
    db_field = {
        'gross_margin': 'q1.gross_margin',
        'revenue_yoy': 'q1.revenue_yoy',
        'net_profit_yoy': 'q1.kfe_np_yoy',
        'net_profit_ttm': 'q1.kfe_np_ttm_w'
    }.get(field)
    
    if db_field:
        if range_vals['min'] is not None:
            sql += f" AND {db_field} >= %s"
            params.append(range_vals['min'])
        if range_vals['max'] is not None:
            sql += f" AND {db_field} <= %s"
            params.append(range_vals['max'])

# 添加Q2筛选条件
for field, range_vals in filters_q2.items():
    db_field = {
        'gross_margin': 'q2.gross_margin',
        'revenue_yoy': 'q2.revenue_yoy',
        'net_profit_yoy': 'q2.kfe_np_yoy',
        'net_profit_ttm': 'q2.kfe_np_ttm_w'
    }.get(field)
    
    if db_field:
        if range_vals['min'] is not None:
            sql += f" AND {db_field} >= %s"
            params.append(range_vals['min'])
        if range_vals['max'] is not None:
            sql += f" AND {db_field} <= %s"
            params.append(range_vals['max'])

# 添加排序
sql += " ORDER BY q1.code DESC"

print("=== 模拟API生成的SQL ===")
print(f"SQL: {sql}")
print(f"参数: {params}")

# 执行查询
results = db.query_all(sql, params)
print(f"\n返回记录数: {len(results)}")

# 检查688456是否在结果中
found = any(row['code'] == '688456' for row in results)
print(f"688456是否在结果中: {found}")

# 如果找到了，打印其数据
if found:
    for row in results:
        if row['code'] == '688456':
            print(f"\n688456的数据:")
            print(f"  毛利率: {row['gross_margin']}")
            print(f"  营收同比: {row['revenue_yoy']}")
            print(f"  扣非同比: {row['kfe_np_yoy']}")
            break

db.close()
