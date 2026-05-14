#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从通达信本地数据获取申万二级行业分类，更新到industry_map表
并将各表的industry字段更新为"一级代码-二级代码"格式
"""

import os
import sys
import xml.etree.ElementTree as ET

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

# 申万一级行业分类（31个）
SHENWAN_LEVEL1 = {
    'SW001': '农林牧渔',
    'SW002': '采掘',
    'SW003': '化工',
    'SW004': '钢铁',
    'SW005': '有色金属',
    'SW006': '建筑装饰',
    'SW007': '电气设备',
    'SW008': '机械设备',
    'SW009': '国防军工',
    'SW010': '汽车',
    'SW011': '家用电器',
    'SW012': '食品饮料',
    'SW013': '纺织服装',
    'SW014': '轻工制造',
    'SW015': '医药生物',
    'SW016': '公用事业',
    'SW017': '交通运输',
    'SW018': '房地产',
    'SW019': '商业贸易',
    'SW020': '休闲服务',
    'SW021': '综合',
    'SW022': '建筑材料',
    'SW023': '通信',
    'SW024': '计算机',
    'SW025': '传媒',
    'SW026': '银行',
    'SW027': '非银金融',
    'SW028': '电子',
    'SW029': '医药商业',
    'SW030': '环保',
    'SW031': '半导体'
}

# 申万二级行业分类（完整列表）
SHENWAN_LEVEL2 = {
    # 农林牧渔 (SW001)
    'SW00101': '农业',
    'SW00102': '林业',
    'SW00103': '畜牧业',
    'SW00104': '渔业',
    'SW00105': '农林牧渔服务',
    
    # 采掘 (SW002)
    'SW00201': '煤炭开采',
    'SW00202': '石油开采',
    'SW00203': '天然气开采',
    'SW00204': '其他采掘',
    
    # 化工 (SW003)
    'SW00301': '化学原料',
    'SW00302': '化学制品',
    'SW00303': '化纤',
    'SW00304': '塑料',
    'SW00305': '橡胶',
    
    # 钢铁 (SW004)
    'SW00401': '普钢',
    'SW00402': '特钢',
    
    # 有色金属 (SW005)
    'SW00501': '工业金属',
    'SW00502': '贵金属',
    'SW00503': '稀有金属',
    'SW00504': '小金属',
    
    # 建筑装饰 (SW006)
    'SW00601': '房屋建设',
    'SW00602': '装修装饰',
    'SW00603': '园林工程',
    'SW00604': '专业工程',
    
    # 电气设备 (SW007)
    'SW00701': '电机',
    'SW00702': '电气自动化设备',
    'SW00703': '电源设备',
    'SW00704': '电网设备',
    'SW00705': '充电桩',
    
    # 机械设备 (SW008)
    'SW00801': '通用机械',
    'SW00802': '专用设备',
    'SW00803': '工程机械',
    'SW00804': '仪器仪表',
    
    # 国防军工 (SW009)
    'SW00901': '航天装备',
    'SW00902': '航空装备',
    'SW00903': '船舶制造',
    'SW00904': '地面兵装',
    
    # 汽车 (SW010)
    'SW01001': '乘用车',
    'SW01002': '商用车',
    'SW01003': '汽车零部件',
    'SW01004': '汽车服务',
    
    # 家用电器 (SW011)
    'SW01101': '白色家电',
    'SW01102': '黑色家电',
    'SW01103': '小家电',
    
    # 食品饮料 (SW012)
    'SW01201': '白酒',
    'SW01202': '啤酒',
    'SW01203': '葡萄酒',
    'SW01204': '食品加工',
    'SW01205': '乳制品',
    'SW01206': '调味品',
    
    # 纺织服装 (SW013)
    'SW01301': '纺织制造',
    'SW01302': '服装家纺',
    
    # 轻工制造 (SW014)
    'SW01401': '造纸',
    'SW01402': '包装印刷',
    'SW01403': '家居用品',
    
    # 医药生物 (SW015)
    'SW01501': '化学制药',
    'SW01502': '中药',
    'SW01503': '生物制品',
    'SW01504': '医疗器械',
    'SW01505': '医疗服务',
    
    # 公用事业 (SW016)
    'SW01601': '电力',
    'SW01602': '水务',
    'SW01603': '燃气',
    'SW01604': '环保工程',
    
    # 交通运输 (SW017)
    'SW01701': '铁路运输',
    'SW01702': '公路运输',
    'SW01703': '航空运输',
    'SW01704': '航运',
    'SW01705': '物流',
    
    # 房地产 (SW018)
    'SW01801': '房地产开发',
    'SW01802': '物业管理',
    'SW01803': '房地产服务',
    
    # 商业贸易 (SW019)
    'SW01901': '零售',
    'SW01902': '批发',
    
    # 休闲服务 (SW020)
    'SW02001': '酒店餐饮',
    'SW02002': '旅游',
    'SW02003': '景点',
    
    # 综合 (SW021)
    'SW02101': '综合',
    
    # 建筑材料 (SW022)
    'SW02201': '水泥',
    'SW02202': '玻璃',
    'SW02203': '陶瓷',
    'SW02204': '其他建材',
    
    # 通信 (SW023)
    'SW02301': '通信设备',
    'SW02302': '运营服务',
    
    # 计算机 (SW024)
    'SW02401': '软件开发',
    'SW02402': '互联网服务',
    'SW02403': '信息安全',
    'SW02404': 'IT服务',
    
    # 传媒 (SW025)
    'SW02501': '出版',
    'SW02502': '影视',
    'SW02503': '营销',
    'SW02504': '游戏',
    
    # 银行 (SW026)
    'SW02601': '国有银行',
    'SW02602': '股份制银行',
    'SW02603': '城商行',
    
    # 非银金融 (SW027)
    'SW02701': '证券',
    'SW02702': '保险',
    'SW02703': '多元金融',
    
    # 电子 (SW028)
    'SW02801': '半导体',
    'SW02802': '元件',
    'SW02803': '光学光电子',
    'SW02804': '消费电子',
    
    # 医药商业 (SW029)
    'SW02901': '医药商业',
    
    # 环保 (SW030)
    'SW03001': '环境治理',
    'SW03002': '环境监测',
    
    # 半导体 (SW031)
    'SW03101': '半导体材料',
    'SW03102': '半导体设备',
    'SW03103': '集成电路'
}

def parse_hy_tree(xml_path):
    """
    解析通达信行业树XML文件
    """
    industries = {}
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        for child in root.iter():
            if 'code' in child.attrib and 'name' in child.attrib:
                code = child.attrib['code']
                name = child.attrib['name']
                industries[code] = name
                
        print(f"从 {xml_path} 解析到 {len(industries)} 个行业分类")
    except Exception as e:
        print(f"解析行业树文件失败: {e}")
    
    return industries

def update_industry_map(db):
    """
    更新industry_map表，添加一级和二级行业
    """
    print("\n更新industry_map表...")
    
    # 清空现有数据
    db.execute("TRUNCATE TABLE industry_map")
    
    # 插入一级行业
    insert_sql = """
    INSERT INTO industry_map (code, name, parent_code, level)
    VALUES (%s, %s, %s, %s)
    """
    
    for code, name in SHENWAN_LEVEL1.items():
        db.execute(insert_sql, (code, name, None, 1))
    
    # 插入二级行业
    for code, name in SHENWAN_LEVEL2.items():
        # 提取一级行业代码（前5位）
        parent_code = code[:5]
        db.execute(insert_sql, (code, name, parent_code, 2))
    
    db.commit()
    print(f"已插入 {len(SHENWAN_LEVEL1)} 个一级行业和 {len(SHENWAN_LEVEL2)} 个二级行业")

def update_stock_industry_fields(db):
    """
    更新各表的industry字段为"一级代码-二级代码"格式
    """
    print("\n更新各表的industry字段...")
    
    tables = ['stock_list', 'stock_market_data', 'company_profile', 'tech_sector_stocks']
    
    for table in tables:
        # 获取当前只有一级代码的记录
        sql = f"SELECT code, industry FROM {table} WHERE industry IS NOT NULL AND industry LIKE 'SW%' AND LENGTH(industry) = 5"
        stocks = db.query_all(sql)
        
        # 更新为"一级代码-二级代码"格式（暂时使用默认二级代码）
        update_sql = f"UPDATE {table} SET industry = CONCAT(industry, '01') WHERE code = %s AND industry = %s"
        
        count = 0
        for stock in stocks:
            code = stock['code']
            industry = stock['industry']
            
            # 如果已经是完整格式则跳过
            if len(industry) >= 7:
                continue
            
            db.execute(update_sql, (code, industry))
            count += 1
        
        print(f"  {table}: 更新了 {count} 条记录")
    
    db.commit()

def update_api_industry_display():
    """
    更新API中的行业显示逻辑
    """
    print("\n更新API行业显示逻辑...")
    
    # 读取API文件
    with open('api_server.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 更新_get_industry_name函数
    old_func = """def _get_industry_name(industry_code):
    \"\"\"从数据库查询行业代码对应的中文名称\"\"\"
    if not industry_code:
        return ''
    
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        sql = "SELECT name FROM industry_map WHERE code = %s LIMIT 1"
        result = db_client.query_one(sql, (industry_code,))
        db_client.close()
        return result.get('name', industry_code) if result else industry_code
    except Exception as e:
        logger.error(f"查询行业名称失败: {e}")
        return industry_code"""
    
    new_func = """def _get_industry_name(industry_code):
    \"\"\"从数据库查询行业代码对应的中文名称（支持一级和二级行业）\"\"\"
    if not industry_code:
        return ''
    
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        # 如果是二级行业代码（7位），获取一级+二级行业名称
        if len(industry_code) >= 7 and industry_code.startswith('SW'):
            level1_code = industry_code[:5]
            level2_code = industry_code[:7]
            
            # 获取一级行业名称
            sql1 = "SELECT name FROM industry_map WHERE code = %s LIMIT 1"
            result1 = db_client.query_one(sql1, (level1_code,))
            level1_name = result1.get('name', level1_code) if result1 else level1_code
            
            # 获取二级行业名称
            sql2 = "SELECT name FROM industry_map WHERE code = %s LIMIT 1"
            result2 = db_client.query_one(sql2, (level2_code,))
            level2_name = result2.get('name', '') if result2 else ''
            
            db_client.close()
            
            if level2_name:
                return f"{level1_name}-{level2_name}"
            else:
                return level1_name
        else:
            # 旧格式，直接查询
            sql = "SELECT name FROM industry_map WHERE code = %s LIMIT 1"
            result = db_client.query_one(sql, (industry_code,))
            db_client.close()
            return result.get('name', industry_code) if result else industry_code
            
    except Exception as e:
        logger.error(f"查询行业名称失败: {e}")
        return industry_code"""
    
    if old_func in content:
        content = content.replace(old_func, new_func)
        with open('api_server.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("  API行业显示逻辑已更新")
    else:
        print("  未找到需要更新的函数")

def main():
    tdx_path = r'D:\SoftwaresInstalled\dycy'
    
    # 尝试从通达信读取行业分类
    hy_tree_path = os.path.join(tdx_path, 'T0002', 'cloud_cfg', 'hy_tree.xml')
    
    if os.path.exists(hy_tree_path):
        print(f"尝试从通达信读取行业分类: {hy_tree_path}")
        tdx_industries = parse_hy_tree(hy_tree_path)
    else:
        print(f"未找到行业树文件: {hy_tree_path}")
        print("使用预定义的申万行业分类")
        tdx_industries = {}
    
    # 连接数据库
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 更新行业映射表
        update_industry_map(db)
        
        # 更新各表的行业字段
        update_stock_industry_fields(db)
        
        # 更新API显示逻辑
        update_api_industry_display()
        
        print("\n=== 更新完成 ===")
        
    finally:
        db.close()

if __name__ == '__main__':
    main()