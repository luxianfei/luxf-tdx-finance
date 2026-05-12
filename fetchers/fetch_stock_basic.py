#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票基本信息采集脚本
功能：从通达信服务器获取股票列表和基本信息（包括行业）
"""

import os
import sys
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pytdx.hq import TdxHq_API
    HAS_PYTDX = True
except ImportError:
    HAS_PYTDX = False
    print("pytdx未安装")

from config import MYSQL_CONFIG as DB_CONFIG
from database.mysql_client import MySQLClient

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 通达信公共服务器列表
TDX_SERVERS = [
    ('183.239.132.37', 7709),
    ('183.239.132.38', 7709),
    ('183.239.134.137', 7709),
    ('180.153.18.178', 7709),
    ('202.108.253.131', 7709),
    ('61.152.107.141', 7709),
    ('202.99.192.68', 7709),
]


def get_stock_basic_from_tdx(api, market: int, start: int = 0) -> list:
    """
    从通达信服务器获取股票基本信息
    
    Args:
        api: TdxHq_API实例
        market: 市场代码 (0=深圳, 1=上海)
        start: 起始位置
        
    Returns:
        list: 股票基本信息列表
    """
    try:
        data = api.get_security_list(market, start)
        return data if data else []
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return []


def connect_to_server(api) -> bool:
    """
    尝试连接到通达信服务器
    
    Args:
        api: TdxHq_API实例
        
    Returns:
        bool: 是否连接成功
    """
    for host, port in TDX_SERVERS:
        try:
            if api.connect(host, port):
                logger.info(f"成功连接到服务器 {host}:{port}")
                return True
        except Exception as e:
            logger.debug(f"连接 {host}:{port} 失败: {e}")
    
    logger.error("无法连接到任何通达信服务器")
    return False


def fetch_and_save_stock_basic(db_client: MySQLClient):
    """
    采集并保存股票基本信息
    
    Args:
        db_client: 数据库客户端
    """
    if not HAS_PYTDX:
        logger.error("pytdx未安装，无法采集股票基本信息")
        return
    
    api = TdxHq_API()
    
    try:
        if not connect_to_server(api):
            return
        
        total_count = 0
        
        # 采集上海市场股票
        logger.info("开始采集上海市场股票...")
        sh_count = 0
        start = 0
        while True:
            stocks = get_stock_basic_from_tdx(api, 1, start)
            if not stocks:
                break
            
            for stock in stocks:
                stock_data = {
                    'code': stock['code'],
                    'name': stock['name'],
                    'market': 1,
                    'industry': stock.get('industry', ''),
                    'list_date': None,
                    'status': 'active'
                }
                
                # 尝试解析上市日期
                list_date = stock.get('list_date')
                if list_date and isinstance(list_date, int) and list_date > 0:
                    stock_data['list_date'] = list_date
                
                db_client.execute("""
                    INSERT INTO stock_list (code, name, market, industry, list_date, status)
                    VALUES (%(code)s, %(name)s, %(market)s, %(industry)s, %(list_date)s, %(status)s)
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        industry = VALUES(industry),
                        list_date = VALUES(list_date)
                """, stock_data)
                sh_count += 1
            
            start += len(stocks)
            logger.info(f"上海市场已采集 {sh_count} 只股票")
        
        # 采集深圳市场股票
        logger.info("开始采集深圳市场股票...")
        sz_count = 0
        start = 0
        while True:
            stocks = get_stock_basic_from_tdx(api, 0, start)
            if not stocks:
                break
            
            for stock in stocks:
                stock_data = {
                    'code': stock['code'],
                    'name': stock['name'],
                    'market': 0,
                    'industry': stock.get('industry', ''),
                    'list_date': None,
                    'status': 'active'
                }
                
                # 尝试解析上市日期
                list_date = stock.get('list_date')
                if list_date and isinstance(list_date, int) and list_date > 0:
                    stock_data['list_date'] = list_date
                
                db_client.execute("""
                    INSERT INTO stock_list (code, name, market, industry, list_date, status)
                    VALUES (%(code)s, %(name)s, %(market)s, %(industry)s, %(list_date)s, %(status)s)
                    ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        industry = VALUES(industry),
                        list_date = VALUES(list_date)
                """, stock_data)
                sz_count += 1
            
            start += len(stocks)
            logger.info(f"深圳市场已采集 {sz_count} 只股票")
        
        db_client.commit()
        total_count = sh_count + sz_count
        logger.info(f"股票基本信息采集完成，共 {total_count} 只股票")
        
    finally:
        api.disconnect()


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("股票基本信息采集脚本启动")
    logger.info("=" * 60)
    
    db_client = MySQLClient(DB_CONFIG)
    
    try:
        fetch_and_save_stock_basic(db_client)
    except Exception as e:
        logger.error(f"采集过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_client.close()


if __name__ == '__main__':
    main()