#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化模块
"""

import pymysql
import logging

logger = logging.getLogger(__name__)


def init_database(config: dict):
    """
    初始化数据库（创建数据库如果不存在）

    Args:
        config: MySQL 连接配置
    """
    try:
        # 连接时不指定数据库
        conn = pymysql.connect(
            host=config["host"],
            port=config["port"],
            user=config["user"],
            password=config["password"],
            charset=config.get("charset", "utf8mb4"),
        )
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {config['database']} "
                f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
        conn.close()
        logger.info(f"数据库 {config['database']} 初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise


def create_tables(config: dict):
    """
    创建数据库表

    Args:
        config: MySQL 连接配置
    """
    conn = pymysql.connect(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        charset=config.get("charset", "utf8mb4"),
    )

    try:
        with conn.cursor() as cursor:
            # 表1: 季度财务数据
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quarterly_finance (
                    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    code            VARCHAR(10) NOT NULL COMMENT '股票代码',
                    report_date     INT UNSIGNED NOT NULL COMMENT '报告期',
                    year            SMALLINT UNSIGNED NOT NULL,
                    quarter         TINYINT UNSIGNED NOT NULL,

                    eps_basic           DECIMAL(10,4),
                    book_value_per_share DECIMAL(10,4),
                    cashflow_ps         DECIMAL(10,4),
                    undistributed_ps    DECIMAL(10,4),
                    reserve_ps          DECIMAL(10,4),

                    net_profit_attr_w   DECIMAL(16,2),
                    kfe_np_quarterly_w  DECIMAL(16,2),
                    revenue_quarterly_w DECIMAL(16,2),
                    cost_quarterly_w    DECIMAL(16,2),

                    gross_margin        DECIMAL(8,4),
                    roe_diluted         DECIMAL(8,4),
                    revenue_yoy         DECIMAL(12,4),
                    kfe_np_yoy          DECIMAL(12,4),
                    kfe_np_ttm_w        DECIMAL(16,2),
                    total_shares        DECIMAL(16,2),

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                    UNIQUE KEY uk_code_report (code, report_date),
                    INDEX idx_code (code),
                    INDEX idx_report_date (report_date)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # 表2: 股票列表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_list (
                    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    code            VARCHAR(10) NOT NULL,
                    name            VARCHAR(50) NOT NULL,
                    market          TINYINT NOT NULL,
                    industry        VARCHAR(50),
                    list_date       INT UNSIGNED,
                    status          VARCHAR(10) DEFAULT 'active',

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                    UNIQUE KEY uk_code (code),
                    INDEX idx_market (market)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # 表3: 采集日志
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fetch_log (
                    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    code            VARCHAR(10) NOT NULL,
                    report_date     INT UNSIGNED,
                    status          VARCHAR(20) NOT NULL,
                    message         TEXT,
                    rows_affected   INT DEFAULT 0,
                    started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at    TIMESTAMP NULL,

                    INDEX idx_code (code),
                    INDEX idx_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """)

            # 表4: 季度财务指标（用于前端展示）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quarterly_metrics (
                    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    code            VARCHAR(10) NOT NULL COMMENT '股票代码',
                    report_date     INT UNSIGNED NOT NULL COMMENT '报告期',
                    year            SMALLINT UNSIGNED NOT NULL COMMENT '年份',
                    quarter         TINYINT UNSIGNED NOT NULL COMMENT '季度 (1-4)',

                    -- 单季度指标
                    gross_margin        DECIMAL(8,4) COMMENT '毛利率(%)',
                    revenue_yoy         DECIMAL(12,4) COMMENT '营收同比(%)',
                    net_profit_yoy      DECIMAL(12,4) COMMENT '净利润同比(%)',
                    kfe_np_yoy          DECIMAL(12,4) COMMENT '扣非净利润同比(%)',
                    kfe_np_ttm_w        DECIMAL(16,2) COMMENT '扣非净利润TTM(万元)',

                    -- 原始数据（万元）
                    revenue_quarterly_w DECIMAL(16,2) COMMENT '单季度营收(万元)',
                    net_profit_attr_w   DECIMAL(16,2) COMMENT '归属净利润(万元)',
                    kfe_np_quarterly_w  DECIMAL(16,2) COMMENT '扣非净利润_单季(万元)',

                    -- 每股指标
                    eps_basic           DECIMAL(10,4) COMMENT '每股基本收益(元)',
                    roe_diluted         DECIMAL(8,4) COMMENT 'ROE摊薄(%)',

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                    UNIQUE KEY uk_metrics_code_report (code, report_date),
                    INDEX idx_metrics_code (code),
                    INDEX idx_metrics_report_date (report_date),
                    INDEX idx_metrics_year_quarter (year, quarter)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='季度财务指标（用于前端展示）'
            """)

            # 表5: 公司概况
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_profile (
                    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    code                VARCHAR(10) NOT NULL COMMENT '股票代码',
                    company_name        VARCHAR(100) COMMENT '公司名称',
                    english_name        VARCHAR(200) COMMENT '英文名称',
                    industry            VARCHAR(50) COMMENT '所属行业',
                    business_scope      TEXT COMMENT '主营业务',
                    list_date           INT UNSIGNED COMMENT '上市日期',
                    reg_capital         VARCHAR(50) COMMENT '注册资本',
                    chairman            VARCHAR(50) COMMENT '法人代表',
                    general_manager     VARCHAR(50) COMMENT '总经理',
                    address             VARCHAR(200) COMMENT '办公地址',
                    phone               VARCHAR(50) COMMENT '联系电话',
                    website             VARCHAR(100) COMMENT '公司网址',

                    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                    UNIQUE KEY uk_code (code),
                    INDEX idx_industry (industry)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='公司概况信息（来源：通达信F10）'
            """)

            # 表6: 最新行情快照
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_snapshot (
                    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    code                VARCHAR(10) NOT NULL COMMENT '股票代码',
                    price               DECIMAL(10,2) COMMENT '最新价格',
                    `change`            DECIMAL(10,2) COMMENT '涨跌额',
                    change_percent      DECIMAL(6,2) COMMENT '涨跌幅(%)',
                    turnover_rate       DECIMAL(6,2) COMMENT '换手率(%)',
                    market_cap          DECIMAL(15,2) COMMENT '市值(亿元)',
                    pe                  DECIMAL(10,2) COMMENT '市盈率',
                    pb                  DECIMAL(10,2) COMMENT '市净率',
                    volume              BIGINT COMMENT '成交量(手)',
                    amount              DECIMAL(15,2) COMMENT '成交额(万元)',
                    high                DECIMAL(10,2) COMMENT '最高价',
                    low                 DECIMAL(10,2) COMMENT '最低价',
                    open                DECIMAL(10,2) COMMENT '开盘价',
                    prev_close          DECIMAL(10,2) COMMENT '昨收价',

                    snapshot_time       TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '快照时间',

                    UNIQUE KEY uk_code (code),
                    INDEX idx_snapshot_time (snapshot_time)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='最新行情快照（来源：通达信行情接口）'
            """)

            # 表7: 盈利预测
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profit_forecast (
                    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    code                VARCHAR(10) NOT NULL COMMENT '股票代码',
                    year                SMALLINT UNSIGNED NOT NULL COMMENT '预测年份',
                    forecast_type       VARCHAR(20) NOT NULL COMMENT '预测类型(actual/forecast)',
                    eps                 DECIMAL(10,4) COMMENT '每股收益(元)',
                    net_profit          DECIMAL(18,2) COMMENT '归属净利润(万元)',
                    revenue             DECIMAL(18,2) COMMENT '营业总收入(万元)',
                    roe                 DECIMAL(8,2) COMMENT '净资产收益率(%)',
                    book_value_ps       DECIMAL(10,4) COMMENT '每股净资产(元)',

                    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

                    UNIQUE KEY uk_code_year (code, year),
                    INDEX idx_code (code),
                    INDEX idx_year (year)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='机构盈利预测数据（来源：通达信F10研报评级）'
            """)

            # 表8: 自选股
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS my_stock (
                    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                    code                VARCHAR(10) NOT NULL COMMENT '股票代码',
                    name                VARCHAR(50) NOT NULL COMMENT '股票名称',
                    pool_type           VARCHAR(20) NOT NULL DEFAULT 'watch' COMMENT '池类型(core/watch)',
                    notes               TEXT COMMENT '备注',
                    added_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '添加时间',
                    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

                    UNIQUE KEY uk_code_pool (code, pool_type),
                    INDEX idx_pool_type (pool_type),
                    INDEX idx_added_at (added_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                COMMENT='自选股管理（核心池/观察池）'
            """)

        conn.commit()
        logger.info("数据库表创建完成")

    finally:
        conn.close()
