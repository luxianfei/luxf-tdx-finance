#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 akshare 更新股票名称
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def update_stock_names():
    """使用 akshare 更新股票名称"""
    try:
        import akshare as ak
        
        db = MySQLClient(MYSQL_CONFIG)
        
        # 获取所有A股信息
        logger.info("正在从 akshare 获取股票信息...")
        stock_info = ak.stock_info_a_code_name()
        logger.info(f"获取到 {len(stock_info)} 只股票信息")
        
        # 构建代码到名称的映射
        name_map = {}
        for _, row in stock_info.iterrows():
            code = row['code']
            name = row['name']
            name_map[code] = name
        
        # 更新数据库
        updated = 0
        failed = 0
        
        result = db.query_all("SELECT code FROM stock_list")
        all_codes = [row['code'] for row in result]
        
        logger.info(f"开始更新 {len(all_codes)} 只股票的名称...")
        
        for code in all_codes:
            if code in name_map:
                try:
                    db.execute(
                        "UPDATE stock_list SET name = %s WHERE code = %s",
                        (name_map[code], code)
                    )
                    updated += 1
                    if updated % 500 == 0:
                        logger.info(f"已更新 {updated} 只股票名称")
                except Exception as e:
                    failed += 1
                    logger.warning(f"更新 {code} 失败: {e}")
            else:
                failed += 1
                logger.warning(f"未找到 {code} 的名称")
        
        db.close()
        
        logger.info(f"\n更新完成！成功: {updated}, 失败: {failed}")
        
    except Exception as e:
        logger.error(f"更新股票名称失败: {e}")

if __name__ == '__main__':
    update_stock_names()