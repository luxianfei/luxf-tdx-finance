#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
通达信 F10 财务数据采集工具
================================================================================
功能：从通达信本地数据（gpcw文件）中提取 A 股财务指标，与通达信 F10 界面完全一致
支持：单股票查询 / 全A股批量采集 / MySQL 8.0 存储

作者：WorkBuddy
版本：v4.0 (2026-05-08)
================================================================================
"""

import os

# ============================================================
# 基础配置
# ============================================================
# 通达信安装目录
TDX_DIR = "D:/SoftwaresInstalled/dycy"

# 数据缓存目录
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
FINANCE_DIR = os.path.join(WORK_DIR, "finance_data")
os.makedirs(FINANCE_DIR, exist_ok=True)

# MySQL 数据库配置（根据实际情况修改）
MYSQL_CONFIG = {
    "host": "172.19.6.48",
    "port": 3306,
    "user": "tdxuser",
    "password": "TdxUser2026!",
    "database": "tdxdb",
    "charset": "utf8mb4",
}

# 采集配置
MAX_QUARTERS = 16  # 最大采集季度数
DEFAULT_MARKET = 1  # 1=上海, 0=深圳

# gpcw 文件列表（按时间升序排列）
# 这些文件从 pytdx 自动下载到 FINANCE_DIR
GPCW_FILE_LIST = [
    "gpcw20210331.zip", "gpcw20210630.zip", "gpcw20210930.zip",
    "gpcw20211231.zip", "gpcw20220331.zip", "gpcw20220630.zip",
    "gpcw20220930.zip", "gpcw20221231.zip", "gpcw20230331.zip",
    "gpcw20230630.zip", "gpcw20230930.zip", "gpcw20231231.zip",
    "gpcw20240331.zip", "gpcw20240630.zip", "gpcw20240930.zip",
    "gpcw20241231.zip", "gpcw20250331.zip", "gpcw20250630.zip",
    "gpcw20250930.zip", "gpcw20251231.zip", "gpcw20260331.zip",
]


# ============================================================
# gpcw 字段映射（已验证）
# ============================================================
# gpcw 文件中每个股票记录包含 584 个 float 字段
# 以下为已验证的字段映射（列号从 1 开始）

GPCW_FIELD_MAP = {
    # 每股指标
    "eps_basic":        1,    # 每股基本收益(元)     → d[0]
    "eps_diluted":      2,    # 每股稀释收益(元)     → d[1]
    "book_value_per_share": 3,  # 每股净资产(元)      → d[2]
    "undistributed_ps": 5,    # 每股未分配利润(元)   → d[4]
    "reserve_ps":       6,    # 每股公积金(元)       → d[5]
    "cashflow_ps":      7,    # 每股经营现金流(元)   → d[6]

    # 利润指标
    "net_profit_attr":  96,   # 归属净利润(元)      → d[95]
    "kfe_np_quarterly": 233,  # 扣非净利润_单季(元)  → d[232]

    # 营收指标
    "revenue_quarterly": 312, # 单季度营收(元)       → d[311]
    "cost_quarterly":    328, # 单季度成本(元)       → d[327]
    "revenue_yoy_base":  230, # 营收同比基数(元)     → d[229] - 用于计算营收YoY

    # 收益率指标
    "roe_diluted":       281, # ROE摊薄(%)          → d[280]
}


# ============================================================
# 数据库表名
# ============================================================
TABLE_QUARTERLY_FINANCE = "quarterly_finance"
TABLE_STOCK_LIST = "stock_list"
TABLE_FETCH_LOG = "fetch_log"


# ============================================================
# 辅助函数
# ============================================================
def get_report_date(file_name: str) -> str:
    """从 gpcw 文件名提取报告期（如 gpcw20241231.zip → 20241231）"""
    return file_name.replace("gpcw", "").replace(".zip", "")


def parse_report_date(date_str: str) -> tuple:
    """解析报告期字符串，返回 (年份, 季度)"""
    year = int(date_str[:4])
    month = int(date_str[4:6])
    quarter_map = {3: 1, 6: 2, 9: 3}
    quarter = quarter_map.get(month, 4)
    return year, quarter
