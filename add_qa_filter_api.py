# -*- coding: utf-8 -*-

# 读取文件
with open('e:/trae_proj/luxf-tdx-finance-v1.0/api_server.py', 'rb') as f:
    content_bytes = f.read()

try:
    content = content_bytes.decode('utf-8')
except:
    content = content_bytes.decode('gbk')

# 要插入的新 API 代码
new_api_code = '''

# ============================================================
# 互动问答筛选API接口
# ============================================================

@app.route('/api/qa/stocks', methods=['GET'])
def get_qa_stocks():
    """
    获取近期有互动问答答复的股票列表
    
    参数:
        range: 时间范围 (today/1day/2day/3day)
        page: 页码，默认1
        limit: 每页条数，默认20
    """
    time_range = request.args.get('range', 'today')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    from datetime import datetime, timedelta
    today = datetime.now().date()
    
    if time_range == 'today':
        start_date = today
    elif time_range == '1day':
        start_date = today - timedelta(days=1)
    elif time_range == '2day':
        start_date = today - timedelta(days=2)
    elif time_range == '3day':
        start_date = today - timedelta(days=3)
    else:
        start_date = today
    
    offset = (page - 1) * limit
    
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        stocks = db_client.get_stocks_with_recent_qa(start_date, limit, offset)
        total = db_client.get_stocks_with_recent_qa_count(start_date)
        total_qa_count = db_client.get_qa_count_by_date_range(start_date)
        
        db_client.close()
        
        total_pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': {
                'stocks': stocks,
                'total': total,
                'total_pages': total_pages,
                'total_qa_count': total_qa_count,
                'current_page': page,
                'limit': limit,
                'range': time_range
            }
        })
    except Exception as e:
        logger.error(f"获取互动问答股票列表失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500


'''

# 查找 PS 筛选 API 的位置并在其前面插入
pattern = r'(# ============================================================\n# PS市销率科技股筛选API接口\n# ============================================================)'
import re
content = re.sub(pattern, new_api_code + r'\1', content)

# 写入文件
with open('e:/trae_proj/luxf-tdx-finance-v1.0/api_server.py', 'wb') as f:
    f.write(content.encode('utf-8'))

print('API 接口添加完成')
