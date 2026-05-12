#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F10数据采集脚本
功能：批量采集股票F10数据（公司概况、行情快照、盈利预测）并存储到数据库
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.config import DB_CONFIG
from database.mysql_client import MySQLClient
from fetchers.f10_collector import F10Collector

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def fetch_f10_for_codes(codes: list, db_client: MySQLClient, collect_market: bool = True):
    """
    批量采集F10数据
    
    Args:
        codes: 股票代码列表
        db_client: 数据库客户端
        collect_market: 是否采集行情数据（需要通达信客户端运行）
        
    Returns:
        dict: 采集统计结果
    """
    collector = F10Collector(db_client=db_client)
    
    stats = {
        'total': len(codes),
        'profile_success': 0,
        'profile_failed': 0,
        'market_success': 0,
        'market_failed': 0,
        'forecast_success': 0,
        'forecast_failed': 0,
        'errors': []
    }
    
    for i, code in enumerate(codes, 1):
        logger.info(f"[{i}/{len(codes)}] 正在采集 {code}...")
        
        try:
            # 采集公司概况
            profile_ok = collector.save_company_profile(code)
            if profile_ok:
                stats['profile_success'] += 1
            else:
                stats['profile_failed'] += 1
            
            # 采集行情数据
            if collect_market:
                market_ok = collector.save_market_snapshot(code)
                if market_ok:
                    stats['market_success'] += 1
                else:
                    stats['market_failed'] += 1
            
            # 采集盈利预测
            forecast_ok = collector.save_profit_forecast(code)
            if forecast_ok:
                stats['forecast_success'] += 1
            else:
                stats['forecast_failed'] += 1
                
        except Exception as e:
            logger.error(f"采集 {code} 失败: {e}")
            stats['errors'].append({'code': code, 'error': str(e)})
            stats['profile_failed'] += 1
            stats['market_failed'] += 1
            stats['forecast_failed'] += 1
    
    return stats


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("F10数据采集脚本启动")
    logger.info("=" * 60)
    
    # 创建数据库客户端
    db_client = MySQLClient(DB_CONFIG)
    
    try:
        # 获取所有股票代码
        codes = db_client.get_all_codes()
        logger.info(f"共 {len(codes)} 只股票需要采集")
        
        if not codes:
            logger.warning("未找到股票列表，请先运行数据采集")
            return
        
        # 询问用户是否采集行情数据（需要通达信客户端运行）
        collect_market = True
        try:
            user_input = input("是否采集行情数据（需要通达信客户端运行）？(y/n): ").strip().lower()
            if user_input == 'n':
                collect_market = False
        except:
            pass
        
        # 开始采集
        start_time = datetime.now()
        stats = fetch_f10_for_codes(codes, db_client, collect_market)
        end_time = datetime.now()
        
        # 输出统计结果
        logger.info("=" * 60)
        logger.info("采集完成！")
        logger.info(f"耗时: {(end_time - start_time).total_seconds():.2f} 秒")
        logger.info("=" * 60)
        logger.info(f"公司概况: {stats['profile_success']}/{stats['total']} 成功")
        if collect_market:
            logger.info(f"行情快照: {stats['market_success']}/{stats['total']} 成功")
        logger.info(f"盈利预测: {stats['forecast_success']}/{stats['total']} 成功")
        
        if stats['errors']:
            logger.error("采集失败的股票:")
            for err in stats['errors']:
                logger.error(f"  {err['code']}: {err['error']}")
                
    except Exception as e:
        logger.error(f"采集过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_client.close()


if __name__ == '__main__':
    main()