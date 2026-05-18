# -*- coding: utf-8 -*-

# 读取文件
with open('e:/trae_proj/luxf-tdx-finance-v1.0/database/mysql_client.py', 'rb') as f:
    content_bytes = f.read()

try:
    content = content_bytes.decode('utf-8')
except:
    content = content_bytes.decode('gbk')

# 要添加的新方法
new_methods = '''

    def get_stocks_with_recent_qa(self, start_date, limit: int = 20, offset: int = 0) -> List[Dict]:
        """
        获取近期有互动问答答复的股票列表（支持分页）

        Args:
            start_date: 开始日期
            limit: 返回条数
            offset: 偏移量

        Returns:
            List[Dict]: 股票列表，包含代码、名称、最新答复时间、问答数量
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

    def get_stocks_with_recent_qa_count(self, start_date) -> int:
        """
        获取近期有互动问答答复的股票数量

        Args:
            start_date: 开始日期

        Returns:
            int: 股票数量
        """
        sql = """
            SELECT COUNT(DISTINCT code) as count
            FROM stock_qa 
            WHERE DATE(answer_time) >= %s
        """
        result = self.query_one(sql, (start_date,))
        return result["count"] if result else 0

    def get_qa_count_by_date_range(self, start_date) -> int:
        """
        获取指定日期范围内的问答总数

        Args:
            start_date: 开始日期

        Returns:
            int: 问答数量
        """
        sql = "SELECT COUNT(*) FROM stock_qa WHERE DATE(answer_time) >= %s"
        result = self.query_one(sql, (start_date,))
        return result["COUNT(*)"] if result else 0

'''

# 在 get_qa_count 方法后添加新方法
insert_marker = '    def get_qa_count(self, code: str) -> int:\n        """\n        获取股票问答数量\n\n        Args:\n            code: 股票代码\n\n        Returns:\n            int: 问答数量\n        """\n        sql = "SELECT COUNT(*) FROM stock_qa WHERE code = %s"\n        result = self.query_one(sql, (code,))\n        return result["COUNT(*)"] if result else 0'

content = content.replace(insert_marker, insert_marker + new_methods)

# 写入文件
with open('e:/trae_proj/luxf-tdx-finance-v1.0/database/mysql_client.py', 'wb') as f:
    f.write(content.encode('utf-8'))

print('数据库方法添加完成')
