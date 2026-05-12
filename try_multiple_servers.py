#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尝试多个通达信服务器获取股票名称
"""

from pytdx.hq import TdxHq_API


def try_multiple_servers():
    """尝试多个服务器"""
    servers = [
        ('120.25.129.112', 7709),   # 深圳
        ('119.147.212.81', 7709),   # 深圳
        ('124.74.236.94', 7709),    # 上海
        ('60.191.116.58', 7709),    # 上海
        ('60.191.116.167', 7709),   # 上海
        ('112.95.158.14', 7709),    # 广州
        ('112.95.158.2', 7709),     # 广州
        ('113.108.112.130', 7709),  # 上海
        ('113.108.144.108', 7709),  # 上海
        ('120.196.127.88', 7709),   # 深圳
        ('183.239.132.37', 7709),   # 杭州
        ('183.239.132.38', 7709),   # 杭州
        ('58.252.15.130', 7709),    # 上海
        ('59.36.23.164', 7709),     # 深圳
        ('59.36.23.165', 7709),     # 深圳
    ]
    
    all_stocks = {}
    
    for host, port in servers:
        print(f"\n尝试连接 {host}:{port}...")
        api = TdxHq_API()
        
        try:
            if api.connect(host, port, time_out=3):
                print("  连接成功")
                
                # 获取上海市场
                print("  获取上海市场股票...")
                for start in range(0, 5000, 80):
                    try:
                        data = api.get_security_list(1, start)
                        if not data or len(data) == 0:
                            break
                        for stock in data:
                            code = stock.get('code')
                            name = stock.get('name')
                            if code and name and code.isdigit() and len(code) == 6:
                                if code.startswith('6'):  # 上海A股
                                    if code not in all_stocks:
                                        all_stocks[code] = name
                    except Exception as e:
                        break
                
                # 获取深圳市场
                print("  获取深圳市场股票...")
                for start in range(0, 5000, 80):
                    try:
                        data = api.get_security_list(0, start)
                        if not data or len(data) == 0:
                            break
                        for stock in data:
                            code = stock.get('code')
                            name = stock.get('name')
                            if code and name and code.isdigit() and len(code) == 6:
                                if code.startswith(('0', '3')):  # 深圳A股
                                    if code not in all_stocks:
                                        all_stocks[code] = name
                    except Exception as e:
                        break
                
                api.disconnect()
                print(f"  从该服务器获取了 {len(all_stocks)} 只股票")
                
                # 如果获取了足够多的股票，提前退出
                if len(all_stocks) > 5000:
                    print("  已获取足够多的股票，提前退出")
                    break
                    
            else:
                print("  连接失败")
                
        except Exception as e:
            print(f"  连接异常: {e}")
    
    print(f"\n总计获取了 {len(all_stocks)} 只股票")
    
    # 统计各类股票数量
    sh_main = sum(1 for code in all_stocks if code.startswith(('600', '601', '603', '605')))
    sh_sci = sum(1 for code in all_stocks if code.startswith('688'))
    sz_main = sum(1 for code in all_stocks if code.startswith(('000', '001')))
    sz_sme = sum(1 for code in all_stocks if code.startswith('002'))
    sz_gem = sum(1 for code in all_stocks if code.startswith(('300', '301')))
    
    print(f"\n股票类型分布:")
    print(f"  上海主板: {sh_main}")
    print(f"  科创板: {sh_sci}")
    print(f"  深圳主板: {sz_main}")
    print(f"  中小板: {sz_sme}")
    print(f"  创业板: {sz_gem}")
    
    return all_stocks


if __name__ == '__main__':
    stocks = try_multiple_servers()
    
    # 保存到文件
    if stocks:
        with open('stock_names_from_servers.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(stocks.items()):
                f.write(f"{code}\t{name}\n")
        print("\n股票名称已保存到 stock_names_from_servers.txt")