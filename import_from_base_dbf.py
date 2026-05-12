#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从通达信 base.dbf 文件导入股票数据
"""

import os
import sys
import logging
from datetime import datetime

sys.path.insert(0, '.')

from config import MYSQL_CONFIG, TDX_DIR
from database.mysql_client import MySQLClient
from dbfread import DBF

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def import_from_base_dbf():
    """从 base.dbf 导入数据"""
    base_dbf = os.path.join(TDX_DIR, "T0002", "hq_cache", "base.dbf")
    
    if not os.path.exists(base_dbf):
        logger.error(f"文件不存在: {base_dbf}")
        return
    
    logger.info(f"正在读取 base.dbf 文件...")
    table = DBF(base_dbf, encoding='gbk')
    
    db_client = MySQLClient(MYSQL_CONFIG)
    conn = db_client.connect()
    
    try:
        with conn.cursor() as cursor:
            count = 0
            for record in table:
                code = str(record.get('GPDM', '')).zfill(6)
                
                # 只处理 A 股股票
                if not (code.startswith('60') or code.startswith('68') or 
                        code.startswith('00') or code.startswith('30')):
                    continue
                
                # 检查数据库中是否存在该股票
                cursor.execute("SELECT COUNT(*) as cnt FROM stock_list WHERE code = %s", (code,))
                exists = cursor.fetchone()['cnt'] > 0
                
                if exists:
                    # 更新股票信息
                    sql = """
                    UPDATE stock_list 
                    SET 
                        industry = %s,
                        list_date = %s,
                        updated_at = %s
                    WHERE code = %s
                    """
                    industry = record.get('HY')
                    list_date = record.get('SSDATE')
                    current_time = datetime.now()
                    
                    # 转换日期格式 (YYYYMMDD -> YYYYMMDD 整数)
                    try:
                        list_date = int(list_date) if list_date else None
                    except:
                        list_date = None
                    
                    cursor.execute(sql, (industry, list_date, current_time, code))
                    count += 1
            
            db_client.commit()
            logger.info(f"成功更新 {count} 条股票记录")
        
    finally:
        db_client.close()


def check_stock_list_status():
    """检查 stock_list 表的状态"""
    db_client = MySQLClient(MYSQL_CONFIG)
    
    total = db_client.query_one("SELECT COUNT(*) as cnt FROM stock_list")
    updated = db_client.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE name NOT LIKE '股票%'")
    not_updated = db_client.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE name LIKE '股票%'")
    
    logger.info(f"\n股票列表状态:")
    logger.info(f"  总数: {total['cnt']}")
    logger.info(f"  已更新名称: {updated['cnt']}")
    logger.info(f"  未更新名称: {not_updated['cnt']}")
    
    db_client.close()


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("从 base.dbf 导入股票数据")
    logger.info("=" * 60)
    
    import_from_base_dbf()
    check_stock_list_status()