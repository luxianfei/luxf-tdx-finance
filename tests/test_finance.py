#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用例
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import GPCW_FIELD_MAP, parse_report_date
from fetchers import GpcwParser, FinanceCollector
from utils import StockListHelper


class TestFieldMap(unittest.TestCase):
    """字段映射测试"""

    def test_field_map_keys(self):
        """验证字段映射完整性"""
        required_fields = [
            'eps_basic', 'book_value_per_share', 'cashflow_ps',
            'net_profit_attr', 'kfe_np_quarterly', 'revenue_quarterly',
            'cost_quarterly', 'revenue_yoy_base', 'roe_diluted'
        ]
        for field in required_fields:
            self.assertIn(field, GPCW_FIELD_MAP)
            self.assertIsInstance(GPCW_FIELD_MAP[field], int)

    def test_parse_report_date(self):
        """测试报告期解析"""
        cases = [
            ('20240331', (2024, 1)),
            ('20240630', (2024, 2)),
            ('20240930', (2024, 3)),
            ('20241231', (2024, 4)),
        ]
        for date_str, expected in cases:
            self.assertEqual(parse_report_date(date_str), expected)


class TestGpcwParser(unittest.TestCase):
    """gpcw 解析器测试"""

    def setUp(self):
        self.parser = GpcwParser(cache_dir="finance_data")

    def test_get_field(self):
        """测试字段提取"""
        data = list(range(1, 101))  # 1-100
        self.assertEqual(GpcwParser.get_field(data, 1), 1.0)
        self.assertEqual(GpcwParser.get_field(data, 50), 50.0)
        self.assertEqual(GpcwParser.get_field(data, 100), 100.0)
        self.assertEqual(GpcwParser.get_field(data, 0), 0.0)  # 越界返回0
        self.assertEqual(GpcwParser.get_field(data, 101), 0.0)  # 越界返回0


class TestStockListHelper(unittest.TestCase):
    """股票列表工具测试"""

    def test_validate_code(self):
        """测试代码验证"""
        valid_codes = ['688456', '000001', '600519', '300750']
        invalid_codes = ['12345', '1234567', 'ABCDEF', '']

        for code in valid_codes:
            self.assertTrue(StockListHelper.validate_code(code))

        for code in invalid_codes:
            self.assertFalse(StockListHelper.validate_code(code))

    def test_get_market(self):
        """测试市场判断"""
        self.assertEqual(StockListHelper.get_market('688456'), 'sh')
        self.assertEqual(StockListHelper.get_market('600519'), 'sh')
        self.assertEqual(StockListHelper.get_market('000001'), 'sz')
        self.assertEqual(StockListHelper.get_market('300750'), 'sz')
        self.assertIsNone(StockListHelper.get_market('000000'))


if __name__ == '__main__':
    unittest.main()
