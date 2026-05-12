#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据模型
定义数据结构，便于类型提示和序列化
"""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
import pandas as pd


@dataclass
class FinanceRecord:
    """
    季度财务数据记录

    对应 MySQL quarterly_finance 表
    """
    code: str                   # 股票代码
    report_date: int            # 报告期 (如 20241231)
    year: int                   # 年份
    quarter: int                # 季度 (1-4)

    # 每股指标
    eps_basic: Optional[float]           # 每股基本收益(元)
    book_value_per_share: Optional[float] # 每股净资产(元)
    cashflow_ps: Optional[float]          # 每股经营现金流(元)
    undistributed_ps: Optional[float]    # 每股未分配利润(元)
    reserve_ps: Optional[float]           # 每股公积金(元)

    # 金额指标（万元）
    net_profit_attr_w: Optional[float]   # 归属净利润(万元)
    kfe_np_quarterly_w: Optional[float]  # 扣非净利润_单季(万元)
    revenue_quarterly_w: Optional[float] # 单季度营收(万元)
    cost_quarterly_w: Optional[float]    # 单季度成本(万元)

    # 计算指标
    gross_margin: Optional[float]        # 毛利率(%)
    roe_diluted: Optional[float]         # ROE摊薄(%)

    # 同比指标
    revenue_yoy: Optional[float]        # 营收同比(%)
    kfe_np_yoy: Optional[float]          # 扣非净利润同比(%)

    # TTM指标
    kfe_np_ttm_w: Optional[float]       # 扣非净利润TTM(万元)

    # 元数据
    total_shares: Optional[float] = None # 总股本(万股)

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'FinanceRecord':
        """从字典创建"""
        return cls(**data)


def to_mysql_dict(df: pd.DataFrame, code: str) -> List[Dict]:
    """
    将 DataFrame 转换为 MySQL 插入格式的字典列表

    Args:
        df: 财务数据 DataFrame
        code: 股票代码

    Returns:
        List[Dict]: MySQL 插入用的字典列表
    """
    records = []
    for _, row in df.iterrows():
        record = {
            'code': code,
            'report_date': int(row['报告期']),
            'year': int(row['年份']),
            'quarter': int(row['季度']),

            'eps_basic': row.get('eps_basic'),
            'book_value_per_share': row.get('book_value_per_share'),
            'cashflow_ps': row.get('cashflow_ps'),
            'undistributed_ps': row.get('undistributed_ps'),
            'reserve_ps': row.get('reserve_ps'),

            'net_profit_attr_w': row.get('net_profit_attr_w'),
            'kfe_np_quarterly_w': row.get('kfe_np_quarterly_w'),
            'revenue_quarterly_w': row.get('revenue_quarterly_w'),
            'cost_quarterly_w': row.get('cost_quarterly_w'),

            'gross_margin': row.get('gross_margin'),
            'roe_diluted': row.get('roe_diluted'),
            'revenue_yoy': row.get('revenue_yoy'),
            'kfe_np_yoy': row.get('kfe_np_yoy'),
            'kfe_np_ttm_w': row.get('kfe_np_ttm_w'),
            'total_shares': row.get('total_shares'),
        }
        records.append(record)

    return records
