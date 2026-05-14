#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从通达信本地板块文件解析股票所属板块，更新到stock_market_data表的plate字段
"""

import os
import sys
import struct

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

# 预定义的板块分类（用于匹配通达信板块名称）
PLATE_CATEGORIES = {
    # 市场板块
    '主板': ['主板', '沪市', '深市'],
    '创业板': ['创业板', '创业板指', '300'],
    '科创板': ['科创板', '科创', '688'],
    '中小板': ['中小板', '002'],
    'ST板块': ['ST', '*ST'],
    
    # 概念板块
    '国产替代': ['国产替代', '自主可控', '国产芯片'],
    '人工智能': ['人工智能', 'AI', '智能'],
    '半导体': ['半导体', '芯片', '集成电路'],
    '5G': ['5G', '通信', '基站'],
    '新能源': ['新能源', '光伏', '风电', '锂电', '储能'],
    '军工': ['军工', '国防', '航天', '航空'],
    '医药': ['医药', '医疗', '生物', '疫苗'],
    '消费': ['消费', '食品', '饮料', '零售'],
    '金融': ['金融', '银行', '证券', '保险'],
    '周期': ['周期', '有色', '煤炭', '钢铁'],
}

def parse_blk_file(filepath):
    """
    解析通达信板块文件(.blk)
    文件格式：
    - 前2字节: 板块名称长度(小端)
    - 后续: 板块名称(GBK编码)
    - 每8字节为一个股票记录: 前2字节市场代码, 后6字节股票代码(右对齐)
    """
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        if len(data) < 2:
            return None, []
        
        # 读取板块名称长度（前2字节，小端）
        name_len = struct.unpack('<H', data[:2])[0]
        
        # 读取板块名称
        name = data[2:2+name_len].decode('gbk', errors='ignore').strip()
        
        # 解析股票列表
        stocks = []
        offset = 2 + name_len
        while offset + 8 <= len(data):
            # 每8字节一个股票
            market_code = struct.unpack('<H', data[offset:offset+2])[0]
            code_bytes = data[offset+2:offset+8]
            code = code_bytes.decode('ascii').strip()
            offset += 8
            
            # 市场代码: 0=深圳, 1=上海
            exchange = 'SZ' if market_code == 0 else 'SH'
            stocks.append((code, exchange))
        
        return name, stocks
    except Exception as e:
        print(f"解析文件 {filepath} 失败: {e}")
        return None, []

def scan_tdx_block_files(tdx_path):
    """
    扫描通达信板块文件
    """
    plate_stocks = {}
    blocknew_path = os.path.join(tdx_path, 'T0002', 'blocknew')
    
    if not os.path.exists(blocknew_path):
        print(f"板块目录不存在: {blocknew_path}")
        return plate_stocks
    
    # 扫描所有.blk文件
    blk_files = [f for f in os.listdir(blocknew_path) if f.endswith('.blk')]
    
    for blk_file in blk_files:
        filepath = os.path.join(blocknew_path, blk_file)
        name, stocks = parse_blk_file(filepath)
        
        if name and stocks:
            plate_stocks[name] = stocks
            print(f"发现板块: {name}, 包含 {len(stocks)} 只股票")
    
    return plate_stocks

def get_main_plate(plate_names):
    """
    根据板块名称列表确定主板块
    """
    # 优先匹配市场板块
    market_plates = ['创业板', '科创板', '中小板', '主板']
    for plate in plate_names:
        for market in market_plates:
            if market in plate or any(keyword in plate for keyword in PLATE_CATEGORIES[market]):
                return market
    
    # 匹配概念板块
    for category, keywords in PLATE_CATEGORIES.items():
        for plate in plate_names:
            if any(keyword in plate for keyword in keywords):
                return category
    
    # 默认返回第一个板块
    return plate_names[0] if plate_names else ''

def update_stock_plate(db):
    """
    更新stock_market_data表的plate字段
    """
    tdx_path = r'D:\SoftwaresInstalled\dycy'
    
    # 扫描板块文件
    plate_stocks = scan_tdx_block_files(tdx_path)
    
    if not plate_stocks:
        print("未找到板块数据，使用预定义的板块映射")
        use_default_plates(db)
        return
    
    # 构建股票到板块的映射
    stock_plate_map = {}
    for plate_name, stocks in plate_stocks.items():
        for code, exchange in stocks:
            clean_code = code.strip()
            if clean_code:
                if clean_code not in stock_plate_map:
                    stock_plate_map[clean_code] = []
                stock_plate_map[clean_code].append(plate_name)
    
    # 更新数据库
    update_sql = "UPDATE stock_market_data SET plate = %s WHERE code = %s"
    count = 0
    
    for code, plates in stock_plate_map.items():
        main_plate = get_main_plate(plates)
        if main_plate:
            db.execute(update_sql, (main_plate, code))
            count += 1
    
    db.commit()
    print(f"\n已更新 {count} 只股票的板块信息")

def use_default_plates(db):
    """
    使用预定义的板块映射（基于代码前缀）
    """
    print("使用预定义板块映射")
    
    # 根据代码前缀判断板块
    prefix_plate_map = {
        '300': '创业板',
        '688': '科创板',
        '002': '中小板',
        '000': '主板',
        '600': '主板',
        '601': '主板',
        '603': '主板',
        '605': '主板',
        '43': '北交所',
        '83': '北交所'
    }
    
    # 获取所有股票代码
    stocks = db.query_all('SELECT DISTINCT code FROM stock_market_data WHERE plate IS NULL OR plate = "" OR plate = "--"')
    
    update_sql = "UPDATE stock_market_data SET plate = %s WHERE code = %s"
    count = 0
    
    for stock in stocks:
        code = stock['code']
        for prefix, plate in prefix_plate_map.items():
            if code.startswith(prefix):
                db.execute(update_sql, (plate, code))
                count += 1
                break
    
    db.commit()
    print(f"已更新 {count} 只股票的板块信息（基于代码前缀）")

def main():
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        print("开始从通达信解析板块数据...")
        update_stock_plate(db)
        print("\n=== 更新完成 ===")
        
    finally:
        db.close()

if __name__ == '__main__':
    main()