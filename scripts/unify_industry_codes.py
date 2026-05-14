#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一更新所有表的行业字段为申万行业代码
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

# 申万一级行业分类
SHENWAN_INDUSTRY = {
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

# 通达信行业代码到申万行业代码的映射
TDX_TO_SHENWAN = {
    '1': 'SW001', '2': 'SW002', '3': 'SW003', '4': 'SW004', '5': 'SW005',
    '6': 'SW006', '7': 'SW008', '8': 'SW028', '9': 'SW012', '10': 'SW013',
    '11': 'SW014', '12': 'SW015', '13': 'SW016', '14': 'SW017', '15': 'SW018',
    '16': 'SW019', '17': 'SW020', '18': 'SW021', '19': 'SW022', '20': 'SW007',
    '21': 'SW009', '22': 'SW024', '23': 'SW025', '24': 'SW023', '25': 'SW026',
    '26': 'SW027', '27': 'SW010', '28': 'SW011', '29': 'SW029', '30': 'SW027',
    '31': 'SW027', '32': 'SW027', '33': 'SW002', '34': 'SW003', '35': 'SW003',
    '36': 'SW007', '37': 'SW007', '38': 'SW007', '39': 'SW007', '40': 'SW007',
    '41': 'SW008', '42': 'SW007', '43': 'SW018', '44': 'SW018', '45': 'SW008',
    '46': 'SW008', '47': 'SW008', '48': 'SW008', '49': 'SW009', '50': 'SW009',
    '51': 'SW009', '52': 'SW017'
}

def update_industry_map(db):
    """更新industry_map表，添加申万行业分类"""
    print("更新industry_map表...")
    
    # 清空现有数据
    db.execute("TRUNCATE TABLE industry_map")
    
    # 插入申万行业数据
    insert_sql = """
    INSERT INTO industry_map (code, name, parent_code, level)
    VALUES (%s, %s, %s, %s)
    """
    
    for code, name in SHENWAN_INDUSTRY.items():
        db.execute(insert_sql, (code, name, None, 1))
    
    db.commit()
    print(f"已插入 {len(SHENWAN_INDUSTRY)} 条申万行业数据")

def update_stock_list_industry(db):
    """更新stock_list表的行业字段"""
    print("\n更新stock_list表的行业字段...")
    
    # 获取所有股票及其行业
    stocks = db.query_all('SELECT code, industry FROM stock_list WHERE industry IS NOT NULL')
    
    count = 0
    update_sql = "UPDATE stock_list SET industry = %s WHERE code = %s"
    
    for stock in stocks:
        original_industry = str(stock['industry']).strip()
        
        # 跳过空值和无效值
        if not original_industry or original_industry in ['-', '--', '---', '0', 'None']:
            continue
        
        # 如果已经是SW格式，保持不变
        if original_industry.startswith('SW'):
            continue
        
        # 尝试映射到申万行业代码
        shenwan_code = TDX_TO_SHENWAN.get(original_industry)
        
        if shenwan_code:
            db.execute(update_sql, (shenwan_code, stock['code']))
            count += 1
    
    db.commit()
    print(f"已更新 {count} 条记录")

def update_tech_sector_stocks_industry(db):
    """更新tech_sector_stocks表的行业字段"""
    print("\n更新tech_sector_stocks表的行业字段...")
    
    stocks = db.query_all('SELECT code, industry FROM tech_sector_stocks WHERE industry IS NOT NULL')
    
    count = 0
    update_sql = "UPDATE tech_sector_stocks SET industry = %s WHERE code = %s"
    
    for stock in stocks:
        original_industry = str(stock['industry']).strip()
        
        if not original_industry or original_industry in ['-', '--', '---', '0', 'None']:
            continue
        
        if original_industry.startswith('SW'):
            continue
        
        shenwan_code = TDX_TO_SHENWAN.get(original_industry)
        
        if shenwan_code:
            db.execute(update_sql, (shenwan_code, stock['code']))
            count += 1
    
    db.commit()
    print(f"已更新 {count} 条记录")

def update_company_profile_industry(db):
    """更新company_profile表的行业字段"""
    print("\n更新company_profile表的行业字段...")
    
    # 获取所有记录
    profiles = db.query_all('SELECT code, industry FROM company_profile WHERE industry IS NOT NULL')
    
    count = 0
    update_sql = "UPDATE company_profile SET industry = %s WHERE code = %s"
    
    for profile in profiles:
        original_industry = str(profile['industry']).strip()
        
        # 清理无效值
        if not original_industry or original_industry in ['-', '--', '---', '0', 'None', '']:
            db.execute(update_sql, ('', profile['code']))
            count += 1
            continue
        
        if original_industry.startswith('SW'):
            continue
        
        # 尝试映射
        shenwan_code = TDX_TO_SHENWAN.get(original_industry)
        
        if shenwan_code:
            db.execute(update_sql, (shenwan_code, profile['code']))
            count += 1
    
    db.commit()
    print(f"已更新 {count} 条记录")

def update_stock_market_data_industry(db):
    """更新stock_market_data表的行业字段"""
    print("\n更新stock_market_data表的行业字段...")
    
    # 获取所有记录
    market_data = db.query_all('SELECT code, industry FROM stock_market_data WHERE industry IS NOT NULL')
    
    count = 0
    update_sql = "UPDATE stock_market_data SET industry = %s WHERE code = %s"
    
    for data in market_data:
        original_industry = str(data['industry']).strip()
        
        # 清理无效值（stock_market_data中的值看起来很奇怪）
        if not original_industry or original_industry in ['-', '--', '---', '0', 'None', '']:
            db.execute(update_sql, ('', data['code']))
            count += 1
            continue
        
        if original_industry.startswith('SW'):
            continue
        
        # 尝试映射
        shenwan_code = TDX_TO_SHENWAN.get(original_industry)
        
        if shenwan_code:
            db.execute(update_sql, (shenwan_code, data['code']))
            count += 1
    
    db.commit()
    print(f"已更新 {count} 条记录")

def main():
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 更新行业映射表
        update_industry_map(db)
        
        # 更新各表的行业字段
        update_stock_list_industry(db)
        update_tech_sector_stocks_industry(db)
        update_company_profile_industry(db)
        update_stock_market_data_industry(db)
        
        print("\n=== 更新完成 ===")
        
    finally:
        db.close()

if __name__ == '__main__':
    main()