#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 stock_list 表中的无效记录
"""

import sys
import logging

sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def clean_stock_list():
    """清理无效的股票记录"""
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 查询总数
        total = db.query_one("SELECT COUNT(*) as cnt FROM stock_list")
        logger.info(f"清理前总记录数: {total['cnt']}")
        
        # 删除"其他"分类的记录（不符合A股代码规则的）
        delete_sql = """
        DELETE FROM stock_list 
        WHERE code NOT LIKE '6%' 
          AND code NOT LIKE '0%' 
          AND code NOT LIKE '3%' 
          AND code NOT LIKE '68%'
        """
        
        conn = db.connect()
        with conn.cursor() as cursor:
            cursor.execute(delete_sql)
            deleted = cursor.rowcount
            conn.commit()
        
        logger.info(f"删除了 {deleted} 条无效记录")
        
        # 查询清理后的总数
        total_after = db.query_one("SELECT COUNT(*) as cnt FROM stock_list")
        logger.info(f"清理后总记录数: {total_after['cnt']}")
        
        # 按市场分类统计
        by_market = db.query_all("""
            SELECT 
                CASE 
                    WHEN code LIKE '6%' THEN '上海主板'
                    WHEN code LIKE '0%' THEN '深圳主板'
                    WHEN code LIKE '3%' THEN '创业板'
                    WHEN code LIKE '68%' THEN '科创板'
                    ELSE '其他'
                END as market,
                COUNT(*) as cnt
            FROM stock_list
            GROUP BY 
                CASE 
                    WHEN code LIKE '6%' THEN '上海主板'
                    WHEN code LIKE '0%' THEN '深圳主板'
                    WHEN code LIKE '3%' THEN '创业板'
                    WHEN code LIKE '68%' THEN '科创板'
                    ELSE '其他'
                END
            ORDER BY cnt DESC
        """)
        logger.info("\n按市场分类:")
        for row in by_market:
            logger.info(f"  {row['market']}: {row['cnt']} 只")
        
        # 查询需要更新名称的股票
        need_update = db.query_one("SELECT COUNT(*) as cnt FROM stock_list WHERE name LIKE '股票%'")
        logger.info(f"\n需要更新名称的股票: {need_update['cnt']} 只")
        
    finally:
        db.close()


if __name__ == '__main__':
    clean_stock_list()