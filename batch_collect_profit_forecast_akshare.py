#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 akshare 批量采集所有股票的盈利预测数据
遍历 stock_list 表中的每只股票，采集盈利预测数据到 profit_forecast 表中
"""

import sys
import time
import logging
from datetime import datetime

sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("警告：akshare 未安装，无法采集盈利预测数据")
    sys.exit(1)

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

def fetch_all_profit_forecast_data() -> dict:
    """从akshare获取所有股票的盈利预测数据，返回字典格式"""
    try:
        df = ak.stock_profit_forecast_em()
        
        # 按股票代码分组
        result = {}
        for _, row in df.iterrows():
            code = row.get('代码', '')
            if not code:
                continue
            
            forecasts = []
            year_columns = [
                ('2025预测每股收益', 2025),
                ('2026预测每股收益', 2026),
                ('2027预测每股收益', 2027),
                ('2028预测每股收益', 2028),
            ]
            
            for col_name, year in year_columns:
                eps_val = row.get(col_name)
                if eps_val and str(eps_val) not in ['', '-', '--', 'nan', 'None']:
                    try:
                        eps = float(eps_val)
                        if eps > 0:
                            forecasts.append({
                                'year': year,
                                'eps': eps,
                                'net_profit': None,
                                'revenue': None,
                                'roe': None,
                            })
                    except:
                        pass
            
            if forecasts:
                result[code] = forecasts
        
        logger.info(f"成功从akshare获取 {len(result)} 只股票的盈利预测数据")
        return result
    except Exception as e:
        logger.error(f"获取盈利预测数据失败: {e}")
        return {}

def save_profit_forecast(db_client, code: str, forecasts: list) -> int:
    """保存盈利预测数据到数据库"""
    if not forecasts:
        return 0
    
    try:
        data_list = []
        for forecast in forecasts:
            data_item = {
                'code': code,
                'year': forecast['year'],
                'forecast_type': 'forecast',
                'eps': forecast['eps'],
                'net_profit': forecast['net_profit'],
                'revenue': forecast['revenue'],
                'roe': forecast['roe'],
                'book_value_ps': None
            }
            data_list.append(data_item)
        
        if data_list:
            count = db_client.batch_insert_profit_forecast(data_list)
            return count
        return 0
    except Exception as e:
        logger.error(f"保存 {code} 盈利预测数据失败: {e}")
        return 0

def batch_collect_profit_forecast():
    """批量采集盈利预测数据"""
    db_client = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取所有股票代码
        sql = "SELECT code, name FROM stock_list ORDER BY code"
        stocks = db_client.query_all(sql)
        
        total_count = len(stocks)
        logger.info(f"开始批量采集盈利预测数据，共 {total_count} 只股票")
        
        # 先获取所有盈利预测数据
        logger.info("正在从akshare获取盈利预测数据...")
        all_forecasts = fetch_all_profit_forecast_data()
        
        success_count = 0
        fail_count = 0
        skip_count = 0
        total_records = 0
        
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
                
                # 从已获取的数据中查找
                forecasts = all_forecasts.get(code, [])
                
                if forecasts:
                    count = save_profit_forecast(db_client, code, forecasts)
                    
                    if count > 0:
                        logger.info(f"[{index}/{total_count}] {code} {name} - 保存 {count} 条记录")
                        success_count += 1
                        total_records += count
                    else:
                        logger.warning(f"[{index}/{total_count}] {code} {name} - 未获取到有效数据")
                        fail_count += 1
                else:
                    logger.info(f"[{index}/{total_count}] {code} {name} - 无盈利预测数据")
                    fail_count += 1
                
                # 每处理50只股票后短暂休息
                if index % 50 == 0:
                    time.sleep(1)
                    logger.info(f"已完成 {index}/{total_count}")
                
            except Exception as e:
                logger.error(f"[{index}/{total_count}] {code} {name} - 处理异常: {e}")
                fail_count += 1
        
        # 输出统计结果
        logger.info("=" * 60)
        logger.info("批量采集完成！")
        logger.info(f"股票总数: {total_count}")
        logger.info(f"成功采集: {success_count}")
        logger.info(f"无数据: {fail_count}")
        logger.info(f"跳过(已有数据): {skip_count}")
        logger.info(f"新增记录数: {total_records}")
        logger.info("=" * 60)
        
    finally:
        db_client.close()

if __name__ == '__main__':
    batch_collect_profit_forecast()