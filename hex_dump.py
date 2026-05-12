#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
十六进制查看通达信.day文件内容
"""

import os
import binascii

def main():
    from config import TDX_DIR
    
    test_file = os.path.join(TDX_DIR, "vipdoc", "sh", "lday", "sh600000.day")
    
    print(f"=== 十六进制查看: {test_file} ===")
    
    if not os.path.exists(test_file):
        print(" 文件不存在")
        return
    
    with open(test_file, 'rb') as f:
        # 读取前128字节
        data = f.read(128)
        
    print("\n前128字节十六进制:")
    print(binascii.hexlify(data).decode('ascii'))
    
    print("\n前128字节ASCII:")
    for i in range(0, len(data), 32):
        line = data[i:i+32]
        hex_str = ' '.join(f'{b:02X}' for b in line)
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in line)
        print(f"{i:04X}: {hex_str}  {ascii_str}")

if __name__ == '__main__':
    main()
