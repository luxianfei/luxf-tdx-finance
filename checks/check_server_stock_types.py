#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查服务器返回的股票代码类型分布
"""

from pytdx.hq import TdxHq_API


def is_a_stock(code):
    """判断是否为A股股票代码"""
    if not code or not code.isdigit() or len(code) != 6:
        return False
    
    # 上海A股
    if code.startswith('600') or code.startswith('601') or code.startswith('603') or \
       code.startswith('605') or code.startswith('688'):
        return True
    
    # 深圳A股
    if code.startswith('000') or code.startswith('001') or code.startswith('002') or \
       code.startswith('300') or code.startswith('301'):
        return True
    
    # 北交所（排除880开头的概念板块）
    if code.startswith('83') or code.startswith('87'):
        return True
    
    return False


def analyze_server_stocks():
    """分析服务器返回的股票类型"""
    api = TdxHq_API()
    
    try:
        if api.connect('120.25.129.112', 7709):
            print("连接成功")
            
            stock_names = {}
            categories = {
                'sh_main': [],   # 上海主板 600, 601, 603, 605
                'sh_sci': [],    # 科创板 688
                'sz_main': [],   # 深圳主板 000, 001
                'sz_sme': [],    # 中小板 002
                'sz_gem': [],    # 创业板 300, 301
                'bj': [],        # 北交所 83, 87
                'other': []      # 其他
            }
            
            # 获取上海市场
            print("获取上海市场...")
            for start in range(0, 10000, 80):
                data = api.get_security_list(1, start)
                if not data or len(data) == 0:
                    break
                for stock in data:
                    code = stock.get('code')
                    name = stock.get('name')
                    if code and name and code.isdigit() and len(code) == 6:
                        stock_names[code] = name
                        
                        if code.startswith('688'):
                            categories['sh_sci'].append(code)
                        elif code.startswith(('600', '601', '603', '605')):
                            categories['sh_main'].append(code)
            
            # 获取深圳市场
            print("获取深圳市场...")
            for start in range(0, 10000, 80):
                data = api.get_security_list(0, start)
                if not data or len(data) == 0:
                    break
                for stock in data:
                    code = stock.get('code')
                    name = stock.get('name')
                    if code and name and code.isdigit() and len(code) == 6:
                        stock_names[code] = name
                        
                        if code.startswith(('300', '301')):
                            categories['sz_gem'].append(code)
                        elif code.startswith('002'):
                            categories['sz_sme'].append(code)
                        elif code.startswith(('000', '001')):
                            categories['sz_main'].append(code)
                        elif code.startswith(('83', '87')):
                            categories['bj'].append(code)
            
            api.disconnect()
            
            # 输出统计
            print("\n服务器返回的A股类型分布:")
            total = 0
            for cat, codes in categories.items():
                count = len(codes)
                total += count
                print(f"  {cat}: {count} 只")
                if codes:
                    print(f"    示例: {', '.join(codes[:3])}")
            
            print(f"\n总计: {total} 只")
            
            # 检查是否有重复代码
            print(f"\n去重后数量: {len(stock_names)}")
            
        else:
            print("连接失败")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    analyze_server_stocks()