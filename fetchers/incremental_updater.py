#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量行情信息更新器
从通达信本地数据中读取最新行情信息，更新到数据库
"""

import os
import struct
import time
from typing import Dict, Optional, Callable, List, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from config import TDX_DIR, MYSQL_CONFIG
from database import MySQLClient
from fetchers.f10_collector import F10Collector


class IncrementalUpdater:
    """增量行情信息更新器"""

    MAX_WORKERS = 16  # 增加线程数

    def __init__(self):
        self.tdx_dir = TDX_DIR
        self.vipdoc_dir = os.path.join(self.tdx_dir, "vipdoc")
        self.db_client = MySQLClient(MYSQL_CONFIG)
        self.f10_collector = F10Collector(db_client=self.db_client)
        self._progress_lock = Lock()
        self._batch_size = 100  # 增大批量大小
        self._total_shares_cache = {}  # 缓存总股本数据

    def get_market_prefix(self, code: str) -> str:
        """获取市场前缀 (sh/sz)"""
        return 'sh' if code.startswith('6') or code.startswith('68') else 'sz'

    def _load_total_shares_cache(self):
        """预加载所有股票的总股本数据到缓存"""
        try:
            from dbfread import DBF
            base_dbf = os.path.join(self.tdx_dir, "T0002", "hq_cache", "base.dbf")
            if os.path.exists(base_dbf):
                table = DBF(base_dbf, encoding='gbk')
                for record in table:
                    code = record.get('GPDM')
                    total_shares = record.get('ZGB')
                    if code and total_shares:
                        try:
                            self._total_shares_cache[code] = float(total_shares)
                        except:
                            pass
                print(f"已缓存 {len(self._total_shares_cache)} 只股票的总股本数据")
        except Exception as e:
            print(f"加载总股本缓存失败: {e}")

    def _get_total_shares(self, code: str) -> Optional[float]:
        """从缓存获取总股本"""
        if not self._total_shares_cache:
            self._load_total_shares_cache()
        return self._total_shares_cache.get(code)

    def read_latest_quote_from_tdx(self, code: str) -> Optional[Dict]:
        """从通达信.day文件读取最新行情数据"""
        market = self.get_market_prefix(code)
        day_file = os.path.join(self.vipdoc_dir, market, "lday", f"{market}{code}.day")

        if not os.path.exists(day_file):
            return None

        try:
            with open(day_file, 'rb') as f:
                f.seek(0, 2)
                file_size = f.tell()
                record_count = file_size // 32

                if record_count == 0:
                    return None

                f.seek(-32, 2)
                data = f.read(32)

                prev_close = None
                if record_count > 1:
                    f.seek(-64, 2)
                    prev_data = f.read(32)
                    if len(prev_data) == 32:
                        prev_close = struct.unpack('<I', prev_data[16:20])[0] / 100.0

            if len(data) != 32:
                return None

            open_price = struct.unpack('<I', data[4:8])[0] / 100.0
            high_price = struct.unpack('<I', data[8:12])[0] / 100.0
            low_price = struct.unpack('<I', data[12:16])[0] / 100.0
            close_price = struct.unpack('<I', data[16:20])[0] / 100.0
            volume = struct.unpack('<I', data[20:24])[0]
            amount = struct.unpack('<I', data[24:28])[0] / 1000000.0

            if close_price <= 0 or close_price > 10000:
                return None

            return {
                'code': code,
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'price': round(close_price, 2),
                'prev_close': round(prev_close, 2) if prev_close else None,
                'volume': volume,
                'amount': round(amount, 2)
            }
        except Exception as e:
            return None

    def get_stock_list(self) -> list:
        """获取所有股票列表"""
        sql = "SELECT code, name FROM stock_list WHERE status = 'active'"
        results = self.db_client.query_all(sql)
        return [{'code': row['code'], 'name': row['name']} for row in results]

    def _process_single_snapshot(self, stock: dict) -> Optional[Tuple]:
        """处理单只股票的市场快照"""
        code = stock['code']
        try:
            quote_data = self.read_latest_quote_from_tdx(code)
            if quote_data:
                prev_close = quote_data.get('prev_close') or quote_data['price']
                change = round(quote_data['price'] - prev_close, 2)
                change_percent = round((change / prev_close) * 100, 2) if prev_close != 0 else 0

                total_shares = self._get_total_shares(code)
                market_cap = 0
                if total_shares:
                    market_cap = quote_data['price'] * total_shares / 10000

                return (
                    code, quote_data['price'], change, change_percent, market_cap,
                    quote_data['volume'], quote_data['amount'],
                    quote_data['high'], quote_data['low'], quote_data['open'], prev_close
                )
            return None
        except Exception as e:
            return None

    def update_market_snapshot(self, callback: Callable = None) -> Dict:
        """更新市场快照数据（使用多线程并行处理）"""
        stocks = self.get_stock_list()
        total_count = len(stocks)
        success_count = 0
        fail_count = 0

        if callback:
            callback(0, f"开始更新市场快照，共 {total_count} 只股票")

        # 预加载总股本缓存
        self._load_total_shares_cache()

        batch_data = []
        results = []

        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = [executor.submit(self._process_single_snapshot, stock) for stock in stocks]

            completed = 0
            for future in as_completed(futures):
                completed += 1
                result = future.result()
                if result:
                    results.append(result)

                if callback and completed % 50 == 0:
                    progress = (completed / total_count) * 50
                    message = f"市场快照：已读取 {completed}/{total_count} 只股票数据"
                    callback(progress, message)

        if callback:
            callback(50, "正在批量写入数据库...")

        # 批量插入数据库
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

        for i in range(0, len(results), self._batch_size):
            batch = results[i:i + self._batch_size]
            try:
                self.db_client.executemany(sql, batch)
                success_count += len(batch)
            except Exception as e:
                fail_count += len(batch)
                print(f"批量插入失败: {e}")

            if callback:
                progress = 50 + (success_count / total_count) * 40
                message = f"市场快照：已写入 {success_count}/{total_count} 只股票"
                callback(progress, message)

        self.db_client.commit()

        if callback:
            callback(100, f"市场快照更新完成！")

        return {
            'total': total_count,
            'success': success_count,
            'failed': fail_count,
            'message': f"市场快照更新完成！共处理 {total_count} 只股票，成功 {success_count} 只，失败 {fail_count} 只"
        }

    def _fetch_single_forecast(self, code: str) -> Tuple[str, Optional[Dict]]:
        """单线程获取单只股票的盈利预测数据"""
        try:
            forecast_result = self.f10_collector.get_profit_forecast(code)
            if forecast_result and forecast_result.get('data'):
                return (code, forecast_result['data'])
            return (code, None)
        except Exception as e:
            return (code, None)

    def update_profit_forecast(self, force_update=False, callback: Callable = None) -> Dict:
        """更新盈利预测数据（使用多线程并行获取）"""
        stocks = self.get_stock_list()
        total_count = len(stocks)
        success_count = 0
        fail_count = 0
        skipped_count = 0

        if callback:
            callback(0, f"开始更新盈利预测，共 {total_count} 只股票（并行获取中...）")

        forecast_results = []

        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            futures = {executor.submit(self._fetch_single_forecast, stock['code']): stock['code'] for stock in stocks}

            completed = 0
            for future in as_completed(futures):
                completed += 1
                code, forecast_data = future.result()
                forecast_results.append((code, forecast_data))

                if callback and completed % 50 == 0:
                    progress = (completed / total_count) * 40
                    message = f"盈利预测：已获取 {completed}/{total_count} 只股票数据"
                    callback(progress, message)

        if callback:
            callback(40, "正在解析并写入数据库...")

        current_year = datetime.now().year
        batch_data = []

        for code, forecast_list in forecast_results:
            try:
                if not forecast_list:
                    skipped_count += 1
                    continue

                parsed_any = False

                for forecast_item in forecast_list:
                    year_data = {}
                    for key, value in forecast_item.items():
                        if isinstance(key, str) and len(key) >= 5 and key.startswith('20') and key[4] == '年':
                            year_data[key] = value

                    if year_data:
                        latest_year = None
                        for year_key in sorted(year_data.keys(), reverse=True):
                            if year_key.startswith('20'):
                                latest_year = int(year_key[:4])
                                break

                        if latest_year and latest_year >= current_year - 2:
                            eps = None
                            revenue = None
                            net_profit = None
                            pe = None

                            indicator = str(forecast_item.get('财务指标', ''))
                            for key, value in year_data.items():
                                try:
                                    val = float(value) if value and value != '---' else None
                                except:
                                    val = None

                                if '每股收益' in indicator:
                                    eps = val
                                elif '营业收入' in indicator:
                                    revenue = val
                                elif '净利润' in indicator:
                                    net_profit = val
                                elif '市盈率' in indicator:
                                    pe = val

                            if eps is not None or revenue is not None or net_profit is not None:
                                batch_data.append((
                                    code, '', latest_year, 4,
                                    eps, revenue, net_profit, pe
                                ))
                                parsed_any = True

                                if len(batch_data) >= self._batch_size:
                                    self._insert_forecast_batch(batch_data)
                                    success_count += len(batch_data)
                                    batch_data = []

                if not parsed_any:
                    skipped_count += 1

            except Exception as e:
                fail_count += 1

        if batch_data:
            self._insert_forecast_batch(batch_data)
            success_count += len(batch_data)

        self.db_client.commit()

        if callback:
            callback(100, f"盈利预测更新完成！")

        return {
            'total': total_count,
            'success': success_count,
            'failed': fail_count,
            'skipped': skipped_count,
            'message': f"盈利预测更新完成！共处理 {total_count} 只股票，成功 {success_count} 条"
        }

    def _insert_forecast_batch(self, batch_data: List[tuple]):
        """批量插入盈利预测数据"""
        if not batch_data:
            return

        sql = """
            INSERT INTO profit_forecast
            (code, name, report_year, report_quarter, eps, revenue,
             net_profit, pe, update_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
            name = VALUES(name), eps = VALUES(eps), revenue = VALUES(revenue),
            net_profit = VALUES(net_profit), pe = VALUES(pe), update_time = NOW()
        """
        try:
            self.db_client.executemany(sql, batch_data)
        except Exception as e:
            print(f"批量插入盈利预测失败: {e}")

    def close(self):
        """关闭数据库连接"""
        self.db_client.close()


if __name__ == '__main__':
    updater = IncrementalUpdater()

    print("=== 测试市场快照更新 ===")
    start = time.time()
    result = updater.update_market_snapshot()
    print(f"耗时: {time.time() - start:.2f}秒")
    print(result['message'])

    print("\n=== 测试盈利预测更新 ===")
    start = time.time()
    result = updater.update_profit_forecast()
    print(f"耗时: {time.time() - start:.2f}秒")
    print(result['message'])

    updater.close()
