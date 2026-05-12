#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查服务器是否返回上海A股数据
"""

from pytdx.hq import TdxHq_API


def check_shanghai_stocks():
    """检查上海A股数据"""
    api = TdxHq_API()
    
    try:
        if api.connect('120.25.129.112', 7709):
            print("连接成功")
            
            # 专门检查上海市场
            print("\n检查上海市场（市场代码1）:")
            shanghai_stocks = []
            
            # 尝试从不同位置获取
            for start in [0, 80, 160, 240, 320, 400, 480, 560, 640, 720]:
                data = api.get_security_list(1, start)
                if data and len(data) > 0:
                    for stock in data[:3]:  # 只看前3条
                        code = stock.get('code')
                        name = stock.get('name')
                        if code and code.isdigit() and len(code) == 6:
                            if code.startswith('6'):
                                shanghai_stocks.append((code, name))
                                print(f"  {code}: {name}")
            
            print(f"\n上海市场共找到 {len(shanghai_stocks)} 只6开头的股票")
            
            # 检查深圳市场
            print("\n检查深圳市场（市场代码0）:")
            sz_stocks = []
            
            for start in [0, 80, 160]:
                data = api.get_security_list(0, start)
                if data and len(data) > 0:
                    for stock in data[:3]:
                        code = stock.get('code')
                        name = stock.get('name')
                        if code and code.isdigit() and len(code) == 6:
                            sz_stocks.append((code, name))
                            print(f"  {code}: {name}")
            
            print(f"\n深圳市场共找到 {len(sz_stocks)} 只股票")
            
            api.disconnect()
            
        else:
            print("连接失败")
            
    except Exception as e:
        print(f"错误: {e}")


if __name__ == '__main__':
    check_shanghai_stocks()