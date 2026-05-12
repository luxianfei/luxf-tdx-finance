-- ============================================================
-- 股票财务数据库 Schema
-- ============================================================
-- MySQL 8.0
-- 运行方式: mysql -u root -p < schema.sql
-- ============================================================

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS stock_finance
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE stock_finance;

-- ============================================================
-- 表1: 季度财务数据（核心表）
-- ============================================================
DROP TABLE IF EXISTS quarterly_finance;

CREATE TABLE quarterly_finance (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code            VARCHAR(10) NOT NULL COMMENT '股票代码',
    report_date     INT UNSIGNED NOT NULL COMMENT '报告期 (如 20241231)',
    year            SMALLINT UNSIGNED NOT NULL COMMENT '年份',
    quarter         TINYINT UNSIGNED NOT NULL COMMENT '季度 (1-4)',

    -- 每股指标
    eps_basic           DECIMAL(10,4) COMMENT '每股基本收益(元)',
    book_value_per_share DECIMAL(10,4) COMMENT '每股净资产(元)',
    cashflow_ps         DECIMAL(10,4) COMMENT '每股经营现金流(元)',
    undistributed_ps    DECIMAL(10,4) COMMENT '每股未分配利润(元)',
    reserve_ps          DECIMAL(10,4) COMMENT '每股公积金(元)',

    -- 金额指标（万元）
    net_profit_attr_w   DECIMAL(16,2) COMMENT '归属净利润(万元)',
    kfe_np_quarterly_w  DECIMAL(16,2) COMMENT '扣非净利润_单季(万元)',
    revenue_quarterly_w DECIMAL(16,2) COMMENT '单季度营收(万元)',
    cost_quarterly_w    DECIMAL(16,2) COMMENT '单季度成本(万元)',

    -- 计算指标
    gross_margin        DECIMAL(8,4) COMMENT '毛利率(%)',
    roe_diluted         DECIMAL(8,4) COMMENT 'ROE摊薄(%)',

    -- 同比指标
    revenue_yoy         DECIMAL(12,4) COMMENT '营收同比(%)',
    kfe_np_yoy          DECIMAL(12,4) COMMENT '扣非净利润同比(%)',

    -- TTM指标
    kfe_np_ttm_w        DECIMAL(16,2) COMMENT '扣非净利润TTM(万元)',

    -- 元数据
    total_shares        DECIMAL(16,2) COMMENT '总股本(万股)',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- 唯一约束
    UNIQUE KEY uk_code_report (code, report_date),

    -- 索引
    INDEX idx_code (code),
    INDEX idx_report_date (report_date),
    INDEX idx_year_quarter (year, quarter)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='A股季度财务指标（来源：通达信F10）';


-- ============================================================
-- 表2: 股票列表
-- ============================================================
DROP TABLE IF EXISTS stock_list;

CREATE TABLE stock_list (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code            VARCHAR(10) NOT NULL COMMENT '股票代码',
    name            VARCHAR(50) NOT NULL COMMENT '股票名称',
    market          TINYINT NOT NULL COMMENT '市场 (1=上海, 0=深圳)',
    industry        VARCHAR(50) COMMENT '所属行业',
    list_date       INT UNSIGNED COMMENT '上市日期',
    status          VARCHAR(10) DEFAULT 'active' COMMENT '状态 (active/delisted)',

    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    UNIQUE KEY uk_code (code),
    INDEX idx_market (market),
    INDEX idx_industry (industry)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='A股股票列表';


-- ============================================================
-- 表3: 采集日志
-- ============================================================
DROP TABLE IF EXISTS fetch_log;

CREATE TABLE fetch_log (
    id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code            VARCHAR(10) NOT NULL COMMENT '股票代码',
    report_date     INT UNSIGNED COMMENT '报告期',
    status          VARCHAR(20) NOT NULL COMMENT '状态 (success/failed/skipped)',
    message         TEXT COMMENT '详细信息',
    rows_affected   INT DEFAULT 0 COMMENT '影响的行数',

    started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP NULL,

    INDEX idx_code (code),
    INDEX idx_status (status),
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='数据采集日志';


-- ============================================================
-- 表4: 公司概况
-- ============================================================
DROP TABLE IF EXISTS company_profile;

CREATE TABLE company_profile (
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
  COMMENT='公司概况信息（来源：通达信F10）';


-- ============================================================
-- 表5: 最新行情快照
-- ============================================================
DROP TABLE IF EXISTS market_snapshot;

CREATE TABLE market_snapshot (
    id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code                VARCHAR(10) NOT NULL COMMENT '股票代码',
    price               DECIMAL(10,2) COMMENT '最新价格',
    change              DECIMAL(10,2) COMMENT '涨跌额',
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
  COMMENT='最新行情快照（来源：通达信行情接口）';


-- ============================================================
-- 表6: 盈利预测
-- ============================================================
DROP TABLE IF EXISTS profit_forecast;

CREATE TABLE profit_forecast (
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
  COMMENT='机构盈利预测数据（来源：通达信F10研报评级）';


-- ============================================================
-- 视图: 最新季度汇总
-- ============================================================
CREATE OR REPLACE VIEW v_latest_quarter AS
SELECT
    code,
    report_date,
    year,
    quarter,
    eps_basic,
    gross_margin,
    roe_diluted,
    kfe_np_ttm_w,
    revenue_yoy,
    kfe_np_yoy,
    total_shares
FROM quarterly_finance q1
WHERE report_date = (
    SELECT MAX(report_date)
    FROM quarterly_finance q2
    WHERE q2.code = q1.code
);


-- ============================================================
-- 视图: 近4季TTM汇总
-- ============================================================
CREATE OR REPLACE VIEW v_ttm_summary AS
SELECT
    code,
    SUM(revenue_quarterly_w) AS revenue_ttm_w,
    SUM(net_profit_attr_w) AS net_profit_ttm_w,
    SUM(kfe_np_quarterly_w) AS kfe_np_ttm_w
FROM quarterly_finance
WHERE report_date >= (
    SELECT MAX(report_date) - 300 FROM quarterly_finance
)
GROUP BY code;
