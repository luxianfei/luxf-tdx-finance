#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从通达信本地数据读取申万一级行业分类，更新到industry_map表和stock_list表
"""

import os
import sys
import struct

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

# 申万一级行业分类（31个）
SHENWAN_INDUSTRY_MAP = {
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

def parse_blk_file(filepath):
    """
    解析通达信板块文件(.blk)
    文件格式：
    - 前4字节: 板块名称长度
    - 后续: 板块名称(GBK编码)
    - 每8字节为一个股票记录: 前2字节市场代码, 后6字节股票代码(右对齐)
    """
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # 读取板块名称长度
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

def parse_dax_file(filepath):
    """
    解析通达信数据文件(.dax)
    尝试提取行业分类信息
    """
    industry_stocks = {}
    
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        # 尝试查找行业相关数据
        # .dax文件格式较为复杂，这里简单处理
        print(f"读取 .dax 文件: {filepath}, 大小: {len(data)} 字节")
        
    except Exception as e:
        print(f"解析 .dax 文件失败: {e}")
    
    return industry_stocks

def scan_tdx_block_files(tdx_path):
    """
    扫描通达信板块文件，提取行业分类
    """
    industry_stocks = {}
    blocknew_path = os.path.join(tdx_path, 'T0002', 'blocknew')
    
    if not os.path.exists(blocknew_path):
        print(f"板块目录不存在: {blocknew_path}")
        return industry_stocks
    
    # 扫描所有.blk文件
    blk_files = [f for f in os.listdir(blocknew_path) if f.endswith('.blk')]
    
    for blk_file in blk_files:
        filepath = os.path.join(blocknew_path, blk_file)
        name, stocks = parse_blk_file(filepath)
        
        if name and stocks:
            # 判断是否为行业板块（通常包含"行业"关键字或特定命名）
            if '行业' in name or any(keyword in name for keyword in ['SW', '申万', '板块', '概念']):
                industry_stocks[name] = stocks
                print(f"发现板块: {name}, 包含 {len(stocks)} 只股票")
    
    return industry_stocks

def update_industry_map(db, industry_list):
    """
    更新industry_map表
    """
    # 清空现有数据
    db.execute("TRUNCATE TABLE industry_map")
    
    # 插入新数据
    insert_sql = """
    INSERT INTO industry_map (code, name, parent_code, level)
    VALUES (%s, %s, %s, %s)
    """
    
    for code, name in industry_list.items():
        db.execute(insert_sql, (code, name, None, 1))
    
    db.commit()
    print(f"已更新 {len(industry_list)} 条行业分类数据")

def update_stock_industry(db, stock_industry_map):
    """
    更新stock_list表中的行业字段
    """
    update_sql = """
    UPDATE stock_list 
    SET industry = %s 
    WHERE code = %s
    """
    
    count = 0
    for code, industry_name in stock_industry_map.items():
        db.execute(update_sql, (industry_name, code))
        count += 1
    
    db.commit()
    print(f"已更新 {count} 只股票的行业信息")

def get_shenwan_industry_code(industry_name):
    """
    根据行业名称获取申万行业代码
    """
    for code, name in SHENWAN_INDUSTRY_MAP.items():
        if name in industry_name or industry_name in name:
            return code
    return None

def main():
    tdx_path = r'D:\SoftwaresInstalled\dycy'
    
    # 检查通达信路径
    if not os.path.exists(tdx_path):
        print(f"通达信路径不存在: {tdx_path}")
        return
    
    print("开始从通达信读取行业分类数据...")
    
    # 扫描板块文件
    industry_stocks = scan_tdx_block_files(tdx_path)
    
    if not industry_stocks:
        print("未找到行业板块数据，使用预定义的申万行业分类")
        # 使用预定义的申万行业分类
        db = MySQLClient(MYSQL_CONFIG)
        update_industry_map(db, SHENWAN_INDUSTRY_MAP)
        db.close()
        return
    
    # 连接数据库
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 更新行业映射表
        print("\n更新行业映射表...")
        update_industry_map(db, SHENWAN_INDUSTRY_MAP)
        
        # 构建股票-行业映射
        stock_industry_map = {}
        for industry_name, stocks in industry_stocks.items():
            # 尝试匹配申万行业
            shenwan_code = get_shenwan_industry_code(industry_name)
            target_industry = SHENWAN_INDUSTRY_MAP.get(shenwan_code, industry_name)
            
            for code, exchange in stocks:
                # 股票代码可能需要调整格式（去掉前导空格）
                clean_code = code.strip()
                if clean_code:
                    stock_industry_map[clean_code] = target_industry
        
        # 更新股票行业信息
        print("\n更新股票行业信息...")
        update_stock_industry(db, stock_industry_map)
        
        print("\n完成！")
        
    finally:
        db.close()

if __name__ == '__main__':
    main()