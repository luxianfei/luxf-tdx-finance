#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增量更新API接口
"""

import sys
sys.path.insert(0, '.')

from fetchers.incremental_updater import IncrementalUpdater

def main():
    print("测试增量更新功能...")
    
    updater = IncrementalUpdater()
    
    try:
        # 测试市场快照更新
        print("\n1. 测试市场快照更新:")
        result = updater.update_market_snapshot(callback=lambda p, m: print(f"\r进度: {p:.1f}% - {m}", end=''))
        print(f"\n结果: {result['message']}")
        print(f"  总数: {result['total']}, 成功: {result['success']}, 失败: {result['failed']}")
        
        # 测试盈利预测更新
        print("\n2. 测试盈利预测更新:")
        result = updater.update_profit_forecast(callback=lambda p, m: print(f"\r进度: {p:.1f}% - {m}", end=''))
        print(f"\n结果: {result['message']}")
        print(f"  总数: {result['total']}, 成功: {result['success']}, 失败: {result['failed']}, 跳过: {result['skipped']}")
        
    finally:
        updater.close()

if __name__ == '__main__':
    main()
