"""
科技股板块数据模型
用于存储从外部数据源获取的科技股板块信息
"""
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

class TechStockSector:
    def __init__(self):
        self.db = MySQLClient(MYSQL_CONFIG)
        self._create_table()
    
    def _create_table(self):
        """创建科技股板块表"""
        sql = """
        CREATE TABLE IF NOT EXISTS tech_sector_stocks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(10) NOT NULL COMMENT '股票代码',
            name VARCHAR(50) COMMENT '股票名称',
            sector VARCHAR(50) COMMENT '科技板块名称',
            sub_sector VARCHAR(50) COMMENT '细分板块',
            market VARCHAR(20) COMMENT '市场类型: 主板/创业板/科创板',
            industry VARCHAR(100) COMMENT '行业分类',
            pe FLOAT COMMENT '市盈率',
            pb FLOAT COMMENT '市净率',
            ps FLOAT COMMENT '市销率',
            revenue_growth FLOAT COMMENT '营收增长率',
            profit_growth FLOAT COMMENT '净利润增长率',
            market_cap BIGINT COMMENT '市值(元)',
            update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY uk_code_sector (code, sector),
            INDEX idx_code (code),
            INDEX idx_sector (sector)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='科技股板块表';
        """
        self.db.execute(sql)
    
    def insert_stock(self, code, name, sector, sub_sector=None, market=None, industry=None, 
                     pe=None, pb=None, ps=None, revenue_growth=None, profit_growth=None, market_cap=None):
        """插入单只科技股"""
        sql = """
        INSERT INTO tech_sector_stocks (code, name, sector, sub_sector, market, industry, 
                                        pe, pb, ps, revenue_growth, profit_growth, market_cap)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            name=VALUES(name), sub_sector=VALUES(sub_sector), market=VALUES(market), 
            industry=VALUES(industry), pe=VALUES(pe), pb=VALUES(pb), ps=VALUES(ps),
            revenue_growth=VALUES(revenue_growth), profit_growth=VALUES(profit_growth),
            market_cap=VALUES(market_cap), update_time=CURRENT_TIMESTAMP
        """
        params = (code, name, sector, sub_sector, market, industry, pe, pb, ps, revenue_growth, profit_growth, market_cap)
        self.db.execute(sql, params)
    
    def insert_batch(self, stocks):
        """批量插入科技股"""
        sql = """
        INSERT INTO tech_sector_stocks (code, name, sector, sub_sector, market, industry, 
                                        pe, pb, ps, revenue_growth, profit_growth, market_cap)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            name=VALUES(name), sub_sector=VALUES(sub_sector), market=VALUES(market), 
            industry=VALUES(industry), pe=VALUES(pe), pb=VALUES(pb), ps=VALUES(ps),
            revenue_growth=VALUES(revenue_growth), profit_growth=VALUES(profit_growth),
            market_cap=VALUES(market_cap), update_time=CURRENT_TIMESTAMP
        """
        self.db.executemany(sql, stocks)
        self.db.commit()
    
    def get_tech_codes(self):
        """获取所有科技股代码"""
        sql = "SELECT DISTINCT code FROM tech_sector_stocks"
        results = self.db.query_all(sql)
        return [row['code'] for row in results]
    
    def get_stocks_by_sector(self, sector):
        """按板块获取科技股"""
        sql = "SELECT * FROM tech_sector_stocks WHERE sector = %s"
        return self.db.query_all(sql, (sector,))
    
    def get_all_sectors(self):
        """获取所有科技板块"""
        sql = "SELECT DISTINCT sector FROM tech_sector_stocks ORDER BY sector"
        results = self.db.query_all(sql)
        return [row['sector'] for row in results]
    
    def clear_all(self):
        """清空所有数据"""
        sql = "TRUNCATE TABLE tech_sector_stocks"
        self.db.execute(sql)
        self.db.commit()
    
    def get_count(self):
        """获取科技股总数"""
        sql = "SELECT COUNT(DISTINCT code) as count FROM tech_sector_stocks"
        result = self.db.query_one(sql)
        return result['count'] if result else 0
    
    def close(self):
        """关闭数据库连接"""
        self.db.close()

# 预定义的科技板块列表
TECH_SECTORS = [
    '半导体', '芯片', '人工智能', '云计算', '大数据', '物联网',
    '5G', '通信设备', '软件服务', '互联网', '新能源', '光伏',
    '锂电池', '新能源车', '智能汽车', '工业机器人', '智能制造',
    '生物医药', '医疗器械', '创新药', '量子科技', '区块链'
]

if __name__ == '__main__':
    # 创建表
    ts = TechStockSector()
    print(f"科技股板块表已创建，当前记录数: {ts.get_count()}")
    print(f"可用板块: {ts.get_all_sectors()}")
    ts.close()