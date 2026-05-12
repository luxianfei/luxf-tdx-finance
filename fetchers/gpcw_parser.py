#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gpcw 二进制文件解析器
功能：解析通达信 gpcwYYYYMMDD.zip 文件，提取指定股票的财务数据
"""

import os
import struct
import tempfile
import shutil
import zipfile
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class GpcwParser:
    """
    gpcw 文件解析器

    gpcw 文件是通达信 F10 财务数据的二进制存储格式：
    - 每个文件包含所有 A 股股票的 584 个 float 字段（约 2.3KB/股票）
    - 使用 zip 压缩，内含单个 .dat 文件
    """

    def __init__(self, cache_dir: str):
        """
        初始化解析器

        Args:
            cache_dir: gpcw 文件缓存目录
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def parse_file(self, zip_path: str, target_code: str) -> Dict[int, List[float]]:
        """
        解析 gpcw zip 文件，提取目标股票的数据

        Args:
            zip_path: gpcw zip 文件路径
            target_code: 目标股票代码（如 "688456"）

        Returns:
            Dict[int, List[float]]: {report_date: [data_list]}，report_date 为整数如 20241231
        """
        tmpdir = tempfile.mkdtemp()
        results = {}

        try:
            # 解压 zip 文件
            with zipfile.ZipFile(zip_path, 'r') as zf:
                dat_files = [f for f in zf.namelist() if f.endswith('.dat')]
                if not dat_files:
                    logger.warning(f"zip 中未找到 .dat 文件: {zip_path}")
                    return results

                # 读取第一个 .dat 文件
                dat_name = dat_files[0]
                with zf.open(dat_name) as dat_file:
                    content = dat_file.read()

            # 提取报告期（从文件名）
            report_date = int(zip_path.split('gpcw')[-1].replace('.zip', ''))

            # 解析二进制数据
            data = self._parse_binary(content, target_code)
            if data:
                results[report_date] = data

        except Exception as e:
            logger.error(f"解析 gpcw 文件失败 {zip_path}: {e}")
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

        return results

    def _parse_binary(self, content: bytes, target_code: str) -> Optional[List[float]]:
        """
        解析 gpcw 二进制数据

        文件结构：
        - 文件头 (header_size bytes)
        - 股票记录索引区 (max_count * index_size bytes)
        - 股票数据区 (实际财务数据)

        每个股票记录：
        - code[6]: 股票代码（6字节 ASCII）
        - market: 市场标识（1字节）
        - offset: 数据区偏移量（4字节，little-endian）
        - ... 数据区 float 数组
        """
        # 解析文件头
        # 格式: short(?), unsigned int, short(?), 3*unsigned int
        header_struct = struct.Struct('<1hI1H3L')
        header_size = header_struct.size  # 20 bytes

        if len(content) < header_size:
            logger.error(f"文件太小: {len(content)} < {header_size}")
            return None

        header = header_struct.unpack(content[:header_size])
        # h: short, I: unsigned int, H: unsigned short, L: unsigned int
        _, report_date, max_count, _, report_size, _ = header
        fields_per_record = int(report_size / 4)

        # 数据字段格式
        data_format = f'<{fields_per_record}f'

        # 索引条目大小
        index_struct = struct.Struct('<6s1c1L')  # 11 bytes: 6s + 1c + 1L
        index_size = index_struct.size

        # 搜索目标股票
        for i in range(max_count):
            offset = header_size + i * index_size
            if offset + index_size > len(content):
                break

            # 解析索引条目
            code_bytes, _, data_offset = index_struct.unpack_from(content, offset)
            code = code_bytes.decode('ascii', errors='replace').strip()

            if code == target_code:
                # 提取数据
                data_start = data_offset
                data_end = data_start + report_size
                if data_end <= len(content):
                    raw_data = struct.unpack_from(data_format, content, data_start)
                    return list(raw_data)

        return None

    def parse_all(self, zip_paths: List[str], target_code: str) -> Dict[int, List[float]]:
        """
        批量解析多个 gpcw 文件

        Args:
            zip_paths: gpcw zip 文件路径列表
            target_code: 目标股票代码

        Returns:
            Dict[int, List[float]]: 所有文件的数据汇总
        """
        all_data = {}
        for zip_path in zip_paths:
            if not os.path.exists(zip_path):
                continue
            data = self.parse_file(zip_path, target_code)
            all_data.update(data)

        return all_data

    @staticmethod
    def get_field(data: List[float], col_num: int) -> float:
        """
        获取字段值（col_num 从 1 开始）

        Args:
            data: 股票数据列表
            col_num: 字段列号（从 1 开始）

        Returns:
            float: 字段值，如果越界返回 0.0
        """
        if col_num < 1 or col_num > len(data):
            return 0.0
        return data[col_num - 1]
