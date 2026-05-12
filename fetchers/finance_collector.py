#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据采集器
功能：从 gpcw 文件中采集 A 股财务指标，计算 YoY 和 TTM
"""

import os
import glob
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
import numpy as np

from fetchers.gpcw_parser import GpcwParser
from config import (
    FINANCE_DIR, GPCW_FILE_LIST, GPCW_FIELD_MAP, TDX_DIR,
    parse_report_date, get_report_date
)

logger = logging.getLogger(__name__)


class FinanceCollector:
    """
    财务数据采集器

    从通达信 gpcw 文件中提取股票财务指标，包括：
    - 每股指标（EPS、净资产、经营现金流等）
    - 利润指标（归属净利润、扣非净利润）
    - 营收指标（营收、成本、毛利率）
    - 收益率指标（ROE）
    - 同比指标（营收YoY、扣非YoY）
    - TTM 指标（扣非净利润TTM）
    """

    def __init__(self, cache_dir: str = FINANCE_DIR):
        """
        初始化采集器

        Args:
            cache_dir: gpcw 文件缓存目录
        """
        self.parser = GpcwParser(cache_dir)
        self.cache_dir = cache_dir
        self.gpcw_files = self._scan_gpcw_files()

    def _scan_gpcw_files(self) -> List[str]:
        """扫描缓存目录中的 gpcw 文件"""
        files = []
        for pattern in GPCW_FILE_LIST:
            path = os.path.join(self.cache_dir, pattern)
            if os.path.exists(path):
                files.append(path)

        # 如果缓存为空，尝试添加下载候选
        if not files:
            for f in GPCW_FILE_LIST:
                files.append(os.path.join(self.cache_dir, f))

        return sorted(files, key=lambda x: os.path.basename(x))

    def collect(self, code: str, max_quarters: int = 16,
                auto_download: bool = True) -> Tuple[pd.DataFrame, Optional[float]]:
        """
        采集指定股票近 N 个季度的完整 F10 财务数据

        Args:
            code: 股票代码（如 "688456"）
            max_quarters: 最大采集季度数（默认 16）
            auto_download: 是否自动下载缺失的 gpcw 文件

        Returns:
            Tuple[pd.DataFrame, Optional[float]]: (财务数据 DataFrame, 总股本)
        """
        logger.info(f"开始采集 {code} 财务数据...")

        # 1. 收集所有 gpcw 数据（从最新到最旧遍历）
        all_data = {}
        available_files = []

        # 倒序遍历所有gpcw文件（从最新开始）
        for fname in reversed(GPCW_FILE_LIST):
            fpath = os.path.join(self.cache_dir, fname)
            if os.path.exists(fpath):
                records = self.parser.parse_file(fpath, code)
                if records:
                    all_data.update(records)
                    available_files.append(fpath)
            elif auto_download:
                # 尝试下载
                downloaded = self._download_gpcw(fname)
                if downloaded and os.path.exists(downloaded):
                    records = self.parser.parse_file(downloaded, code)
                    if records:
                        all_data.update(records)
                        available_files.append(downloaded)

        if not all_data:
            raise ValueError(f"未找到股票 {code} 的任何财务数据！")

        # 2. 按日期升序排列，然后从最新季度开始取 max_quarters 个季度
        sorted_dates = sorted(all_data.keys())
        logger.info(f"获取 {len(sorted_dates)} 个季度数据")
        
        # 从最新季度开始往前取 max_quarters 个季度
        if len(sorted_dates) > max_quarters:
            sorted_dates = sorted_dates[-max_quarters:]
        
        logger.info(f"使用最新 {len(sorted_dates)} 个季度数据（从 {sorted_dates[0]} 到 {sorted_dates[-1]}）")

        # 3. 提取字段并计算指标
        rows = []
        total_shares = None
        
        # 首先尝试从 base.dbf 获取总股本（单位：万股）
        total_shares = self._get_total_shares_from_base_dbf(code)
        
        # 如果从 base.dbf 获取失败，后续会通过计算估算

        for idx, rdate in enumerate(sorted_dates):
            data = all_data[rdate]
            year, quarter = parse_report_date(str(rdate))

            # 提取原始字段
            raw = {
                'eps':           GpcwParser.get_field(data, GPCW_FIELD_MAP['eps_basic']),
                'book_value':    GpcwParser.get_field(data, GPCW_FIELD_MAP['book_value_per_share']),
                'cashflow_ps':   GpcwParser.get_field(data, GPCW_FIELD_MAP['cashflow_ps']),
                'undist_ps':     GpcwParser.get_field(data, GPCW_FIELD_MAP['undistributed_ps']),
                'reserve_ps':   GpcwParser.get_field(data, GPCW_FIELD_MAP['reserve_ps']),
                'net_profit':    GpcwParser.get_field(data, GPCW_FIELD_MAP['net_profit_attr']),
                'kfe_np':        GpcwParser.get_field(data, GPCW_FIELD_MAP['kfe_np_quarterly']),
                'revenue':       GpcwParser.get_field(data, GPCW_FIELD_MAP['revenue_quarterly']),
                'cost':          GpcwParser.get_field(data, GPCW_FIELD_MAP['cost_quarterly']),
                'rev_yoy_base':  GpcwParser.get_field(data, GPCW_FIELD_MAP['revenue_yoy_base']),
                'roe':          GpcwParser.get_field(data, GPCW_FIELD_MAP['roe_diluted']),
            }

            # 估算总股本
            if total_shares is None and raw['net_profit'] != 0 and raw['eps'] != 0:
                total_shares = abs(raw['net_profit'] / raw['eps'])

            # 计算毛利率
            gross_margin = (raw['revenue'] - raw['cost']) / raw['revenue'] * 100 \
                if raw['revenue'] != 0 else 0.0

            row = {
                '报告期': rdate,
                '年份': year,
                '季度': quarter,
                'code': code,

                # 每股指标
                'eps_basic': round(raw['eps'], 4),
                'book_value_per_share': round(raw['book_value'], 4),
                'cashflow_ps': round(raw['cashflow_ps'], 4),
                'undistributed_ps': round(raw['undist_ps'], 4),
                'reserve_ps': round(raw['reserve_ps'], 4),

                # 金额指标（万元）
                'net_profit_attr_w': round(raw['net_profit'] / 1e4, 2),
                'kfe_np_quarterly_w': round(raw['kfe_np'] / 1e4, 2),
                'revenue_quarterly_w': round(raw['revenue'] / 1e4, 2),
                'cost_quarterly_w': round(raw['cost'] / 1e4, 2),

                # 计算指标
                'gross_margin': round(gross_margin, 4),
                'roe_diluted': round(raw['roe'], 4),

                # 用于 YoY 计算的原始数据
                '_rev_yoy_base': raw['rev_yoy_base'],
                '_kfe_np': raw['kfe_np'],
            }
            rows.append(row)

        df = pd.DataFrame(rows)

        # 4. 计算同比增长率
        df['revenue_yoy'] = None
        df['kfe_np_yoy'] = None

        for i in range(len(df)):
            # 营收同比（同季度去年）
            if i >= 4:
                prev_rev = df.iloc[i - 4]['_rev_yoy_base']
                cur_rev = df.iloc[i]['_rev_yoy_base']
                if prev_rev != 0:
                    df.at[df.index[i], 'revenue_yoy'] = round((cur_rev / prev_rev - 1) * 100, 4)

            # 扣非净利润同比（同季度去年）
            if i >= 4:
                prev_kfe = df.iloc[i - 4]['_kfe_np']
                cur_kfe = df.iloc[i]['_kfe_np']
                if prev_kfe != 0:
                    df.at[df.index[i], 'kfe_np_yoy'] = round((cur_kfe / prev_kfe - 1) * 100, 4)

        # 5. 计算扣非净利润 TTM
        df['kfe_np_ttm_w'] = None
        for i in range(len(df)):
            if i >= 3:
                ttm = sum(df.iloc[j]['_kfe_np'] for j in range(i - 3, i + 1)) / 1e4
                df.at[df.index[i], 'kfe_np_ttm_w'] = round(ttm, 2)

        # 清理临时列
        for col in ['_rev_yoy_base', '_kfe_np']:
            if col in df.columns:
                df.drop(columns=[col], inplace=True)

        # 取最近 N 季度
        df = df.tail(max_quarters).reset_index(drop=True)

        # 添加总股本（已经是万股单位）
        if total_shares:
            df['total_shares'] = round(total_shares, 2)  # 万股

        return df, total_shares

    def _download_gpcw(self, filename: str) -> Optional[str]:
        """
        下载 gpcw 文件（使用 pytdx）

        Args:
            filename: 文件名（如 "gpcw20241231.zip"）

        Returns:
            str: 下载后的文件路径，失败返回 None
        """
        save_path = os.path.join(self.cache_dir, filename)
        if os.path.exists(save_path):
            return save_path

        try:
            from pytdx.crawler.history_financial_crawler import HistoryFinancialCrawler
            crawler = HistoryFinancialCrawler()
            logger.info(f"下载 {filename}...")
            crawler.fetch_and_parse(filename=filename, path_to_download=save_path)
            return save_path
        except Exception as e:
            logger.error(f"下载失败 {filename}: {e}")
            return None

    def collect_to_dict(self, code: str, max_quarters: int = 16) -> Dict:
        """
        采集数据并转为字典格式（用于 MySQL 插入）

        Args:
            code: 股票代码
            max_quarters: 最大季度数

        Returns:
            Dict: 包含 DataFrame 和元数据的字典
        """
        df, total_shares = self.collect(code, max_quarters)

        return {
            'dataframe': df,
            'total_shares': total_shares,
            'record_count': len(df),
            'code': code,
            'latest_report_date': int(df['报告期'].max()) if len(df) > 0 else None,
        }

    def batch_collect(self, codes: List[str], max_quarters: int = 16,
                      progress_callback=None) -> Dict[str, Dict]:
        """
        批量采集多个股票的财务数据

        Args:
            codes: 股票代码列表
            max_quarters: 最大季度数
            progress_callback: 进度回调函数 (current, total, code) -> None

        Returns:
            Dict[str, Dict]: 各股票采集结果
        """
        results = {}
        total = len(codes)

        for idx, code in enumerate(codes):
            try:
                result = self.collect_to_dict(code, max_quarters)
                results[code] = {
                    'status': 'success',
                    'data': result,
                    'error': None,
                }
            except Exception as e:
                results[code] = {
                    'status': 'failed',
                    'data': None,
                    'error': str(e),
                }
                logger.error(f"采集失败 {code}: {e}")

            if progress_callback:
                progress_callback(idx + 1, total, code)

        return results

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
            base_dbf = os.path.join(TDX_DIR, "T0002", "hq_cache", "base.dbf")
            if os.path.exists(base_dbf):
                table = DBF(base_dbf, encoding='gbk')
                for record in table:
                    if record.get('GPDM') == code:
                        total_shares = record.get('ZGB')  # 总股本（万股）
                        if total_shares:
                            return float(total_shares)
        except Exception as e:
            logger.error(f"从 base.dbf 获取 {code} 总股本失败: {e}")
        
        return None
