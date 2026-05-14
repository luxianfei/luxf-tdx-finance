#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试采集器
"""

import sys
sys.path.insert(0, '.')

print("=== 测试本地日线数据读取 ===")
from collectors.enhanced_collector import read_local_daily_data, read_historical_data
local = read_local_daily_data('688456')
print("本地日线:", local)

historical = read_historical_data('688456', 10)
print(f"历史数据: {len(historical)} 条")
if historical:
    print("最新历史:", historical[-1])

print("\n=== 测试akshare ===")
try:
    import akshare as ak
    print("akshare版本:", ak.__version__)
    
    print("\n测试 stock_zh_a_spot_em:")
    df = ak.stock_zh_a_spot_em()
    print(f"获取到 {len(df)} 只股票")
    row = df[df['代码'] == '688456']
    if not row.empty:
        print("找到688456:", row.iloc[0][['代码', '名称', '最新价', '涨跌幅', '总市值']])
    else:
        print("未找到688456")
    
    print("\n测试 stock_individual_info_em:")
    df = ak.stock_individual_info_em(symbol='688456')
    print(df)
    
except Exception as e:
    print(f"akshare测试失败: {e}")
    import traceback
    traceback.print_exc()
