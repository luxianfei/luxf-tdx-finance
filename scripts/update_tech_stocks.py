"""
科技股识别脚本
基于股票代码前缀和行业关键词从stock_list中识别科技股
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.tech_sector import TechStockSector
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

# 科技相关行业关键词（用于匹配行业名称）
TECH_KEYWORDS = [
    # 半导体/芯片
    '半导体', '芯片', '集成电路', '晶圆', '光刻', '封装', '测试', 'IC',
    # 人工智能
    '人工智能', 'AI', '机器学习', '深度学习', '机器人', '自动化',
    # 软件/互联网
    '软件', '互联网', '云计算', '大数据', '数据中心', '服务器', 'IT服务',
    # 通信
    '通信', '5G', '基站', '射频', '天线', '光通信', '光纤',
    # 新能源
    '光伏', '太阳能', '锂电池', '新能源', '动力电池', '储能',
    # 智能汽车
    '智能汽车', '新能源车', '汽车电子', '自动驾驶', '车联网',
    # 医药生物
    '生物医药', '医疗器械', '创新药', '基因', '疫苗', '诊断',
    # 智能制造
    '工业机器人', '智能制造', '数控机床', '工业自动化',
    # 其他科技
    '电子', '科技', '计算机', '数字', '信息', '网络', '安防'
]

# 科技板块映射（基于代码前缀和行业）
SECTOR_BY_CODE_PREFIX = {
    '688': '科创板',      # 科创板 - 高科技企业聚集地
    '300': '创业板',      # 创业板 - 创新型企业
    '002': '中小板',      # 中小板
    '60': '主板',         # 主板
    '000': '主板'         # 主板
}

# 已知科技股列表（手动添加一些知名科技股）
KNOWN_TECH_STOCKS = {
    # 半导体/芯片
    '600584': ('长电科技', '半导体'),
    '600460': ('士兰微', '半导体'),
    '002156': ('通富微电', '半导体'),
    '002185': ('华天科技', '半导体'),
    '603986': ('兆易创新', '半导体'),
    '603160': ('汇顶科技', '半导体'),
    '300661': ('圣邦股份', '半导体'),
    '300782': ('卓胜微', '半导体'),
    '688981': ('中芯国际', '半导体'),
    '688396': ('华润微', '半导体'),
    '688595': ('芯海科技', '半导体'),
    '688046': ('赛微电子', '半导体'),
    '300793': ('佳禾智能', '人工智能'),
    # 人工智能
    '002230': ('科大讯飞', '人工智能'),
    '300024': ('机器人', '人工智能'),
    '000938': ('紫光国微', '人工智能'),
    '300450': ('先导智能', '人工智能'),
    '600536': ('中国软件', '软件服务'),
    '600756': ('浪潮软件', '软件服务'),
    '300253': ('卫宁健康', '软件服务'),
    '300377': ('赢时胜', '软件服务'),
    '688111': ('金山办公', '软件服务'),
    # 通信设备
    '000063': ('中兴通讯', '通信设备'),
    '002415': ('海康威视', '通信设备'),
    '002236': ('大华股份', '通信设备'),
    '000021': ('深科技', '通信设备'),
    '600498': ('烽火通信', '通信设备'),
    '600522': ('中天科技', '通信设备'),
    '300502': ('新易盛', '通信设备'),
    # 新能源
    '300750': ('宁德时代', '新能源'),
    '300014': ('亿纬锂能', '新能源'),
    '002594': ('比亚迪', '智能汽车'),
    '300124': ('汇川技术', '新能源'),
    '600438': ('通威股份', '光伏'),
    '601012': ('隆基绿能', '光伏'),
    '688599': ('天合光能', '光伏'),
    # 生物医药
    '600276': ('恒瑞医药', '生物医药'),
    '603259': ('药明康德', '生物医药'),
    '300760': ('迈瑞医疗', '医疗器械'),
    '688298': ('东方生物', '生物医药'),
    '300601': ('康泰生物', '生物医药'),
    # 云计算/大数据
    '000977': ('浪潮信息', '云计算'),
    '603019': ('中科曙光', '云计算'),
    '300296': ('利亚德', '云计算'),
    # 5G
    '000063': ('中兴通讯', '5G'),
    '600776': ('东方通信', '5G'),
    '300312': ('邦讯技术', '5G'),
    # 智能汽车
    '600741': ('华域汽车', '智能汽车'),
    '002594': ('比亚迪', '智能汽车'),
    '300104': ('乐视网', '智能汽车'),
    '600104': ('上汽集团', '智能汽车'),
}

def classify_by_code_prefix(code):
    """根据股票代码前缀判断板块"""
    if code.startswith('688'):
        return '科创板'
    elif code.startswith('300'):
        return '创业板'
    elif code.startswith('002'):
        return '中小板'
    elif code.startswith('60'):
        return '主板'
    elif code.startswith('000'):
        return '主板'
    return None

def classify_tech_sector(industry_name, code):
    """根据行业名称和代码判断所属科技板块"""
    # 首先检查已知科技股列表
    if code in KNOWN_TECH_STOCKS:
        return KNOWN_TECH_STOCKS[code][1], KNOWN_TECH_STOCKS[code][0]
    
    # 根据代码前缀判断
    sector = classify_by_code_prefix(code)
    if sector in ['科创板', '创业板']:
        return sector, None
    
    # 如果行业名称包含科技关键词
    if industry_name:
        industry = str(industry_name).lower()
        for keyword in TECH_KEYWORDS:
            if keyword.lower() in industry:
                return '科技股', keyword
    
    return None, None

def identify_tech_stocks():
    """识别所有科技股"""
    db = MySQLClient(MYSQL_CONFIG)
    
    # 获取所有活跃股票
    sql = "SELECT code, name, industry FROM stock_list WHERE status = 'active'"
    stocks = db.query_all(sql)
    
    tech_stocks = []
    
    for stock in stocks:
        code = stock['code']
        name = stock['name']
        industry = stock['industry']
        
        sector, sub_sector = classify_tech_sector(industry, code)
        
        if sector:
            # 获取市值数据
            market_cap_sql = "SELECT market_cap FROM stock_market_data WHERE code = %s"
            market_cap_result = db.query_one(market_cap_sql, (code,))
            market_cap = market_cap_result['market_cap'] if market_cap_result else None
            
            tech_stocks.append({
                'code': code,
                'name': name,
                'sector': sector,
                'sub_sector': sub_sector,
                'industry': industry,
                'market_cap': market_cap
            })
    
    db.close()
    return tech_stocks

def update_tech_sector_stocks():
    """更新科技股板块数据"""
    tech_stocks = identify_tech_stocks()
    print(f"识别到 {len(tech_stocks)} 只科技股")
    
    if len(tech_stocks) == 0:
        print("未识别到科技股，将使用预设的已知科技股列表")
        # 使用预设的已知科技股
        tech_stocks = []
        for code, (name, sector) in KNOWN_TECH_STOCKS.items():
            tech_stocks.append({
                'code': code,
                'name': name,
                'sector': sector,
                'sub_sector': None,
                'industry': sector,
                'market_cap': None
            })
    
    ts = TechStockSector()
    ts.clear_all()
    
    # 转换为批量插入格式
    insert_data = []
    for stock in tech_stocks:
        insert_data.append((
            stock['code'],
            stock['name'],
            stock['sector'],
            stock['sub_sector'],
            None,  # market
            stock['industry'],
            None,  # pe
            None,  # pb
            None,  # ps
            None,  # revenue_growth
            None,  # profit_growth
            stock['market_cap']
        ))
    
    ts.insert_batch(insert_data)
    print(f"已更新 {ts.get_count()} 只科技股到数据库")
    
    # 打印板块分布
    sectors = ts.get_all_sectors()
    print("\n板块分布:")
    for sector in sectors:
        count = len(ts.get_stocks_by_sector(sector))
        print(f"  {sector}: {count}只")
    
    ts.close()

if __name__ == '__main__':
    update_tech_sector_stocks()