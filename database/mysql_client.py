#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL 客户端封装
支持：连接管理、CRUD操作、批量插入、事务处理
"""

import pymysql
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging

from .schema import init_database, create_tables

logger = logging.getLogger(__name__)


class MySQLClient:
    """MySQL 数据库客户端"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化 MySQL 客户端

        Args:
            config: MySQL 连接配置
                - host: 172.19.6.48
                - port: 3306
                - user: tdxuser
                - password: TdxUser2026!
                - database: tdxdb
                - charset: utf8mb4
        """
        self.config = config
        self._conn: Optional[pymysql.Connection] = None

    def connect(self) -> pymysql.Connection:
        """建立数据库连接"""
        if self._conn is None or not self._conn.open:
            self._conn = pymysql.connect(
                host=self.config["host"],
                port=self.config["port"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                charset=self.config.get("charset", "utf8mb4"),
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
            )
        return self._conn

    def close(self):
        """关闭数据库连接"""
        if self._conn and self._conn.open:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def execute(self, sql: str, params: tuple = None) -> int:
        """执行 SQL（增删改），返回影响行数"""
        conn = self.connect()
        with conn.cursor() as cursor:
            return cursor.execute(sql, params)

    def query_one(self, sql: str, params: tuple = None) -> Optional[Dict]:
        """查询单条记录"""
        conn = self.connect()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def query_all(self, sql: str, params: tuple = None) -> List[Dict]:
        """查询所有记录"""
        conn = self.connect()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def query_column(self, sql: str, params: tuple = None) -> List[Any]:
        """查询单列数据"""
        conn = self.connect()
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return [row[0] for row in cursor.fetchall()]

    def commit(self):
        """提交事务"""
        if self._conn and self._conn.open:
            self._conn.commit()

    def rollback(self):
        """回滚事务"""
        if self._conn and self._conn.open:
            self._conn.rollback()

    # ============================================================
    # 财务数据操作
    # ============================================================

    def insert_quarterly_finance(self, data: Dict) -> bool:
        """
        插入单条季度财务数据（INSERT OR UPDATE）

        Args:
            data: 财务数据字典

        Returns:
            bool: 是否成功
        """
        sql = """
        INSERT INTO quarterly_finance (
            code, report_date, year, quarter,
            eps_basic, book_value_per_share, cashflow_ps,
            undistributed_ps, reserve_ps,
            net_profit_attr_w, kfe_np_quarterly_w,
            revenue_quarterly_w, cost_quarterly_w,
            gross_margin, roe_diluted,
            revenue_yoy, kfe_np_yoy,
            kfe_np_ttm_w, total_shares
        ) VALUES (
            %(code)s, %(report_date)s, %(year)s, %(quarter)s,
            %(eps_basic)s, %(book_value_per_share)s, %(cashflow_ps)s,
            %(undistributed_ps)s, %(reserve_ps)s,
            %(net_profit_attr_w)s, %(kfe_np_quarterly_w)s,
            %(revenue_quarterly_w)s, %(cost_quarterly_w)s,
            %(gross_margin)s, %(roe_diluted)s,
            %(revenue_yoy)s, %(kfe_np_yoy)s,
            %(kfe_np_ttm_w)s, %(total_shares)s
        )
        ON DUPLICATE KEY UPDATE
            eps_basic = VALUES(eps_basic),
            book_value_per_share = VALUES(book_value_per_share),
            cashflow_ps = VALUES(cashflow_ps),
            undistributed_ps = VALUES(undistributed_ps),
            reserve_ps = VALUES(reserve_ps),
            net_profit_attr_w = VALUES(net_profit_attr_w),
            kfe_np_quarterly_w = VALUES(kfe_np_quarterly_w),
            revenue_quarterly_w = VALUES(revenue_quarterly_w),
            cost_quarterly_w = VALUES(cost_quarterly_w),
            gross_margin = VALUES(gross_margin),
            roe_diluted = VALUES(roe_diluted),
            revenue_yoy = VALUES(revenue_yoy),
            kfe_np_yoy = VALUES(kfe_np_yoy),
            kfe_np_ttm_w = VALUES(kfe_np_ttm_w),
            total_shares = VALUES(total_shares)
        """
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.execute(sql, data)
            self.commit()
            return True
        except Exception as e:
            logger.error(f"插入财务数据失败: {e}")
            self.rollback()
            return False

    def batch_insert_quarterly_finance(self, data_list: List[Dict]) -> int:
        """
        批量插入季度财务数据

        Args:
            data_list: 财务数据列表

        Returns:
            int: 成功插入的行数
        """
        if not data_list:
            return 0

        sql = """
        INSERT INTO quarterly_finance (
            code, report_date, year, quarter,
            eps_basic, book_value_per_share, cashflow_ps,
            undistributed_ps, reserve_ps,
            net_profit_attr_w, kfe_np_quarterly_w,
            revenue_quarterly_w, cost_quarterly_w,
            gross_margin, roe_diluted,
            revenue_yoy, kfe_np_yoy,
            kfe_np_ttm_w, total_shares
        ) VALUES (
            %(code)s, %(report_date)s, %(year)s, %(quarter)s,
            %(eps_basic)s, %(book_value_per_share)s, %(cashflow_ps)s,
            %(undistributed_ps)s, %(reserve_ps)s,
            %(net_profit_attr_w)s, %(kfe_np_quarterly_w)s,
            %(revenue_quarterly_w)s, %(cost_quarterly_w)s,
            %(gross_margin)s, %(roe_diluted)s,
            %(revenue_yoy)s, %(kfe_np_yoy)s,
            %(kfe_np_ttm_w)s, %(total_shares)s
        )
        ON DUPLICATE KEY UPDATE
            eps_basic = VALUES(eps_basic),
            book_value_per_share = VALUES(book_value_per_share),
            cashflow_ps = VALUES(cashflow_ps),
            undistributed_ps = VALUES(undistributed_ps),
            reserve_ps = VALUES(reserve_ps),
            net_profit_attr_w = VALUES(net_profit_attr_w),
            kfe_np_quarterly_w = VALUES(kfe_np_quarterly_w),
            revenue_quarterly_w = VALUES(revenue_quarterly_w),
            cost_quarterly_w = VALUES(cost_quarterly_w),
            gross_margin = VALUES(gross_margin),
            roe_diluted = VALUES(roe_diluted),
            revenue_yoy = VALUES(revenue_yoy),
            kfe_np_yoy = VALUES(kfe_np_yoy),
            kfe_np_ttm_w = VALUES(kfe_np_ttm_w),
            total_shares = VALUES(total_shares)
        """
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.executemany(sql, data_list)
            self.commit()
            return len(data_list)
        except Exception as e:
            logger.error(f"批量插入财务数据失败: {e}")
            self.rollback()
            return 0

    def get_quarterly_finance(self, code: str, report_date: int) -> Optional[Dict]:
        """获取单条季度财务数据"""
        sql = "SELECT * FROM quarterly_finance WHERE code = %s AND report_date = %s"
        return self.query_one(sql, (code, report_date))

    def get_stock_finance_history(self, code: str, limit: int = 16) -> List[Dict]:
        """获取股票历史财务数据"""
        sql = """
        SELECT * FROM quarterly_finance
        WHERE code = %s
        ORDER BY report_date DESC
        LIMIT %s
        """
        return self.query_all(sql, (code, limit))

    def get_all_codes(self) -> List[str]:
        """获取所有股票代码"""
        sql = "SELECT DISTINCT code FROM stock_list WHERE status = 'active'"
        return self.query_column(sql)

    def get_missing_codes(self, all_codes: List[str]) -> List[str]:
        """获取尚未采集的股票代码"""
        if not all_codes:
            return []

        placeholders = ",".join(["%s"] * len(all_codes))
        sql = f"""
        SELECT code FROM quarterly_finance
        WHERE code IN ({placeholders})
        GROUP BY code
        HAVING COUNT(DISTINCT report_date) >= 8
        """
        fetched_codes = set(self.query_column(sql, tuple(all_codes)))
        return [code for code in all_codes if code not in fetched_codes]

    def log_fetch(self, code: str, report_date: int, status: str,
                  message: str = "", rows_affected: int = 0):
        """记录采集日志"""
        sql = """
        INSERT INTO fetch_log (code, report_date, status, message, rows_affected, completed_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """
        try:
            self.execute(sql, (code, report_date, status, message, rows_affected))
            self.commit()
        except Exception as e:
            logger.error(f"记录日志失败: {e}")

    def get_fetch_stats(self) -> Dict:
        """获取采集统计信息"""
        sql = """
        SELECT
            COUNT(DISTINCT code) AS total_codes,
            COUNT(*) AS total_records,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS success_count,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed_count
        FROM fetch_log
        """
        return self.query_one(sql) or {}

    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        sql = """
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = %s AND table_name = %s
        """
        result = self.query_one(sql, (self.config["database"], table_name))
        return result["COUNT(*)"] > 0 if result else False

    def init_tables(self):
        """初始化数据库表结构"""
        init_database(self.config)
        create_tables(self.config)

    # ============================================================
    # 季度指标表操作
    # ============================================================

    def insert_quarterly_metrics(self, data: Dict) -> bool:
        """
        插入单条季度指标数据

        Args:
            data: 指标数据字典

        Returns:
            bool: 是否成功
        """
        sql = """
        INSERT INTO quarterly_metrics (
            code, report_date, year, quarter,
            gross_margin, revenue_yoy, net_profit_yoy, kfe_np_yoy, kfe_np_ttm_w,
            revenue_quarterly_w, net_profit_attr_w, kfe_np_quarterly_w,
            eps_basic, roe_diluted
        ) VALUES (
            %(code)s, %(report_date)s, %(year)s, %(quarter)s,
            %(gross_margin)s, %(revenue_yoy)s, %(net_profit_yoy)s, %(kfe_np_yoy)s, %(kfe_np_ttm_w)s,
            %(revenue_quarterly_w)s, %(net_profit_attr_w)s, %(kfe_np_quarterly_w)s,
            %(eps_basic)s, %(roe_diluted)s
        )
        ON DUPLICATE KEY UPDATE
            gross_margin = VALUES(gross_margin),
            revenue_yoy = VALUES(revenue_yoy),
            net_profit_yoy = VALUES(net_profit_yoy),
            kfe_np_yoy = VALUES(kfe_np_yoy),
            kfe_np_ttm_w = VALUES(kfe_np_ttm_w),
            revenue_quarterly_w = VALUES(revenue_quarterly_w),
            net_profit_attr_w = VALUES(net_profit_attr_w),
            kfe_np_quarterly_w = VALUES(kfe_np_quarterly_w),
            eps_basic = VALUES(eps_basic),
            roe_diluted = VALUES(roe_diluted)
        """
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.execute(sql, data)
            self.commit()
            return True
        except Exception as e:
            logger.error(f"插入季度指标失败: {e}")
            self.rollback()
            return False

    def batch_insert_quarterly_metrics(self, data_list: List[Dict]) -> int:
        """
        批量插入季度指标数据

        Args:
            data_list: 指标数据列表

        Returns:
            int: 成功插入的行数
        """
        if not data_list:
            return 0

        sql = """
        INSERT INTO quarterly_metrics (
            code, report_date, year, quarter,
            gross_margin, revenue_yoy, net_profit_yoy, kfe_np_yoy, kfe_np_ttm_w,
            revenue_quarterly_w, net_profit_attr_w, kfe_np_quarterly_w,
            eps_basic, roe_diluted
        ) VALUES (
            %(code)s, %(report_date)s, %(year)s, %(quarter)s,
            %(gross_margin)s, %(revenue_yoy)s, %(net_profit_yoy)s, %(kfe_np_yoy)s, %(kfe_np_ttm_w)s,
            %(revenue_quarterly_w)s, %(net_profit_attr_w)s, %(kfe_np_quarterly_w)s,
            %(eps_basic)s, %(roe_diluted)s
        )
        ON DUPLICATE KEY UPDATE
            gross_margin = VALUES(gross_margin),
            revenue_yoy = VALUES(revenue_yoy),
            net_profit_yoy = VALUES(net_profit_yoy),
            kfe_np_yoy = VALUES(kfe_np_yoy),
            kfe_np_ttm_w = VALUES(kfe_np_ttm_w),
            revenue_quarterly_w = VALUES(revenue_quarterly_w),
            net_profit_attr_w = VALUES(net_profit_attr_w),
            kfe_np_quarterly_w = VALUES(kfe_np_quarterly_w),
            eps_basic = VALUES(eps_basic),
            roe_diluted = VALUES(roe_diluted)
        """
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.executemany(sql, data_list)
            self.commit()
            return len(data_list)
        except Exception as e:
            logger.error(f"批量插入季度指标失败: {e}")
            self.rollback()
            return 0

    def get_quarterly_metrics(self, code: str, limit: int = 16) -> List[Dict]:
        """
        获取股票季度指标数据

        Args:
            code: 股票代码
            limit: 返回记录数

        Returns:
            List[Dict]: 指标数据列表
        """
        sql = """
        SELECT
            code, report_date, year, quarter,
            gross_margin, revenue_yoy, net_profit_yoy, kfe_np_yoy, kfe_np_ttm_w,
            revenue_quarterly_w, net_profit_attr_w, kfe_np_quarterly_w,
            eps_basic, roe_diluted
        FROM quarterly_metrics
        WHERE code = %s
        ORDER BY report_date DESC
        LIMIT %s
        """
        return self.query_all(sql, (code, limit))

    # ============================================================
    # F10数据操作
    # ============================================================

    def insert_company_profile(self, data: Dict) -> bool:
        """
        插入公司概况数据（INSERT OR UPDATE）

        Args:
            data: 公司概况数据字典

        Returns:
            bool: 是否成功
        """
        sql = """
        INSERT INTO company_profile (
            code, company_name, english_name, industry, business_scope,
            list_date, reg_capital, chairman, general_manager,
            address, phone, website
        ) VALUES (
            %(code)s, %(company_name)s, %(english_name)s, %(industry)s, %(business_scope)s,
            %(list_date)s, %(reg_capital)s, %(chairman)s, %(general_manager)s,
            %(address)s, %(phone)s, %(website)s
        )
        ON DUPLICATE KEY UPDATE
            company_name = VALUES(company_name),
            english_name = VALUES(english_name),
            industry = VALUES(industry),
            business_scope = VALUES(business_scope),
            list_date = VALUES(list_date),
            reg_capital = VALUES(reg_capital),
            chairman = VALUES(chairman),
            general_manager = VALUES(general_manager),
            address = VALUES(address),
            phone = VALUES(phone),
            website = VALUES(website)
        """
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.execute(sql, data)
            self.commit()
            return True
        except Exception as e:
            logger.error(f"插入公司概况失败: {e}")
            self.rollback()
            return False

    def get_company_profile(self, code: str) -> Optional[Dict]:
        """获取公司概况"""
        sql = "SELECT * FROM company_profile WHERE code = %s"
        return self.query_one(sql, (code,))

    def insert_market_snapshot(self, data: Dict) -> bool:
        """
        插入行情快照数据（INSERT OR UPDATE）

        Args:
            data: 行情快照数据字典

        Returns:
            bool: 是否成功
        """
        sql = """
        INSERT INTO market_snapshot (
            code, price, `change`, change_percent, turnover_rate,
            market_cap, pe, pb, volume, amount,
            high, low, open, prev_close
        ) VALUES (
            %(code)s, %(price)s, %(change)s, %(change_percent)s, %(turnover_rate)s,
            %(market_cap)s, %(pe)s, %(pb)s, %(volume)s, %(amount)s,
            %(high)s, %(low)s, %(open)s, %(prev_close)s
        )
        ON DUPLICATE KEY UPDATE
            price = VALUES(price),
            `change` = VALUES(`change`),
            change_percent = VALUES(change_percent),
            turnover_rate = VALUES(turnover_rate),
            market_cap = VALUES(market_cap),
            pe = VALUES(pe),
            pb = VALUES(pb),
            volume = VALUES(volume),
            amount = VALUES(amount),
            high = VALUES(high),
            low = VALUES(low),
            open = VALUES(open),
            prev_close = VALUES(prev_close),
            snapshot_time = NOW()
        """
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.execute(sql, data)
            self.commit()
            return True
        except Exception as e:
            logger.error(f"插入行情快照失败: {e}")
            self.rollback()
            return False

    def get_market_snapshot(self, code: str) -> Optional[Dict]:
        """获取行情快照"""
        sql = "SELECT * FROM market_snapshot WHERE code = %s"
        return self.query_one(sql, (code,))

    def batch_insert_profit_forecast(self, data_list: List[Dict]) -> int:
        """
        批量插入盈利预测数据

        Args:
            data_list: 盈利预测数据列表

        Returns:
            int: 成功插入的行数
        """
        if not data_list:
            return 0

        sql = """
        INSERT INTO profit_forecast (
            code, year, forecast_type, eps, net_profit, revenue, roe, book_value_ps
        ) VALUES (
            %(code)s, %(year)s, %(forecast_type)s, %(eps)s, %(net_profit)s, %(revenue)s, %(roe)s, %(book_value_ps)s
        )
        ON DUPLICATE KEY UPDATE
            forecast_type = VALUES(forecast_type),
            eps = VALUES(eps),
            net_profit = VALUES(net_profit),
            revenue = VALUES(revenue),
            roe = VALUES(roe),
            book_value_ps = VALUES(book_value_ps)
        """
        try:
            conn = self.connect()
            with conn.cursor() as cursor:
                cursor.executemany(sql, data_list)
            self.commit()
            return len(data_list)
        except Exception as e:
            logger.error(f"批量插入盈利预测失败: {e}")
            self.rollback()
            return 0

    def get_profit_forecast(self, code: str) -> List[Dict]:
        """获取盈利预测数据"""
        sql = """
        SELECT * FROM profit_forecast
        WHERE code = %s
        ORDER BY year ASC
        """
        return self.query_all(sql, (code,))
