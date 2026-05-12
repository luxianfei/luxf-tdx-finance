#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采集互动问答数据并写入数据库
"""

import sys
import json
import time
from datetime import datetime

sys.path.insert(0, '.')

from config import MYSQL_CONFIG
from database.mysql_client import MySQLClient
from fetchers.luxf_fetch_ths_hudong import fetch_qa_data

def parse_datetime(datetime_str):
    """解析日期时间字符串"""
    if not datetime_str:
        return None
    
    try:
        # 尝试解析标准格式
        return datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        pass
    
    try:
        # 尝试解析格式: 20240101120000
        if len(datetime_str) == 14:
            return datetime.strptime(datetime_str, '%Y%m%d%H%M%S')
    except ValueError:
        pass
    
    try:
        # 尝试解析格式: 2024-01-01T12:00:00
        return datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        pass
    
    return None

def fetch_and_save_qa(code, limit=20, fetch_all=False):
    """
    采集股票问答数据并保存到数据库
    
    Args:
        code: 股票代码
        limit: 采集条数限制（当fetch_all=True时无效）
        fetch_all: 是否获取所有3年内的已回复数据
    
    Returns:
        int: 成功保存的条数
    """
    print(f"开始采集股票 {code} 的互动问答数据...")
    print(f"采集模式: {'全部3年内已回复数据' if fetch_all else f'最多{limit}条'}")
    
    # 采集数据
    if fetch_all:
        qa_list = fetch_qa_data(code, fetch_all=True, max_years=3)
    else:
        qa_list = fetch_qa_data(code, limit)
    
    print(f"采集到 {len(qa_list)} 条已回复的问答数据")
    
    if not qa_list:
        print("未采集到数据")
        return 0
    
    # 转换数据格式
    data_list = []
    for item in qa_list:
        ask_time = parse_datetime(item.get('ask_time'))
        answer_time = parse_datetime(item.get('answer_time'))
        
        data = {
            'code': code,
            'ask_user': item.get('ask_user', '') or '',
            'ask_time': ask_time,
            'answer_time': answer_time,
            'question': item.get('content', '') or item.get('question', '') or '',
            'answer': item.get('answer', '') or '',
            'status': 1 if (item.get('status') == '1' or (item.get('answer') and item.get('answer').strip())) else 0,
            'source_id': str(item.get('id', '')) or ''
        }
        data_list.append(data)
    
    # 保存到数据库
    db_client = MySQLClient(MYSQL_CONFIG)
    try:
        count = db_client.batch_insert_stock_qa(data_list)
        print(f"成功保存 {count} 条问答数据到数据库")
        return count
    finally:
        db_client.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_qa_to_db.py <stock_code> [limit]")
        print("Example: python fetch_qa_to_db.py 688456 20")
        sys.exit(1)
    
    code = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    fetch_and_save_qa(code, limit)

if __name__ == '__main__':
    main()
