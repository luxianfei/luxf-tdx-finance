#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用启发式方法更新股票名称
从company_profile表中提取股票简称
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def extract_stock_name(full_name):
    """从公司全称提取股票简称"""
    if not full_name or full_name == '--' or full_name == '未知':
        return None
    
    # 去除末尾的常见后缀
    suffixes = ['股份有限公司', '有限公司', '股份公司', '集团股份有限公司', 
                '集团有限公司', '科技股份有限公司', '控股股份有限公司',
                '发展股份有限公司', '实业股份有限公司', '投资股份有限公司',
                '生物科技股份有限公司', '医药股份有限公司']
    
    name = full_name.strip()
    
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break
    
    # 如果名称太短，直接返回
    if len(name) <= 4:
        return name
    
    # 尝试提取核心部分（去掉行业词）
    industry_words = ['科技', '银行', '证券', '保险', '集团', '控股', '股份', 
                      '发展', '投资', '实业', '生物', '医药', '医疗', '健康',
                      '电子', '电气', '机械', '设备', '能源', '环保', '科技',
                      '软件', '网络', '通信', '信息', '数据', '智能', '数字',
                      '材料', '化工', '化学', '制药', '食品', '饮料', '农业',
                      '矿业', '资源', '金属', '钢铁', '汽车', '交通', '物流',
                      '建筑', '地产', '物业', '商业', '贸易', '零售', '服务',
                      '文化', '传媒', '娱乐', '教育', '旅游', '酒店', '餐饮']
    
    # 如果名称较长，尝试提取前半部分
    if len(name) > 6:
        # 查找行业词位置
        for word in industry_words:
            idx = name.find(word)
            if idx > 0:
                if idx <= 4:
                    # 行业词在前4个字符内，取到行业词结束
                    result = name[:idx + len(word)]
                else:
                    # 行业词在后面，取前4个字符
                    result = name[:4]
                return result
        
        # 如果没有找到行业词，取前4个字符
        return name[:4]
    
    return name


def update_names():
    """更新股票名称"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取需要更新的股票
        sql = "SELECT code, name FROM stock_list WHERE name LIKE '股票%'"
        results = db.query_all(sql)
        print(f"需要更新的股票数量: {len(results)}")
        
        if not results:
            print("没有需要更新的股票")
            return
        
        # 获取company_profile中的公司名称
        sql_profile = "SELECT code, company_name FROM company_profile WHERE company_name IS NOT NULL AND company_name != '--' AND company_name != '未知'"
        profiles = db.query_all(sql_profile)
        profile_dict = {p['code']: p['company_name'] for p in profiles}
        
        print(f"从company_profile获取了 {len(profile_dict)} 条公司名称")
        
        # 更新股票名称
        conn = db.connect()
        update_sql = "UPDATE stock_list SET name = %s WHERE code = %s"
        
        updated_count = 0
        heuristic_count = 0
        
        with conn.cursor() as cursor:
            for row in results:
                code = row['code']
                full_name = profile_dict.get(code)
                
                if full_name:
                    short_name = extract_stock_name(full_name)
                    if short_name:
                        cursor.execute(update_sql, (short_name, code))
                        updated_count += 1
                        heuristic_count += 1
                        print(f"  {code}: {short_name} (从公司名称提取)")
        
            conn.commit()
        
        print(f"\n成功更新 {updated_count} 只股票的名称")
        print(f"  使用启发式方法: {heuristic_count} 只")
        
        # 统计结果
        sql_updated = "SELECT COUNT(*) as cnt FROM stock_list WHERE name NOT LIKE '股票%'"
        sql_not_updated = "SELECT COUNT(*) as cnt FROM stock_list WHERE name LIKE '股票%'"
        
        updated = db.query_one(sql_updated)['cnt']
        not_updated = db.query_one(sql_not_updated)['cnt']
        
        print(f"\n统计结果:")
        print(f"  已更新名称: {updated} 只")
        print(f"  未更新名称: {not_updated} 只")
        
    finally:
        db.close()


if __name__ == '__main__':
    update_names()