#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于workbuddy方法改进的股票数据采集器
"""

import sys
import os
import struct
import json
import datetime
from pathlib import Path
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG, TDX_DIR

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False


def read_local_daily_data(code: str) -> dict:
    """
    从本地通达信日线文件读取数据
    
    Args:
        code: 股票代码 (6位数字)
        
    Returns:
        包含最新日线数据的字典
    """
    try:
        # 判断市场
        if code.startswith('6'):
            market = 'sh'
        else:
            market = 'sz'
        
        day_file = Path(TDX_DIR) / "vipdoc" / market / "lday" / f"{market}{code}.day"
        
        if not day_file.exists():
            return {}
        
        with open(day_file, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            
            # 读取最后一条记录
            f.seek(max(0, file_size - 32), 0)
            data = f.read(32)
            
            if len(data) < 32:
                return {}
            
            # 解析数据 - 使用小端序
            date_int = struct.unpack('<I', data[0:4])[0]
            open_price = struct.unpack('<I', data[4:8])[0] / 100.0
            high_price = struct.unpack('<I', data[8:12])[0] / 100.0
            low_price = struct.unpack('<I', data[12:16])[0] / 100.0
            close_price = struct.unpack('<I', data[16:20])[0] / 100.0
            amount = struct.unpack('<I', data[20:24])[0]  # 成交额（需要单位转换）
            volume = struct.unpack('<I', data[24:28])[0]  # 成交量（手）
            
            # 转换日期
            date_str = str(date_int)
            if len(date_str) == 8:
                date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                date = date_str
            
            return {
                'date': date,
                'price': close_price,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'amount': amount,
                'volume': volume
            }
            
    except Exception as e:
        return {}


def read_historical_data(code: str, days: int = 60) -> list:
    """
    读取历史日线数据
    
    Args:
        code: 股票代码
        days: 要读取的天数
        
    Returns:
        历史数据列表
    """
    try:
        if code.startswith('6'):
            market = 'sh'
        else:
            market = 'sz'
        
        day_file = Path(TDX_DIR) / "vipdoc" / market / "lday" / f"{market}{code}.day"
        
        if not day_file.exists():
            return []
        
        with open(day_file, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            
            # 读取最后N条记录
            record_size = 32
            start_pos = max(0, file_size - days * record_size)
            f.seek(start_pos, 0)
            
            data = f.read()
            
            records = []
            for i in range(0, len(data), record_size):
                if i + record_size > len(data):
                    break
                    
                record = data[i:i+record_size]
                
                date_int = struct.unpack('<I', record[0:4])[0]
                open_price = struct.unpack('<I', record[4:8])[0] / 100.0
                high_price = struct.unpack('<I', record[8:12])[0] / 100.0
                low_price = struct.unpack('<I', record[12:16])[0] / 100.0
                close_price = struct.unpack('<I', record[16:20])[0] / 100.0
                amount = struct.unpack('<I', record[20:24])[0]
                volume = struct.unpack('<I', record[24:28])[0]
                
                date_str = str(date_int)
                if len(date_str) == 8:
                    date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                else:
                    date = date_str
                
                # 计算涨跌幅
                if len(records) > 0:
                    prev_close = records[-1]['price']
                    change_pct = (close_price - prev_close) / prev_close * 100
                else:
                    change_pct = 0
                
                records.append({
                    'date': date,
                    'price': close_price,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'change_pct': change_pct,
                    'amount': amount,
                    'volume': volume
                })
            
            return records
            
    except Exception as e:
        return []


def get_realtime_from_akshare(code: str) -> dict:
    """从akshare获取实时行情"""
    if not AKSHARE_AVAILABLE:
        return {}
    
    try:
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == code]
        
        if row.empty:
            return {}
        
        row = row.iloc[0]
        
        return {
            'price': float(row.get('最新价', 0)),
            'change_pct': float(row.get('涨跌幅', 0)),
            'change_amount': float(row.get('涨跌额', 0)),
            'open': float(row.get('今开', 0)),
            'high': float(row.get('最高', 0)),
            'low': float(row.get('最低', 0)),
            'volume': int(row.get('成交量', 0)),
            'amount': float(row.get('成交额', 0)),
            'turnover': float(row.get('换手率', 0)),
            'pe_ratio': float(row.get('市盈率-动态', 0)) if str(row.get('市盈率-动态', '-')) != '-' else 0,
            'market_cap': float(row.get('总市值', 0)),
            'circulating_market_cap': float(row.get('流通市值', 0))
        }
    except Exception as e:
        return {}


def get_company_info_from_akshare(code: str) -> dict:
    """从akshare获取公司信息"""
    if not AKSHARE_AVAILABLE:
        return {}
    
    try:
        df = ak.stock_individual_info_em(symbol=code)
        
        info = {}
        for _, row in df.iterrows():
            info[row['item']] = row['value']
        
        return {
            'name': info.get('股票简称', ''),
            'industry': info.get('行业', ''),
            'main_business': info.get('主营业务', ''),
            'listing_date': info.get('上市时间', ''),
            'total_shares': info.get('总股本', ''),
            'circulating_shares': info.get('流通股本', '')
        }
    except Exception as e:
        return {}


def get_financial_data_from_akshare(code: str) -> list:
    """从akshare获取盈利预测"""
    if not AKSHARE_AVAILABLE:
        return []
    
    try:
        df = ak.stock_yjyg_em(indicator="预测指标")
        df = df[df['股票代码'] == code]
        
        forecasts = []
        for _, row in df.iterrows():
            forecast = {
                'year': str(row.get('预测年度', '')),
                'eps': str(row.get('EPS', '')),
                'revenue': str(row.get('营业总收入', '')),
                'revenue_growth': str(row.get('营业总收入同比', '')),
                'net_profit': str(row.get('净利润', '')),
                'net_profit_growth': str(row.get('净利润同比增长', '')),
                'roe': str(row.get('ROE', '')),
            }
            forecasts.append(forecast)
        
        return forecasts
    except Exception as e:
        return []


def collect_and_save_stock_data(code: str, db: MySQLClient = None):
    """
    采集并保存单只股票的数据
    
    Args:
        code: 股票代码
        db: 数据库连接（可选，不传则创建一个）
    """
    should_close_db = False
    if db is None:
        db = MySQLClient(MYSQL_CONFIG)
        should_close_db = True
    
    try:
        print(f"正在采集 {code} 的数据...")
        
        # 1. 本地日线数据
        local_daily = read_local_daily_data(code)
        historical = read_historical_data(code, 60)
        
        # 2. 从akshare获取数据
        realtime = get_realtime_from_akshare(code)
        company = get_company_info_from_akshare(code)
        forecasts = get_financial_data_from_akshare(code)
        
        # 3. 合并显示价格
        display_price = 0
        display_change_pct = 0
        if realtime.get('price', 0) > 0:
            display_price = realtime['price']
            display_change_pct = realtime['change_pct']
        elif local_daily.get('price', 0) > 0:
            display_price = local_daily['price']
        
        # 4. 保存历史K线数据
        if historical:
            for record in historical:
                try:
                    conn = db.connect()
                    sql = """
                        INSERT IGNORE INTO stock_kline 
                        (code, trade_date, open_price, high_price, low_price, close_price, volume, amount, change_pct)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    with conn.cursor() as cursor:
                        cursor.execute(sql, (
                            code,
                            record['date'],
                            record['open'],
                            record['high'],
                            record['low'],
                            record['price'],
                            record['volume'],
                            record['amount'],
                            record['change_pct']
                        ))
                    conn.commit()
                except Exception as e:
                    pass
        
        # 5. 保存公司信息
        if company:
            try:
                conn = db.connect()
                sql = """
                    INSERT INTO company_profile 
                    (code, name, industry, main_business, listing_date, total_shares, circulating_shares)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    name=VALUES(name), industry=VALUES(industry), main_business=VALUES(main_business),
                    listing_date=VALUES(listing_date), total_shares=VALUES(total_shares),
                    circulating_shares=VALUES(circulating_shares)
                """
                with conn.cursor() as cursor:
                    cursor.execute(sql, (
                        code,
                        company.get('name', ''),
                        company.get('industry', ''),
                        company.get('main_business', ''),
                        company.get('listing_date', ''),
                        company.get('total_shares', ''),
                        company.get('circulating_shares', '')
                    ))
                conn.commit()
            except Exception as e:
                pass
        
        # 6. 保存盈利预测
        if forecasts:
            try:
                conn = db.connect()
                for forecast in forecasts:
                    sql = """
                        INSERT IGNORE INTO profit_forecast 
                        (code, report_year, eps, revenue, revenue_growth, net_profit, net_profit_growth, roe)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    with conn.cursor() as cursor:
                        cursor.execute(sql, (
                            code,
                            forecast['year'],
                            forecast['eps'],
                            forecast['revenue'],
                            forecast['revenue_growth'],
                            forecast['net_profit'],
                            forecast['net_profit_growth'],
                            forecast['roe']
                        ))
                conn.commit()
            except Exception as e:
                pass
        
        # 7. 更新stock_list表
        try:
            conn = db.connect()
            update_fields = []
            update_values = []
            
            if display_price > 0:
                update_fields.append("current_price = %s")
                update_values.append(display_price)
            
            if display_change_pct != 0:
                update_fields.append("change_pct = %s")
                update_values.append(display_change_pct)
            
            if realtime.get('market_cap', 0) > 0:
                update_fields.append("market_cap = %s")
                update_values.append(realtime['market_cap'])
            
            if realtime.get('pe_ratio', 0) > 0:
                update_fields.append("pe_ratio = %s")
                update_values.append(realtime['pe_ratio'])
            
            if company.get('industry', ''):
                update_fields.append("industry = %s")
                update_values.append(company['industry'])
            
            if update_fields:
                sql = f"UPDATE stock_list SET {', '.join(update_fields)} WHERE code = %s"
                update_values.append(code)
                
                with conn.cursor() as cursor:
                    cursor.execute(sql, update_values)
                conn.commit()
        except Exception as e:
            pass
        
        print(f"  {code} 数据采集完成")
        
        return {
            'code': code,
            'local_daily': local_daily,
            'historical': historical,
            'realtime': realtime,
            'company': company,
            'forecasts': forecasts
        }
        
    finally:
        if should_close_db:
            db.close()


def batch_collect_all(limit: int = None):
    """
    批量采集所有A股数据
    
    Args:
        limit: 限制采集数量（None表示不限制）
    """
    db = MySQLClient(MYSQL_CONFIG)
    
    try:
        # 获取需要采集的股票列表
        sql = "SELECT code FROM stock_list WHERE name NOT LIKE '股票%' ORDER BY code"
        results = db.query_all(sql)
        
        if limit:
            results = results[:limit]
        
        print(f"开始采集 {len(results)} 只股票的数据...")
        
        success_count = 0
        for idx, row in enumerate(results):
            code = row['code']
            try:
                collect_and_save_stock_data(code, db)
                success_count += 1
            except Exception as e:
                print(f"  {code} 采集失败: {e}")
            
            # 每20只添加一个延迟
            if (idx + 1) % 20 == 0:
                print(f"进度: {idx + 1}/{len(results)}")
                import time
                time.sleep(2)
        
        print(f"\n采集完成！成功: {success_count}/{len(results)}")
        
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='改进的股票数据采集器')
    parser.add_argument('--code', help='采集单只股票')
    parser.add_argument('--batch', action='store_true', help='批量采集所有股票')
    parser.add_argument('--limit', type=int, help='批量采集限制数量')
    
    args = parser.parse_args()
    
    if args.code:
        collect_and_save_stock_data(args.code)
    elif args.batch:
        batch_collect_all(args.limit)
    else:
        print("请指定 --code 或 --batch 参数")
