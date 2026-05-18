# -*- coding: utf-8 -*-

# 读取文件
with open('e:/trae_proj/luxf-tdx-finance-v1.0/database/mysql_client.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# 要添加的新方法
new_methods = '''

    def get_stocks_with_recent_qa(self, start_date, limit: int = 20, offset: int = 0):
        """
        获取近期有互动问答答复的股票列表（支持分页）
        """
        sql = """
            SELECT 
                sl.code, 
                sl.name, 
                MAX(sq.answer_time) as latest_answer_time,
                COUNT(sq.id) as qa_count
            FROM stock_qa sq
            JOIN stock_list sl ON sq.code = sl.code
            WHERE DATE(sq.answer_time) >= %s
            GROUP BY sq.code, sl.name
            ORDER BY MAX(sq.answer_time) DESC
            LIMIT %s OFFSET %s
        """
        result = self.query_all(sql, (start_date, limit, offset))
        return result

    def get_stocks_with_recent_qa_count(self, start_date):
        """
        获取近期有互动问答答复的股票数量
        """
        sql = """
            SELECT COUNT(DISTINCT code) as count
            FROM stock_qa 
            WHERE DATE(answer_time) >= %s
        """
        result = self.query_one(sql, (start_date,))
        return result["count"] if result else 0

    def get_qa_count_by_date_range(self, start_date):
        """
        获取指定日期范围内的问答总数
        """
        sql = "SELECT COUNT(*) FROM stock_qa WHERE DATE(answer_time) >= %s"
        result = self.query_one(sql, (start_date,))
        return result["COUNT(*)"] if result else 0

'''

# 在 get_qa_count 方法后添加新方法
insert_marker = '    def get_qa_count(self, code: str) -> int:\n        """\n        获取股票问答数量\n\n        Args:\n            code: 股票代码\n\n        Returns:\n            int: 问答数量\n        """\n        sql = "SELECT COUNT(*) FROM stock_qa WHERE code = %s"\n        result = self.query_one(sql, (code,))\n        return result["COUNT(*)"] if result else 0'

if insert_marker in content:
    content = content.replace(insert_marker, insert_marker + new_methods)
else:
    print("未找到插入位置")
    exit(1)

# 写入文件
with open('e:/trae_proj/luxf-tdx-finance-v1.0/database/mysql_client.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('数据库方法添加完成')
