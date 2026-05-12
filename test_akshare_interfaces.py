#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试akshare各接口，查找可用的股票名称获取方法
"""

import sys
import time
import random
sys.path.insert(0, '.')


def test_various_akshare_funcs():
    """测试各种akshare接口"""
    try:
        import akshare as ak
        
        print("=" * 60)
        print("测试各种akshare接口")
        print("=" * 60)
        
        time.sleep(1)
        
        # 测试1: stock_zh_a_spot_em - 获取所有A股
        print("\n[1] stock_zh_a_spot_em() - 所有A股列表")
        try:
            df = ak.stock_zh_a_spot_em()
            print(f"  成功: {len(df)} 只股票")
        except Exception as e:
            print(f"  失败: {str(e)[:80]}")
        
        time.sleep(random.uniform(1, 2))
        
        # 测试2: stock_info_a_code_name - 股票代码和名称
        print("\n[2] stock_info_a_code_name() - A股代码和名称")
        try:
            df = ak.stock_info_a_code_name()
            print(f"  成功: {len(df)} 只股票")
            if len(df) > 0:
                print(f"  示例: {df.head(3).to_dict('records')}")
        except Exception as e:
            print(f"  失败: {str(e)[:80]}")
        
        time.sleep(random.uniform(1, 2))
        
        # 测试3: stock_individual_info_em - 单个股票信息
        print("\n[3] stock_individual_info_em() - 单个股票信息")
        try:
            df = ak.stock_individual_info_em(symbol="688456")
            print(f"  成功: 股票简称 = {df[df['item']=='股票简称']['value'].values[0] if len(df[df['item']=='股票简称']) > 0 else 'N/A'}")
        except Exception as e:
            print(f"  失败: {str(e)[:80]}")
        
        time.sleep(random.uniform(1, 2))
        
        # 测试4: stock_board_industry_name_em - 行业板块
        print("\n[4] stock_board_industry_name_em() - 行业板块")
        try:
            df = ak.stock_board_industry_name_em()
            print(f"  成功: {len(df)} 个行业")
        except Exception as e:
            print(f"  失败: {str(e)[:80]}")
        
        time.sleep(random.uniform(1, 2))
        
        # 测试5: stock_zh_a_spot - 获取A股列表
        print("\n[5] stock_zh_a_spot() - A股列表")
        try:
            df = ak.stock_zh_a_spot()
            print(f"  成功: {len(df)} 只股票")
        except Exception as e:
            print(f"  失败: {str(e)[:80]}")
        
        time.sleep(random.uniform(1, 2))
        
        # 测试6: stock_board_concept_em - 概念板块
        print("\n[6] stock_board_concept_em() - 概念板块")
        try:
            df = ak.stock_board_concept_em()
            print(f"  成功: {len(df)} 个概念")
        except Exception as e:
            print(f"  失败: {str(e)[:80]}")
        
        time.sleep(random.uniform(1, 2))
        
        # 测试7: stock_zh_indexspot_em - 指数行情
        print("\n[7] stock_zh_indexspot_em() - 指数行情")
        try:
            df = ak.stock_zh_indexspot_em()
            print(f"  成功: {len(df)} 个指数")
        except Exception as e:
            print(f"  失败: {str(e)[:80]}")
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
    except ImportError:
        print("akshare未安装")
    except Exception as e:
        print(f"错误: {e}")


if __name__ == '__main__':
    test_various_akshare_funcs()