#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试akshare连接，参考workbuddy的实现方式
"""

import sys
import time
import random
from pathlib import Path

sys.path.insert(0, '.')

TDX_PATH = "D:/SoftwaresInstalled/dycy"


def test_akshare_connection():
    """测试akshare连接"""
    try:
        import akshare as ak
        
        print("=" * 50)
        print("测试1: 获取实时行情 (stock_zh_a_spot_em)")
        print("=" * 50)
        time.sleep(random.uniform(1, 3))
        
        try:
            df = ak.stock_zh_a_spot_em()
            print(f"成功！获取了 {len(df)} 只股票")
            print("前5只股票:")
            print(df[['代码', '名称']].head())
            return True
        except Exception as e:
            print(f"失败: {e}")
        
        print()
        print("=" * 50)
        print("测试2: 获取单个股票信息 (stock_individual_info_em)")
        print("=" * 50)
        time.sleep(random.uniform(1, 3))
        
        try:
            df = ak.stock_individual_info_em(symbol="688456")
            print(f"成功！获取了股票688456的信息")
            print(df)
            return True
        except Exception as e:
            print(f"失败: {e}")
        
        print()
        print("=" * 50)
        print("测试3: 获取盈利预测 (stock_yjyg_em)")
        print("=" * 50)
        time.sleep(random.uniform(1, 3))
        
        try:
            df = ak.stock_yjyg_em(indicator="预测指标")
            print(f"成功！获取了盈利预测数据，共 {len(df)} 条")
            return True
        except Exception as e:
            print(f"失败: {e}")
        
        return False
        
    except ImportError:
        print("akshare未安装")
        return False
    except Exception as e:
        print(f"导入akshare失败: {e}")
        return False


def test_with_session():
    """使用自定义session测试"""
    import requests
    
    print()
    print("=" * 50)
    print("测试4: 直接请求东方财富API")
    print("=" * 50)
    
    url = "http://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': 1,
        'pz': 10,
        'po': 1,
        'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': 2,
        'invt': 2,
        'fid': 'f3',
        'fs': 'm:0+t:6,m:0+t:13,m:0+t:80,m:1+t:2,m:1+t:23',
        'fields': 'f12,f14',
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'http://quote.eastmoney.com/',
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应长度: {len(response.text)}")
        print(f"响应内容: {response.text[:500]}")
        return True
    except Exception as e:
        print(f"请求失败: {e}")
        return False


if __name__ == '__main__':
    success = test_akshare_connection()
    test_with_session()
    
    print()
    print("=" * 50)
    if success:
        print("akshare连接测试: 成功")
    else:
        print("akshare连接测试: 失败")
    print("=" * 50)