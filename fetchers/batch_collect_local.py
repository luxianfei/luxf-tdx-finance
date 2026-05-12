#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量采集脚本 - 从通达信本地目录采集所有A股数据
功能：
1. 从通达信本地lday文件获取股票列表
2. 批量采集财务数据、公司概况、盈利预测
"""

import os
import sys
import logging
from datetime import datetime
import glob

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TDX_DIR, MYSQL_CONFIG
from database.mysql_client import MySQLClient
from fetchers.f10_collector import F10Collector
from fetchers.finance_collector import FinanceCollector

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def get_stock_codes_from_local():
    """
    从通达信本地目录获取股票代码列表
    从 vipdoc/sh/lday 和 vipdoc/sz/lday 目录读取.day文件
    """
    codes = set()
    
    # 上海市场
    sh_dir = os.path.join(TDX_DIR, "vipdoc", "sh", "lday")
    if os.path.exists(sh_dir):
        for file_name in os.listdir(sh_dir):
            if file_name.endswith(".day"):
                # 文件名格式：sh600001.day
                code = file_name.replace("sh", "").replace(".day", "")
                if code.isdigit() and len(code) == 6:
                    codes.add(code)
    
    # 深圳市场
    sz_dir = os.path.join(TDX_DIR, "vipdoc", "sz", "lday")
    if os.path.exists(sz_dir):
        for file_name in os.listdir(sz_dir):
            if file_name.endswith(".day"):
                # 文件名格式：sz000001.day
                code = file_name.replace("sz", "").replace(".day", "")
                if code.isdigit() and len(code) == 6:
                    codes.add(code)
    
    # 北京市场（精选层）
    bj_dir = os.path.join(TDX_DIR, "vipdoc", "bj", "lday")
    if os.path.exists(bj_dir):
        for file_name in os.listdir(bj_dir):
            if file_name.endswith(".day"):
                # 文件名格式：bj899050.day
                code = file_name.replace("bj", "").replace(".day", "")
                if code.isdigit() and len(code) == 6:
                    codes.add(code)
    
    return sorted(list(codes))


def init_stock_list(db_client, codes):
    """
    初始化股票列表到数据库
    """
    if not codes:
        return 0
    
    # 使用SQL语句直接插入
    sql = """
    INSERT INTO stock_list (code, name, market, industry, list_date, status)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        name = VALUES(name),
        market = VALUES(market),
        status = VALUES(status)
    """
    
    data = []
    for code in codes:
        market = 1 if code.startswith('6') else 0  # 上海=1, 深圳=0
        data.append((code, f'股票{code}', market, None, None, 'active'))
    
    try:
        conn = db_client.connect()
        with conn.cursor() as cursor:
            cursor.executemany(sql, data)
        db_client.commit()
        logger.info(f"初始化股票列表完成，共 {len(codes)} 只股票")
        return len(codes)
    except Exception as e:
        logger.error(f"初始化股票列表失败: {e}")
        db_client.rollback()
        return 0


def batch_collect_finance_data(db_client, codes, fetch_forecast=True):
    """
    批量采集财务数据
    """
    from models.finance_models import to_mysql_dict
    
    fetcher = FinanceCollector()
    collector = F10Collector(db_client=db_client)
    
    stats = {
        'total': len(codes),
        'finance_success': 0,
        'finance_failed': 0,
        'profile_success': 0,
        'profile_failed': 0,
        'forecast_success': 0,
        'forecast_failed': 0,
        'errors': []
    }
    
    for i, code in enumerate(codes, 1):
        logger.info(f"[{i}/{len(codes)}] 正在采集 {code}...")
        
        try:
            # 采集财务数据（季度指标）
            try:
                result = fetcher.collect_to_dict(code)
                if result and result['record_count'] > 0:
                    df = result['dataframe']
                    records = to_mysql_dict(df, code)
                    count = db_client.batch_insert_quarterly_finance(records)
                    if count > 0:
                        stats['finance_success'] += 1
                    else:
                        stats['finance_failed'] += 1
                else:
                    stats['finance_failed'] += 1
            except Exception as e:
                logger.warning(f"采集财务数据失败 {code}: {e}")
                stats['finance_failed'] += 1
            
            # 采集公司概况（行业、主营业务等）
            try:
                profile_ok = collector.save_company_profile(code)
                if profile_ok:
                    stats['profile_success'] += 1
                else:
                    stats['profile_failed'] += 1
            except Exception as e:
                logger.warning(f"采集公司概况失败 {code}: {e}")
                stats['profile_failed'] += 1
            
            # 采集盈利预测
            if fetch_forecast:
                try:
                    forecast_ok = collector.save_profit_forecast(code)
                    if forecast_ok:
                        stats['forecast_success'] += 1
                    else:
                        stats['forecast_failed'] += 1
                except Exception as e:
                    logger.warning(f"采集盈利预测失败 {code}: {e}")
                    stats['forecast_failed'] += 1
                    
        except Exception as e:
            logger.error(f"采集 {code} 发生异常: {e}")
            stats['errors'].append({'code': code, 'error': str(e)})
    
    return stats


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("批量采集脚本启动 - 从通达信本地目录采集")
    logger.info("=" * 60)
    
    # 检查通达信目录
    if not os.path.exists(TDX_DIR):
        logger.error(f"通达信目录不存在: {TDX_DIR}")
        return
    
    # 获取本地股票列表
    logger.info(f"正在从 {TDX_DIR} 获取股票列表...")
    codes = get_stock_codes_from_local()
    logger.info(f"共发现 {len(codes)} 只股票")
    
    if not codes:
        logger.warning("未找到股票数据，请确保通达信已下载行情数据")
        return
    
    # 创建数据库客户端
    db_client = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 初始化股票列表
        logger.info("初始化股票列表...")
        init_stock_list(db_client, codes)
        
        # 询问用户是否采集盈利预测
        fetch_forecast = True
        try:
            user_input = input("是否采集盈利预测数据（耗时较长）？(y/n): ").strip().lower()
            if user_input == 'n':
                fetch_forecast = False
        except:
            pass
        
        # 询问用户是否限制采集数量
        limit_count = None
        try:
            user_input = input(f"是否限制采集数量？输入数字或回车采集全部（共{len(codes)}只）: ").strip()
            if user_input.isdigit():
                limit_count = int(user_input)
                codes = codes[:limit_count]
                logger.info(f"限制采集前 {limit_count} 只股票")
        except:
            pass
        
        # 开始批量采集
        logger.info(f"开始批量采集 {len(codes)} 只股票数据...")
        start_time = datetime.now()
        stats = batch_collect_finance_data(db_client, codes, fetch_forecast)
        end_time = datetime.now()
        
        # 输出统计结果
        logger.info("=" * 60)
        logger.info("采集完成！")
        logger.info(f"耗时: {(end_time - start_time).total_seconds():.2f} 秒")
        logger.info("=" * 60)
        logger.info(f"财务数据: {stats['finance_success']}/{stats['total']} 成功")
        logger.info(f"公司概况: {stats['profile_success']}/{stats['total']} 成功")
        if fetch_forecast:
            logger.info(f"盈利预测: {stats['forecast_success']}/{stats['total']} 成功")
        
        if stats['errors']:
            logger.error(f"采集异常的股票数量: {len(stats['errors'])}")
            
    except Exception as e:
        logger.error(f"采集过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_client.close()


if __name__ == '__main__':
    main()