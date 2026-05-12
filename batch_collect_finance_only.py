#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量采集财务数据（跳过名称更新）
每100只股票更新一次updated_at字段
"""

import os
import sys
import time
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MYSQL_CONFIG
from database.mysql_client import MySQLClient
from fetchers.finance_collector import FinanceCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 全局锁
db_lock = Lock()


def collect_quarterly_finance(code, finance_collector):
    """采集单只股票的季度财务数据"""
    try:
        # 采集财务数据（至少20个季度，用于计算同比）
        df, total_shares = finance_collector.collect(code, max_quarters=20)
        
        if df is None or len(df) == 0:
            return code, 0, None, "未获取到财务数据"
        
        # 转换为数据库记录格式（使用正确的字段名）
        finance_data = []
        
        for _, row in df.iterrows():
            # 解析报告日期
            report_date = int(row['报告期'])
            year = report_date // 10000
            quarter = ((report_date // 100) % 100 + 2) // 3
            
            record = {
                'code': code,
                'report_date': report_date,
                'year': year,
                'quarter': quarter,
                'eps_basic': float(row.get('eps_basic', 0)) if pd.notna(row.get('eps_basic')) else None,
                'book_value_per_share': float(row.get('book_value_per_share', 0)) if pd.notna(row.get('book_value_per_share')) else None,
                'cashflow_ps': float(row.get('cashflow_ps', 0)) if pd.notna(row.get('cashflow_ps')) else None,
                'undistributed_ps': float(row.get('undistributed_ps', 0)) if pd.notna(row.get('undistributed_ps')) else None,
                'reserve_ps': float(row.get('reserve_ps', 0)) if pd.notna(row.get('reserve_ps')) else None,
                'net_profit_attr_w': float(row.get('net_profit_attr_w', 0)) if pd.notna(row.get('net_profit_attr_w')) else None,
                'kfe_np_quarterly_w': float(row.get('kfe_np_quarterly_w', 0)) if pd.notna(row.get('kfe_np_quarterly_w')) else None,
                'revenue_quarterly_w': float(row.get('revenue_quarterly_w', 0)) if pd.notna(row.get('revenue_quarterly_w')) else None,
                'cost_quarterly_w': float(row.get('cost_quarterly_w', 0)) if pd.notna(row.get('cost_quarterly_w')) else None,
                'gross_margin': float(row.get('gross_margin', 0)) if pd.notna(row.get('gross_margin')) else None,
                'roe_diluted': float(row.get('roe_diluted', 0)) if pd.notna(row.get('roe_diluted')) else None,
                'revenue_yoy': float(row.get('revenue_yoy', 0)) if pd.notna(row.get('revenue_yoy')) else None,
                'kfe_np_yoy': float(row.get('kfe_np_yoy', 0)) if pd.notna(row.get('kfe_np_yoy')) else None,
                'kfe_np_ttm_w': float(row.get('kfe_np_ttm_w', 0)) if pd.notna(row.get('kfe_np_ttm_w')) else None,
                'total_shares': float(row.get('total_shares', 0)) if pd.notna(row.get('total_shares')) else None,
            }
            finance_data.append(record)
        
        return code, len(finance_data), finance_data, None
    
    except Exception as e:
        return code, 0, None, str(e)


def batch_collect_finance(codes, max_workers=20, batch_size=100):
    """批量采集财务数据"""
    logger.info("=" * 60)
    logger.info("开始批量采集财务数据")
    logger.info("=" * 60)
    
    db_client = MySQLClient(MYSQL_CONFIG)
    finance_collector = FinanceCollector()
    
    success_count = 0
    failed_count = 0
    total_quarters = 0
    errors = []
    batch_count = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(collect_quarterly_finance, code, finance_collector): code for code in codes}
        
        for i, future in enumerate(as_completed(futures), 1):
            code, quarters, finance_data, error = future.result()
            
            if error:
                failed_count += 1
                errors.append((code, error))
            else:
                success_count += 1
                total_quarters += quarters
                
                # 保存到数据库（使用已有的批量插入方法）
                if finance_data:
                    with db_lock:
                        inserted = db_client.batch_insert_quarterly_finance(finance_data)
            
            # 每处理batch_size只股票，更新一次updated_at并输出日志
            if i % batch_size == 0:
                batch_count += 1
                current_time = datetime.now()
                logger.info(f"【批次 {batch_count}】已采集 {i}/{len(codes)} 只股票，成功: {success_count}, 失败: {failed_count}, 总季度数: {total_quarters}")
                
                # 更新updated_at字段
                with db_lock:
                    conn = db_client.connect()
                    with conn.cursor() as cursor:
                        cursor.execute("UPDATE quarterly_finance SET updated_at = %s WHERE updated_at IS NULL", (current_time,))
                        updated_rows = cursor.rowcount
                        conn.commit()
                    logger.info(f"  └── 更新了 {updated_rows} 条记录的 updated_at 字段")
            
            # 每处理1000只股票，输出一次统计
            if i % 1000 == 0:
                logger.info(f"进度: {i}/{len(codes)}, 成功: {success_count}, 失败: {failed_count}, 总季度数: {total_quarters}")
    
    # 最后更新一次updated_at
    current_time = datetime.now()
    with db_lock:
        conn = db_client.connect()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE quarterly_finance SET updated_at = %s WHERE updated_at IS NULL", (current_time,))
            updated_rows = cursor.rowcount
            conn.commit()
        logger.info(f"最后更新了 {updated_rows} 条记录的 updated_at 字段")
    
    db_client.close()
    
    logger.info("\n" + "=" * 60)
    logger.info(f"财务数据采集完成！")
    logger.info(f"  成功: {success_count} 只股票")
    logger.info(f"  失败: {failed_count} 只股票")
    logger.info(f"  总季度数: {total_quarters}")
    logger.info("=" * 60)
    
    if errors:
        with open('finance_collect_errors.txt', 'w', encoding='utf-8') as f:
            for code, error in errors:
                f.write(f"{code}\t{error}\n")
        logger.info(f"错误信息已保存到 finance_collect_errors.txt")


def main():
    logger.info("=" * 60)
    logger.info("批量采集财务数据")
    logger.info("=" * 60)
    
    db_client = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取所有股票代码
        result = db_client.query_all("SELECT code FROM stock_list")
        all_codes = [row['code'] for row in result]
        logger.info(f"共有 {len(all_codes)} 只股票")
        
        # 采集财务数据（不限制数量，采集全部）
        batch_collect_finance(all_codes, max_workers=20, batch_size=100)
        
    finally:
        db_client.close()


if __name__ == '__main__':
    main()