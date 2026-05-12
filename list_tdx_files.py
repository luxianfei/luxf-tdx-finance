#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
列出通达信目录中的文件
"""

import os

TDX_DIR = "D:/SoftwaresInstalled/dycy"


def list_files():
    """列出文件"""
    # 列出vipdoc目录下的文件结构
    vipdoc_dir = os.path.join(TDX_DIR, "vipdoc")
    
    if not os.path.exists(vipdoc_dir):
        print(f"目录不存在: {vipdoc_dir}")
        return
    
    print(f"扫描目录: {vipdoc_dir}")
    
    for root, dirs, files in os.walk(vipdoc_dir):
        # 只显示有文件的目录
        if files:
            print(f"\n{root}")
            # 只显示部分文件
            for f in sorted(files)[:10]:
                print(f"  {f}")
            if len(files) > 10:
                print(f"  ... 还有 {len(files) - 10} 个文件")


if __name__ == '__main__':
    list_files()