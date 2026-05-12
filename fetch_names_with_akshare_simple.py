#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用akshare简单获取股票名称
"""

import sys
sys.path.insert(0, '.')

from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def fetch_names():
    """获取股票名称"""
    try:
        import akshare as ak
        
        print("正在从akshare获取股票列表...")
        df = ak.stock_zh_a_spot_em()
        print(f"成功获取 {len(df)} 只股票")
        
        # 保存到文件
        with open('stock_names_akshare.csv', 'w', encoding='utf-8') as f:
            f.write('code,name\n')
            for _, row in df.iterrows():
                code = str(row['代码']).zfill(6)
                name = row['名称']
                f.write(f"{code},{name}\n")
        
        print("股票名称已保存到 stock_names_akshare.csv")
        
        return True
        
    except Exception as e:
        print(f"获取失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    fetch_names()