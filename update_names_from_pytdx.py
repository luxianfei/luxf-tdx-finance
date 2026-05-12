#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 pytdx 获取股票名称并更新数据库
"""

import sys
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

sys.path.insert(0, '.')

from config import MYSQL_CONFIG
from database.mysql_client import MySQLClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

db_lock = Lock()


def get_stock_names_from_pytdx():
    """从 pytdx 获取股票名称"""
    from utils.stock_list import StockListHelper
    
    helper = StockListHelper()
    return helper.get_codes_with_names()


def update_stock_names(db_client, name_dict):
    """更新数据库中的股票名称"""
    if not name_dict:
        return 0
    
    sql = """
    UPDATE stock_list 
    SET name = %s 
    WHERE code = %s AND name LIKE '股票%%'
    """
    
    updated_count = 0
    total_count = len(name_dict)
    
    conn = db_client.connect()
    
    try:
        with conn.cursor() as cursor:
            for i, (code, name) in enumerate(name_dict.items(), 1):
                cursor.execute(sql, (name, code))
                if cursor.rowcount > 0:
                    updated_count += 1
            
            db_client.commit()
        
        logger.info(f"更新完成！共更新 {updated_count}/{total_count} 条记录")
        return updated_count
    
    finally:
        db_client.close()


def main():
    logger.info("=" * 60)
    logger.info("从 pytdx 更新股票名称")
    logger.info("=" * 60)
    
    # 获取股票名称
    name_dict = get_stock_names_from_pytdx()
    
    if not name_dict:
        logger.error("无法获取股票名称数据")
        return
    
    # 更新数据库
    db_client = MySQLClient(MYSQL_CONFIG)
    update_stock_names(db_client, name_dict)
    
    # 显示统计结果
    updated = db_client.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE name NOT LIKE '股票%'")
    not_updated = db_client.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE name LIKE '股票%'")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"统计结果:")
    logger.info(f"  已更新名称: {updated['cnt']} 只")
    logger.info(f"  未更新名称: {not_updated['cnt']} 只")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()