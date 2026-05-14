#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查通达信.day文件格式
"""

import os
import struct

def main():
    from config import TDX_DIR
    
    # 测试文件
    test_files = [
        os.path.join(TDX_DIR, "vipdoc", "sh", "lday", "sh600000.day"),
        os.path.join(TDX_DIR, "vipdoc", "sz", "lday", "sz000001.day")
    ]
    
    for day_file in test_files:
        print(f"\n=== 检查文件: {day_file} ===")
        
        if not os.path.exists(day_file):
            print(" 文件不存在")
            continue
        
        file_size = os.path.getsize(day_file)
        print(f"文件大小: {file_size} 字节")
        
        record_count = file_size // 32
        print(f"预计记录数: {record_count}")
        
        with open(day_file, 'rb') as f:
            # 读取前几条记录
            print("\n前3条记录:")
            for i in range(min(3, record_count)):
                data = f.read(32)
                if len(data) < 32:
                    break
                
                date = struct.unpack('<I', data[0:4])[0]
                open_price = struct.unpack('<f', data[4:8])[0]
                high_price = struct.unpack('<f', data[8:12])[0]
                low_price = struct.unpack('<f', data[12:16])[0]
                close_price = struct.unpack('<f', data[16:20])[0]
                volume = struct.unpack('<I', data[20:24])[0]
                amount = struct.unpack('<f', data[24:28])[0]
                
                print(f"记录 {i+1}:")
                print(f"  日期: {date}")
                print(f"  开盘: {open_price:.2f}, 最高: {high_price:.2f}, 最低: {low_price:.2f}, 收盘: {close_price:.2f}")
                print(f"  成交量: {volume}, 成交额: {amount:.2f}")
            
            # 如果记录数大于3，读取最后一条记录
            if record_count > 3:
                f.seek(-32, 2)
                data = f.read(32)
                
                date = struct.unpack('<I', data[0:4])[0]
                open_price = struct.unpack('<f', data[4:8])[0]
                high_price = struct.unpack('<f', data[8:12])[0]
                low_price = struct.unpack('<f', data[12:16])[0]
                close_price = struct.unpack('<f', data[16:20])[0]
                volume = struct.unpack('<I', data[20:24])[0]
                amount = struct.unpack('<f', data[24:28])[0]
                
                print(f"\n最后一条记录:")
                print(f"  日期: {date}")
                print(f"  开盘: {open_price:.2f}, 最高: {high_price:.2f}, 最低: {low_price:.2f}, 收盘: {close_price:.2f}")
                print(f"  成交量: {volume}, 成交额: {amount:.2f}")

if __name__ == '__main__':
    main()
