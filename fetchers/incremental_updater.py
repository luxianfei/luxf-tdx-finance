#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量行情信息更新器
从通达信本地数据中读取最新行情信息，更新到数据库
"""

import os
import struct
from typing import Dict, Optional, Callable
from datetime import datetime

from config import TDX_DIR, MYSQL_CONFIG
from database import MySQLClient
from fetchers.f10_collector import F10Collector


class IncrementalUpdater:
    """增量行情信息更新器"""
    
    def __init__(self):
        self.tdx_dir = TDX_DIR
        self.vipdoc_dir = os.path.join(self.tdx_dir, "vipdoc")
        self.db_client = MySQLClient(MYSQL_CONFIG)
        self.f10_collector = F10Collector(db_client=self.db_client)
    
    def get_market_prefix(self, code: str) -> str:
        """获取市场前缀 (sh/sz)"""
        return 'sh' if code.startswith('6') or code.startswith('68') else 'sz'
    
    def read_latest_quote_from_tdx(self, code: str) -> Optional[Dict]:
        """从通达信.day文件读取最新行情数据（包含前收盘价）"""
        market = self.get_market_prefix(code)
        
        # 正确的通达信数据文件路径
        # 格式: vipdoc/{market}/lday/{market}{code}.day
        day_file = os.path.join(self.vipdoc_dir, market, "lday", f"{market}{code}.day")
        
        if not os.path.exists(day_file):
            return None
        
        try:
            with open(day_file, 'rb') as f:
                # 获取文件大小
                f.seek(0, 2)
                file_size = f.tell()
                
                # 计算有多少条记录（每条32字节）
                record_count = file_size // 32
                
                if record_count == 0:
                    return None
                
                # 读取最后一条记录（今日数据）
                f.seek(-32, 2)
                data = f.read(32)
                
                # 如果有多于1条记录，读取倒数第二条记录作为前收盘价
                prev_close = None
                if record_count > 1:
                    f.seek(-64, 2)
                    prev_data = f.read(32)
                    if len(prev_data) == 32:
                        prev_close = struct.unpack('<I', prev_data[16:20])[0] / 100.0
                
            if len(data) != 32:
                return None
            
            # 解析.day文件格式
            # 通达信.day文件格式（小端序）: 
            #   日期(4字节整数), 开盘(4字节整数/100), 最高(4字节整数/100), 最低(4字节整数/100), 
            #   收盘(4字节整数/100), 成交量(4字节整数), 成交额(4字节整数/1000000万元), 保留(4字节)
            date = struct.unpack('<I', data[0:4])[0]
            open_price = struct.unpack('<I', data[4:8])[0] / 100.0
            high_price = struct.unpack('<I', data[8:12])[0] / 100.0
            low_price = struct.unpack('<I', data[12:16])[0] / 100.0
            close_price = struct.unpack('<I', data[16:20])[0] / 100.0
            volume = struct.unpack('<I', data[20:24])[0]
            amount = struct.unpack('<I', data[24:28])[0] / 1000000.0  # 转为万元
            
            # 检查数据有效性
            if close_price <= 0 or close_price > 10000:
                return None
            
            return {
                'code': code,
                'date': str(date),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'price': round(close_price, 2),
                'prev_close': round(prev_close, 2) if prev_close else None,
                'volume': volume,
                'amount': round(amount, 2)
            }
        except Exception as e:
            print(f"读取 {code}.day 文件失败: {e}")
            return None
    
    def get_stock_list(self) -> list:
        """获取所有股票列表 - 使用正确的状态字段"""
        sql = "SELECT code, name FROM stock_list WHERE status = 'active'"
        results = self.db_client.query_all(sql)
        return [{'code': row['code'], 'name': row['name']} for row in results]
    
    def update_market_snapshot(self, callback: Callable = None) -> Dict:
        """更新市场快照数据"""
        stocks = self.get_stock_list()
        total_count = len(stocks)
        success_count = 0
        fail_count = 0
        
        if callback:
            callback(0, f"开始更新市场快照，共 {total_count} 只股票")
        
        for index, stock in enumerate(stocks, 1):
            code = stock['code']
            name = stock['name']
            
            try:
                quote_data = self.read_latest_quote_from_tdx(code)
                
                if quote_data:
                    # 使用从通达信文件中获取的前收盘价
                    prev_close = quote_data.get('prev_close') or quote_data['price']
                    change = round(quote_data['price'] - prev_close, 2)
                    change_percent = round((change / prev_close) * 100, 2) if prev_close != 0 else 0
                    
                    # 动态计算市值：市值 = 当前价格 × 总股本
                    # 从base.dbf获取总股本（单位：万股）
                    total_shares = self._get_total_shares_from_base_dbf(code)
                    market_cap = 0
                    if total_shares:
                        # 总股本单位是万股，市值 = 价格 × 总股本(万股) / 10000 = 价格 × 总股本(亿股)
                        market_cap = quote_data['price'] * total_shares / 10000  # 转换为亿元
                    
                    # 更新或插入数据（使用正确的字段名，change是MySQL保留关键字需要用反引号）
                    sql = """
                        INSERT INTO market_snapshot 
                        (code, price, `change`, change_percent, market_cap, 
                         volume, amount, high, low, open, prev_close, snapshot_time)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        ON DUPLICATE KEY UPDATE
                        price = VALUES(price), `change` = VALUES(`change`),
                        change_percent = VALUES(change_percent), market_cap = VALUES(market_cap),
                        volume = VALUES(volume), amount = VALUES(amount),
                        high = VALUES(high), low = VALUES(low), open = VALUES(open),
                        prev_close = VALUES(prev_close), snapshot_time = NOW()
                    """
                    params = (
                        code, quote_data['price'], change, change_percent, market_cap,
                        quote_data['volume'], quote_data['amount'],
                        quote_data['high'], quote_data['low'], quote_data['open'], prev_close
                    )
                    self.db_client.execute(sql, params)
                    success_count += 1
                    
                    # 每成功更新100只股票输出一次日志
                    if success_count % 100 == 0:
                        print(f"市场快照: 已成功更新 {success_count} 只股票")
                    
                    # 进度按成功数占总数的比例计算，每成功20只回调一次，让页面数字及时更新
                    if callback and success_count % 20 == 0:
                        progress = (success_count / total_count) * 100
                        message = f"市场快照: 已成功更新 {success_count}/{total_count} 只股票，失败 {fail_count} 只"
                        callback(progress, message)
                else:
                    fail_count += 1
                    
            except Exception as e:
                fail_count += 1
                print(f"更新 {code} {name} 失败: {e}")
        
        self.db_client.commit()
        
        if callback:
            callback(100, f"市场快照更新完成！")
        
        return {
            'total': total_count,
            'success': success_count,
            'failed': fail_count,
            'message': f"市场快照更新完成！共处理 {total_count} 只股票，成功 {success_count} 只，失败 {fail_count} 只"
        }
    
    def update_profit_forecast(self, force_update=False, callback: Callable = None) -> Dict:
        """更新盈利预测数据"""
        stocks = self.get_stock_list()
        total_count = len(stocks)
        success_count = 0
        fail_count = 0
        skipped_count = 0
        
        if callback:
            callback(0, f"开始更新盈利预测，共 {total_count} 只股票")
        
        for index, stock in enumerate(stocks, 1):
            code = stock['code']
            name = stock['name']
            
            try:
                # 获取最新的盈利预测数据
                forecast_result = self.f10_collector.get_profit_forecast(code)
                
                if forecast_result and forecast_result.get('data'):
                    # forecast_result['data'] 是一个列表，包含多个预测指标
                    # 需要解析这个列表并提取数据
                    forecast_list = forecast_result['data']
                    
                    # 查找包含年份和季度的数据
                    for forecast_item in forecast_list:
                        # 解析表格式数据，查找年份和预测指标
                        # 表头可能是：财务指标 | 2024 年 | 2025 年 | 2026 年
                        # 数据行可能是：每股收益 | 0.50 | 0.60 | 0.70
                        
                        # 跳过没有找到年份数据的行
                        has_year_data = False
                        year_data = {}
                        for key, value in forecast_item.items():
                            # 查找年份格式的键（如'2024 年'）
                            if isinstance(key, str) and len(key) >= 5 and key.startswith('20') and key[4] == '年':
                                has_year_data = True
                                year_data[key] = value
                        
                        if has_year_data:
                            # 找到当前年份作为报告期
                            current_year = datetime.now().year
                            # 插入数据（简化处理，只保存最新年份的数据）
                            latest_year = None
                            for year_key in sorted(year_data.keys(), reverse=True):
                                if year_key.startswith('20'):
                                    latest_year = int(year_key[:4])
                                    break
                            
                            if latest_year:
                                # 检查是否已有相同数据
                                if not force_update:
                                    sql = """
                                        SELECT id FROM profit_forecast 
                                        WHERE code = %s AND report_year = %s
                                    """
                                    exists = self.db_client.query_one(sql, (code, latest_year))
                                    if exists:
                                        skipped_count += 1
                                        continue
                                
                                # 提取预测数据（简化处理）
                                eps = None
                                revenue = None
                                net_profit = None
                                pe = None
                                
                                # 根据指标名称提取对应的预测值
                                for key, value in year_data.items():
                                    year_str = key[:4]
                                    try:
                                        val = float(value) if value and value != '---' else None
                                    except:
                                        val = None
                                    
                                    # 这里简化处理，实际需要更复杂的解析逻辑
                                    if '每股收益' in str(forecast_item.get('财务指标', '')):
                                        eps = val
                                    elif '营业收入' in str(forecast_item.get('财务指标', '')):
                                        revenue = val
                                    elif '净利润' in str(forecast_item.get('财务指标', '')):
                                        net_profit = val
                                    elif '市盈率' in str(forecast_item.get('财务指标', '')):
                                        pe = val
                                
                                # 插入数据
                                sql = """
                                    INSERT INTO profit_forecast 
                                    (code, name, report_year, report_quarter, eps, revenue, 
                                     net_profit, pe, update_time)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                                    ON DUPLICATE KEY UPDATE
                                    name = VALUES(name), eps = VALUES(eps), revenue = VALUES(revenue),
                                    net_profit = VALUES(net_profit), pe = VALUES(pe), update_time = NOW()
                                """
                                params = (
                                    code, name, latest_year, 4,  # 默认为年报
                                    eps, revenue, net_profit, pe
                                )
                                self.db_client.execute(sql, params)
                                success_count += 1
                                break  # 只处理一条数据
                        else:
                            # 没有找到年份数据，跳过
                            skipped_count += 1
                            break
                else:
                    skipped_count += 1
                
                # 每成功处理 100 只股票输出一次日志
                if success_count % 100 == 0:
                    print(f"盈利预测：已成功更新 {success_count} 只股票")
                
                # 进度按成功数占总数的比例计算，每成功 20 只回调一次，让页面数字及时更新
                if callback and success_count % 20 == 0:
                    progress = (success_count / total_count) * 100
                    message = f"盈利预测：已成功更新 {success_count}/{total_count} 只股票，失败 {fail_count} 只"
                    callback(progress, message)
                    
            except Exception as e:
                fail_count += 1
                print(f"更新 {code} {name} 盈利预测失败: {e}")
        
        self.db_client.commit()
        
        if callback:
            callback(100, f"盈利预测更新完成！")
        
        return {
            'total': total_count,
            'success': success_count,
            'failed': fail_count,
            'skipped': skipped_count,
            'message': f"盈利预测更新完成！共处理 {total_count} 只股票，成功 {success_count} 只，失败 {fail_count} 只，跳过 {skipped_count} 只"
        }
    
    def _get_total_shares_from_base_dbf(self, code: str) -> Optional[float]:
        """
        从通达信 base.dbf 文件获取总股本
        
        Args:
            code: 股票代码
        
        Returns:
            float: 总股本（万股），获取失败返回 None
        """
        try:
            from dbfread import DBF
            base_dbf = os.path.join(self.tdx_dir, "T0002", "hq_cache", "base.dbf")
            if os.path.exists(base_dbf):
                table = DBF(base_dbf, encoding='gbk')
                for record in table:
                    if record.get('GPDM') == code:
                        total_shares = record.get('ZGB')  # 总股本（万股）
                        if total_shares:
                            return float(total_shares)
        except Exception as e:
            print(f"从 base.dbf 获取 {code} 总股本失败: {e}")
        
        return None

    def close(self):
        """关闭数据库连接"""
        self.db_client.close()


if __name__ == '__main__':
    updater = IncrementalUpdater()
    
    print("=== 测试市场快照更新 ===")
    result = updater.update_market_snapshot()
    print(result['message'])
    
    print("\n=== 测试盈利预测更新 ===")
    result = updater.update_profit_forecast()
    print(result['message'])
    
    updater.close()
