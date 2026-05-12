#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量采集所有股票的盈利预测数据
遍历 stock_list 表中的每只股票，采集盈利预测数据到 profit_forecast 表中
"""

import sys
import time
import logging
from datetime import datetime

sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG
from fetchers.f10_collector import F10Collector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(f'profit_forecast_collect_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def batch_collect_profit_forecast():
    """批量采集盈利预测数据"""
    db_client = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取所有股票代码
        sql = "SELECT code, name FROM stock_list ORDER BY code"
        stocks = db_client.query_all(sql)
        
        total_count = len(stocks)
        logger.info(f"开始批量采集盈利预测数据，共 {total_count} 只股票")
        
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        # 创建采集器
        collector = F10Collector(db_client=db_client)
        
        for index, stock in enumerate(stocks, 1):
            code = stock['code']
            name = stock['name']
            
            try:
                # 检查是否已有数据（避免重复采集）
                existing = db_client.query_one(
                    "SELECT COUNT(*) as cnt FROM profit_forecast WHERE code = %s",
                    (code,)
                )
                
                if existing and existing['cnt'] > 0:
                    logger.info(f"[{index}/{total_count}] {code} {name} - 已有数据，跳过")
                    skip_count += 1
                    continue
                
                # 采集盈利预测数据
                logger.info(f"[{index}/{total_count}] {code} {name} - 开始采集")
                start_time = time.time()
                
                success = collector.save_profit_forecast(code)
                
                elapsed = time.time() - start_time
                
                if success:
                    logger.info(f"[{index}/{total_count}] {code} {name} - 采集成功 (耗时: {elapsed:.2f}s)")
                    success_count += 1
                else:
                    logger.warning(f"[{index}/{total_count}] {code} {name} - 采集失败 (耗时: {elapsed:.2f}s)")
                    fail_count += 1
                
                # 每采集10只股票后短暂休息，避免请求过于频繁
                if index % 10 == 0:
                    time.sleep(2)
                    logger.info(f"已完成 {index}/{total_count}，休息2秒...")
                
            except Exception as e:
                logger.error(f"[{index}/{total_count}] {code} {name} - 采集异常: {e}")
                fail_count += 1
        
        # 输出统计结果
        logger.info("=" * 60)
        logger.info("批量采集完成！")
        logger.info(f"股票总数: {total_count}")
        logger.info(f"成功采集: {success_count}")
        logger.info(f"采集失败: {fail_count}")
        logger.info(f"跳过(已有数据): {skip_count}")
        logger.info("=" * 60)
        
    finally:
        db_client.close()

if __name__ == '__main__':
    batch_collect_profit_forecast()