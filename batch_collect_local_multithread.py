#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多线程批量采集股票名称和财务数据（基于本地通达信数据）
"""

import os
import sys
import time
import random
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MYSQL_CONFIG, TDX_DIR
from database.mysql_client import MySQLClient
from fetchers.finance_collector import FinanceCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 全局锁，用于线程安全
db_lock = Lock()


def extract_short_name(company_name):
    """从公司全称中提取简称"""
    import re
    name_clean = re.sub(r'（.*?）|\(.*?\)', '', company_name)
    
    suffixes = ['股份有限公司', '有限责任公司', '有限公司', '股份公司', '集团', '控股']
    
    for suffix in suffixes:
        if name_clean.endswith(suffix):
            name_clean = name_clean[:-len(suffix)]
            break
    
    if len(name_clean) > 6:
        name_clean = name_clean[:4]
    
    return name_clean.strip()


def get_stock_name_from_local(code):
    """从通达信本地文件获取股票名称"""
    try:
        # 尝试从 code2name.ini 文件读取（更简单）
        code2name_path = os.path.join(TDX_DIR, "T0002", "hq_cache", "code2name.ini")
        if os.path.exists(code2name_path):
            with open(code2name_path, 'r', encoding='gbk') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('['):
                        continue
                    if '=' in line:
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            record_code = parts[0].strip()
                            name = parts[1].strip()
                            if record_code == code:
                                return name
        
        # 尝试从 base.dbf 文件读取
        base_dbf = os.path.join(TDX_DIR, "T0002", "hq_cache", "base.dbf")
        if os.path.exists(base_dbf):
            from dbfread import DBF
            table = DBF(base_dbf, encoding='gbk')
            for record in table:
                record_code = str(record.get('DM', '')).zfill(6)
                if record_code == code:
                    name = record.get('NAME', '')
                    if name:
                        return extract_short_name(name)
    except Exception as e:
        logger.debug(f"从本地文件读取 {code} 名称失败: {e}")
    
    return None


def update_stock_name(code, db_client):
    """更新单只股票的名称"""
    try:
        # 从本地文件获取名称
        name = get_stock_name_from_local(code)
        
        if name:
            with db_lock:
                conn = db_client.connect()
                with conn.cursor() as cursor:
                    cursor.execute(
                        "UPDATE stock_list SET name = %s WHERE code = %s AND name LIKE '股票%%'",
                        (name, code)
                    )
                    conn.commit()
            
            return code, name, None
        else:
            return code, None, "未找到公司名称"
    
    except Exception as e:
        return code, None, str(e)


def collect_quarterly_finance(code, db_client, finance_collector):
    """采集单只股票的季度财务数据"""
    try:
        # 采集财务数据（至少20个季度，用于计算同比）
        df, total_shares = finance_collector.collect(code, max_quarters=20)
        
        if df is None or len(df) == 0:
            return code, 0, "未获取到财务数据"
        
        # 转换为数据库记录格式
        finance_data = []
        current_time = datetime.now()
        
        for _, row in df.iterrows():
            record = {
                'code': code,
                'report_date': int(row['报告期']),
                'revenue': float(row.get('revenue_quarterly_w', 0) * 10000) if pd.notna(row.get('revenue_quarterly_w')) else None,
                'net_profit': float(row.get('net_profit_attr_w', 0) * 10000) if pd.notna(row.get('net_profit_attr_w')) else None,
                'eps': float(row.get('eps_basic', 0)) if pd.notna(row.get('eps_basic')) else None,
                'roe': float(row.get('roe_diluted', 0)) if pd.notna(row.get('roe_diluted')) else None,
                'roa': None,
                'gross_margin': float(row.get('gross_margin', 0)) if pd.notna(row.get('gross_margin')) else None,
                'net_margin': None,
                'debt_ratio': None,
                'current_ratio': None,
                'quick_ratio': None,
                'operating_cash_flow': float(row.get('cashflow_ps', 0) * 10000) if pd.notna(row.get('cashflow_ps')) else None,
                'total_assets': None,
                'total_liabilities': None,
                'created_at': current_time,
                'updated_at': current_time
            }
            finance_data.append(record)
        
        # 保存到数据库
        with db_lock:
            conn = db_client.connect()
            with conn.cursor() as cursor:
                for data in finance_data:
                    sql = """
                    INSERT INTO quarterly_finance (
                        code, report_date, revenue, net_profit, eps,
                        roe, roa, gross_margin, net_margin,
                        debt_ratio, current_ratio, quick_ratio,
                        operating_cash_flow, total_assets, total_liabilities,
                        created_at, updated_at
                    ) VALUES (
                        %(code)s, %(report_date)s, %(revenue)s, %(net_profit)s, %(eps)s,
                        %(roe)s, %(roa)s, %(gross_margin)s, %(net_margin)s,
                        %(debt_ratio)s, %(current_ratio)s, %(quick_ratio)s,
                        %(operating_cash_flow)s, %(total_assets)s, %(total_liabilities)s,
                        %(created_at)s, %(updated_at)s
                    ) ON DUPLICATE KEY UPDATE
                        revenue = VALUES(revenue),
                        net_profit = VALUES(net_profit),
                        eps = VALUES(eps),
                        roe = VALUES(roe),
                        roa = VALUES(roa),
                        gross_margin = VALUES(gross_margin),
                        net_margin = VALUES(net_margin),
                        debt_ratio = VALUES(debt_ratio),
                        current_ratio = VALUES(current_ratio),
                        quick_ratio = VALUES(quick_ratio),
                        operating_cash_flow = VALUES(operating_cash_flow),
                        total_assets = VALUES(total_assets),
                        total_liabilities = VALUES(total_liabilities),
                        updated_at = VALUES(updated_at)
                    """
                    cursor.execute(sql, data)
                
                conn.commit()
        
        return code, len(finance_data), None
    
    except Exception as e:
        return code, 0, str(e)


def batch_update_names(codes, max_workers=10):
    """批量更新股票名称"""
    logger.info("=" * 60)
    logger.info("开始批量更新股票名称")
    logger.info("=" * 60)
    
    db_client = MySQLClient(MYSQL_CONFIG)
    
    success_count = 0
    failed_count = 0
    errors = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(update_stock_name, code, db_client): code for code in codes}
        
        for i, future in enumerate(as_completed(futures), 1):
            code, name, error = future.result()
            
            if error:
                failed_count += 1
                errors.append((code, error))
            else:
                success_count += 1
                if i % 100 == 0:
                    logger.info(f"[{i}/{len(codes)}] 更新 {code}: {name}")
            
            # 每处理1000只股票，输出一次统计
            if i % 1000 == 0:
                logger.info(f"进度: {i}/{len(codes)}, 成功: {success_count}, 失败: {failed_count}")
    
    db_client.close()
    
    logger.info("\n" + "=" * 60)
    logger.info(f"股票名称更新完成！")
    logger.info(f"  成功: {success_count} 只")
    logger.info(f"  失败: {failed_count} 只")
    logger.info("=" * 60)
    
    if errors:
        with open('name_update_errors.txt', 'w', encoding='utf-8') as f:
            for code, error in errors:
                f.write(f"{code}\t{error}\n")
        logger.info(f"错误信息已保存到 name_update_errors.txt")


def batch_collect_finance(codes, max_workers=10, batch_size=100):
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
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(collect_quarterly_finance, code, db_client, finance_collector): code for code in codes}
        
        for i, future in enumerate(as_completed(futures), 1):
            code, quarters, error = future.result()
            
            if error:
                failed_count += 1
                errors.append((code, error))
            else:
                success_count += 1
                total_quarters += quarters
            
            # 每处理batch_size只股票，更新一次updated_at
            if i % batch_size == 0:
                current_time = datetime.now()
                with db_lock:
                    conn = db_client.connect()
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "UPDATE quarterly_finance SET updated_at = %s WHERE updated_at IS NULL",
                            (current_time,)
                        )
                        conn.commit()
                
                logger.info(f"[{i}/{len(codes)}] 进度更新，已采集 {total_quarters} 个季度数据，成功: {success_count}, 失败: {failed_count}")
            
            # 每处理1000只股票，输出一次统计
            if i % 1000 == 0:
                logger.info(f"进度: {i}/{len(codes)}, 成功: {success_count}, 失败: {failed_count}, 总季度数: {total_quarters}")
    
    # 最后更新一次updated_at
    current_time = datetime.now()
    with db_lock:
        conn = db_client.connect()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE quarterly_finance SET updated_at = %s WHERE updated_at IS NULL", (current_time,))
            conn.commit()
    
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
    logger.info("多线程批量采集股票数据（基于本地通达信数据）")
    logger.info("=" * 60)
    
    db_client = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取需要更新名称的股票代码
        result = db_client.query_all("SELECT code FROM stock_list WHERE name LIKE '股票%%'")
        codes = [row['code'] for row in result]
        logger.info(f"发现 {len(codes)} 只股票需要更新名称")
        
        if codes:
            # 更新股票名称
            batch_update_names(codes, max_workers=20)
        
        # 获取所有股票代码
        result = db_client.query_all("SELECT code FROM stock_list")
        all_codes = [row['code'] for row in result]
        logger.info(f"共有 {len(all_codes)} 只股票")
        
        # 询问用户是否限制采集数量
        limit_count = None
        try:
            user_input = input(f"是否限制采集数量？输入数字或回车采集全部（共{len(all_codes)}只）: ").strip()
            if user_input.isdigit():
                limit_count = int(user_input)
                all_codes = all_codes[:limit_count]
                logger.info(f"限制采集前 {limit_count} 只股票")
        except:
            pass
        
        # 采集财务数据
        batch_collect_finance(all_codes, max_workers=20, batch_size=100)
        
    finally:
        db_client.close()


if __name__ == '__main__':
    main()