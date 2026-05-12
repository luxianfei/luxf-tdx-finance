#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建互动问答表结构
"""

import sys
sys.path.insert(0, '.')

from config import MYSQL_CONFIG
from database.mysql_client import MySQLClient

def create_qa_table():
    """创建互动问答表"""
    db_client = MySQLClient(MYSQL_CONFIG)
    
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS stock_qa (
            id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
            code VARCHAR(10) NOT NULL COMMENT '股票代码',
            ask_user VARCHAR(100) DEFAULT '' COMMENT '提问人',
            ask_time DATETIME COMMENT '提问时间',
            answer_time DATETIME COMMENT '回答时间',
            question TEXT COMMENT '提问问题',
            answer TEXT COMMENT '答复内容',
            status TINYINT DEFAULT 0 COMMENT '状态: 0待回复 1已回复',
            source_id VARCHAR(50) DEFAULT '' COMMENT '来源ID',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
            INDEX idx_code (code),
            INDEX idx_ask_time (ask_time),
            INDEX idx_status (status),
            UNIQUE KEY uk_code_source (code, source_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='股票互动问答表';
        """
        
        db_client.execute(sql)
        db_client.commit()
        print("股票互动问答表创建成功!")
        
    except Exception as e:
        print(f"创建表失败: {e}")
        db_client.rollback()
    finally:
        db_client.close()

if __name__ == '__main__':
    create_qa_table()
