#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整读取通达信base.dbf文件
"""

import os
import struct

TDX_DIR = "D:/SoftwaresInstalled/dycy"


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
            
        print(f"\n读取文件: {base_file}")
        
        try:
            with open(base_file, 'rb') as f:
                # DBF文件头
                header = f.read(32)
                if len(header) < 32:
                    print("文件头太短")
                    continue
                
                # 解析DBF头
                version = header[0]
                num_records = struct.unpack('<I', header[4:8])[0]
                header_len = struct.unpack('<H', header[8:10])[0]
                record_len = struct.unpack('<H', header[10:12])[0]
                
                print(f"  版本: {version}")
                print(f"  记录数: {num_records}")
                print(f"  表头长度: {header_len}")
                print(f"  记录长度: {record_len}")
                
                # 读取字段定义
                fields = []
                pos = 32
                while pos < header_len:
                    field_name = b''
                    while True:
                        c = f.read(1)
                        if c == b'\x00':
                            break
                        field_name += c
                    if field_name == b'':
                        break
                    pos += 11
                    f.seek(pos)
                
                # 跳过表头
                f.seek(header_len)
                
                # 读取所有记录
                count = 0
                for i in range(num_records):
                    record = f.read(record_len)
                    if len(record) < record_len:
                        break
                    
                    # 解析记录 - 通达信base.dbf格式
                    try:
                        # 代码在前10字节
                        code = record[0:10].decode('gbk', errors='ignore').strip()
                        # 名称通常在接下来的字节
                        name = record[10:26].decode('gbk', errors='ignore').strip()
                        
                        if code and code.isdigit() and len(code) == 6:
                            if name and name != '':
                                stock_names[code] = name
                                count += 1
                                # 每500只打印一次
                                if count % 500 == 0:
                                    print(f"  已读取 {count} 条记录...")
                                
                    except Exception as e:
                        pass
                
                print(f"  共读取 {count} 条有效记录")
                
        except Exception as e:
            print(f"读取失败: {e}")
            import traceback
            traceback.print_exc()
    
    return stock_names


if __name__ == '__main__':
    stocks = read_base_dbf()
    
    print(f"\n总计获取 {len(stocks)} 只股票名称")
    
    # 统计代码前缀
    prefix_counts = {}
    for code in stocks.keys():
        prefix = code[:2]
        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    
    print("\n股票代码前缀分布:")
    for prefix, count in sorted(prefix_counts.items()):
        print(f"  {prefix}开头: {count} 只")
    
    # 保存到文件
    if stocks:
        with open('base_dbf_stocks.txt', 'w', encoding='utf-8') as f:
            for code, name in sorted(stocks.items()):
                f.write(f"{code}\t{name}\n")
        print("\n股票名称已保存到 base_dbf_stocks.txt")