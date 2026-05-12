#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API返回数据
"""

import sys
sys.path.insert(0, '.')

from api_server import app

def test_market_api():
    """测试行情API"""
    with app.test_client() as client:
        response = client.get('/api/stock/600011/f10/market')
        print(f"状态码: {response.status_code}")
        print(f"响应数据: {response.data.decode('utf-8')}")

if __name__ == '__main__':
    test_market_api()