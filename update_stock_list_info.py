#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
更新 stock_list 表中的股票名称、市值、换手率等信息
"""

import os
import sys
import struct
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MYSQL_CONFIG, TDX_DIR
from database.mysql_client import MySQLClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

db_lock = Lock()


def get_market_prefix(code: str) -> str:
    """根据代码判断市场前缀"""
    if code.startswith(('6', '68')):
        return 'sh'
    return 'sz'


def read_local_daily_data(code: str) -> dict:
    """
    从本地通达信日线文件读取最新数据
    
    Returns:
        dict: 包含最新日线数据的字典
    """
    try:
        market = get_market_prefix(code)
        vipdoc_dir = os.path.join(TDX_DIR, "vipdoc")
        day_file = os.path.join(vipdoc_dir, market, "lday", f"{market}{code}.day")
        
        if not os.path.exists(day_file):
            return None
            
        with open(day_file, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            
            if file_size < 32:
                return None
                
            # 读取最后一条记录（最新数据）
            f.seek(max(0, file_size - 32), 0)
            data = f.read(32)
            
            # 解析数据 - 通达信日线文件格式
            date_int = struct.unpack('<I', data[0:4])[0]
            open_price = struct.unpack('<I', data[4:8])[0] / 100.0
            high_price = struct.unpack('<I', data[8:12])[0] / 100.0
            low_price = struct.unpack('<I', data[12:16])[0] / 100.0
            close_price = struct.unpack('<I', data[16:20])[0] / 100.0
            amount = struct.unpack('<f', data[20:24])[0]  # 成交金额（万元）
            volume = struct.unpack('<I', data[24:28])[0]  # 成交量（手）
            
            # 读取前一天的收盘价来计算涨跌幅
            if file_size >= 64:
                f.seek(max(0, file_size - 64), 0)
                prev_data = f.read(32)
                prev_close = struct.unpack('<I', prev_data[16:20])[0] / 100.0
                change_pct = (close_price - prev_close) / prev_close * 100 if prev_close > 0 else 0
            else:
                change_pct = 0
            
            return {
                'date': date_int,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'amount': amount,
                'volume': volume,
                'change_pct': round(change_pct, 2)
            }
            
    except Exception as e:
        logger.warning(f"读取本地日线数据失败 {code}: {e}")
        return None


def get_stock_name_from_pytdx(code: str) -> str:
    """使用 pytdx 获取股票名称"""
    try:
        from pytdx.hq import TdxHq_API
        
        api = TdxHq_API()
        market = 1 if code.startswith(('6', '68')) else 0
        
        # 尝试连接多个服务器
        servers = [
            ('119.147.212.81', 7709),
            ('119.147.212.80', 7709),
            ('218.75.126.9', 7709),
            ('115.238.90.165', 7709)
        ]
        
        for host, port in servers:
            try:
                if api.connect(host, port, time_out=5):
                    # 获取股票行情
                    data = api.get_security_quotes([(market, code)])
                    if data and len(data) > 0:
                        stock_name = data[0].get('stock_name', '')
                        api.disconnect()
                        return stock_name
                    api.disconnect()
            except:
                continue
                
        return None
    except Exception as e:
        logger.warning(f"获取股票名称失败 {code}: {e}")
        return None


def update_stock_info(code: str, db_client: MySQLClient) -> tuple:
    """
    更新单只股票的信息
    
    Returns:
        (code, success, message)
    """
    try:
        # 1. 获取股票名称
        stock_name = get_stock_name_from_pytdx(code)
        
        # 2. 获取最新行情数据
        daily_data = read_local_daily_data(code)
        
        # 3. 从 base.dbf 获取总股本（用于计算市值）
        total_shares = None
        try:
            from dbfread import DBF
            base_dbf = os.path.join(TDX_DIR, "T0002", "hq_cache", "base.dbf")
            if os.path.exists(base_dbf):
                table = DBF(base_dbf, encoding='gbk')
                for record in table:
                    if record.get('GPDM') == code:
                        total_shares = record.get('ZGB')  # 总股本（万股）
                        break
        except:
            pass
        
        # 4. 更新数据库
        current_time = datetime.now()
        
        with db_lock:
            conn = db_client.connect()
            with conn.cursor() as cursor:
                # 构建更新SQL
                updates = []
                params = []
                
                if stock_name:
                    updates.append("name = %s")
                    params.append(stock_name)
                
                if daily_data:
                    updates.append("current_price = %s")
                    params.append(daily_data['close'])
                    updates.append("change_pct = %s")
                    params.append(daily_data['change_pct'])
                    
                    # 计算市值 = 最新价 * 总股本
                    if total_shares and daily_data['close']:
                        market_cap = daily_data['close'] * total_shares  # 万元
                        updates.append("market_cap = %s")
                        params.append(market_cap)
                
                if updates:
                    sql = f"UPDATE stock_list SET {', '.join(updates)}, updated_at = %s WHERE code = %s"
                    params.extend([current_time, code])
                    cursor.execute(sql, params)
                    conn.commit()
                    
                    return code, True, f"名称:{stock_name or '未获取'}, 价格:{daily_data['close'] if daily_data else '未获取'}"
                else:
                    return code, False, "未获取到任何数据"
                    
    except Exception as e:
        return code, False, str(e)


def batch_update_stock_list(max_workers=20, batch_size=100):
    """批量更新 stock_list 表"""
    logger.info("=" * 60)
    logger.info("开始更新 stock_list 表")
    logger.info("=" * 60)
    
    db_client = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取所有股票代码
        result = db_client.query_all("SELECT code FROM stock_list")
        all_codes = [row['code'] for row in result]
        logger.info(f"共有 {len(all_codes)} 只股票需要更新")
        
        success_count = 0
        failed_count = 0
        batch_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(update_stock_info, code, db_client): code for code in all_codes}
            
            for i, future in enumerate(as_completed(futures), 1):
                code, success, message = future.result()
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    logger.warning(f"更新失败 {code}: {message}")
                
                # 每处理batch_size只股票，输出日志
                if i % batch_size == 0:
                    batch_count += 1
                    logger.info(f"【批次 {batch_count}】已处理 {i}/{len(all_codes)} 只股票，成功: {success_count}, 失败: {failed_count}")
                
                # 每处理1000只股票，输出一次统计
                if i % 1000 == 0:
                    logger.info(f"进度: {i}/{len(all_codes)}, 成功: {success_count}, 失败: {failed_count}")
        
        logger.info("\n" + "=" * 60)
        logger.info(f"更新完成！")
        logger.info(f"  成功: {success_count} 只股票")
        logger.info(f"  失败: {failed_count} 只股票")
        logger.info("=" * 60)
        
    finally:
        db_client.close()


def main():
    batch_update_stock_list(max_workers=20, batch_size=100)


if __name__ == '__main__':
    main()