#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将F10数据保存到数据库
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetchers.fetch_f10_server import TdxF10Collector
from database.mysql_client import MySQLClient
from config import MYSQL_CONFIG


def save_f10_to_database(code: str):
    """保存F10数据到数据库"""
    # 获取F10数据
    collector = TdxF10Collector()
    profile = collector.get_company_profile(code)
    collector.disconnect()

    if not profile:
        print(f"获取 {code} F10数据失败")
        return False

    # 连接数据库
    db_client = MySQLClient(MYSQL_CONFIG)

    # 准备数据
    data = {
        'code': code,
        'company_name': profile.get('company_name', '--'),
        'english_name': profile.get('english_name', '--'),
        'industry': profile.get('industry', '--'),
        'business_scope': profile.get('business_scope', '--'),
        'list_date': profile.get('list_date', '--'),
        'reg_capital': profile.get('reg_capital', '--'),
        'chairman': profile.get('chairman', '--'),
        'general_manager': profile.get('general_manager', '--'),
        'address': profile.get('address', '--'),
        'phone': profile.get('phone', '--'),
        'website': profile.get('website', '--')
    }

    # 转换list_date为整数
    if data.get('list_date') and data['list_date'] != '--':
        try:
            data['list_date'] = int(data['list_date'].replace('-', ''))
        except:
            data['list_date'] = None
    else:
        data['list_date'] = None

    # 插入数据库
    success = db_client.insert_company_profile(data)

    if success:
        print(f"成功保存 {code} F10数据到数据库")
        print(f"公司名称: {data['company_name']}")
        print(f"所属行业: {data['industry']}")
    else:
        print(f"保存 {code} F10数据失败")

    db_client.close()
    return success


def main():
    import argparse
    parser = argparse.ArgumentParser(description='保存F10数据到数据库')
    parser.add_argument('code', nargs='?', default='688456', help='股票代码')
    args = parser.parse_args()

    print(f"\n保存股票 {args.code} 的F10数据到数据库...")
    save_f10_to_database(args.code)


if __name__ == '__main__':
    main()