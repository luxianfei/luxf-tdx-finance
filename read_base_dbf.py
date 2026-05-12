#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从通达信本地base.dbf文件读取股票名称
"""

import os
import struct
from config import TDX_DIR


def read_base_dbf():
    """读取通达信base.dbf文件"""
    base_files = [
        os.path.join(TDX_DIR, "vipdoc", "sh", "base.dbf"),
        os.path.join(TDX_DIR, "vipdoc", "sz", "base.dbf"),
    ]
    
    stock_names = {}
    
    for base_file in base_files:
        if not os.path.exists(base_file):
            print(f"文件不存在: {base_file}")
            continue
            
        print(f"读取文件: {base_file}")
        
        try:
            with open(base_file, 'rb') as f:
                # DBF文件头
                header = f.read(32)
                if len(header) < 32:
                    print("文件头太短")
                    continue
                
                # 解析DBF头
                version = header[0]
                update_date = header[1:4]
                num_records = struct.unpack('<I', header[4:8])[0]
                header_len = struct.unpack('<H', header[8:10])[0]
                record_len = struct.unpack('<H', header[10:12])[0]
                
                print(f"  版本: {version}")
                print(f"  记录数: {num_records}")
                print(f"  表头长度: {header_len}")
                print(f"  记录长度: {record_len}")
                
                # 跳过表头
                f.seek(header_len)
                
                # 读取记录
                for i in range(min(10, num_records)):
                    record = f.read(record_len)
                    if len(record) < record_len:
                        break
                    
                    # 解析记录 - 通达信base.dbf格式
                    # 通常前10个字节是代码，后面是名称
                    try:
                        code = record[0:10].decode('gbk').strip()
                        name = record[10:26].decode('gbk').strip()
                        
                        if code and code.isdigit() and len(code) == 6:
                            stock_names[code] = name
                            print(f"  {code}: {name}")
                    except Exception as e:
                        print(f"  解析失败: {e}")
                
                print(f"  共读取 {len(stock_names)} 条记录")
                
        except Exception as e:
            print(f"读取失败: {e}")
    
    return stock_names


if __name__ == '__main__':
    stocks = read_base_dbf()
    print(f"\n总计获取 {len(stocks)} 只股票名称")