#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票列表工具
功能：获取 A 股全量股票列表，支持从 pytdx 或本地文件获取
"""

import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class StockListHelper:
    """
    股票列表辅助工具

    用于获取和管理 A 股全量股票列表
    """

    # 常用股票代码前缀
    SH_PREFIXES = ['60', '68']      # 上海: 上证主板、科创板
    SZ_PREFIXES = ['00', '30']      # 深圳: 深证主板、创业板

    def __init__(self, cache_file: str = None):
        """
        初始化

        Args:
            cache_file: 股票列表缓存文件路径
        """
        self.cache_file = cache_file or "stock_list.json"

    def get_all_codes(self) -> List[str]:
        """
        获取所有 A 股股票代码

        Returns:
            List[str]: 股票代码列表
        """
        # 方法1: 从缓存文件读取
        if os.path.exists(self.cache_file):
            return self._load_from_cache()

        # 方法2: 从 pytdx 获取
        try:
            return self._fetch_from_tdx()
        except Exception as e:
            logger.warning(f"pytdx 获取失败: {e}")
            # 方法3: 返回默认列表
            return self._get_default_list()

    def _load_from_cache(self) -> List[str]:
        """从缓存文件加载"""
        import json
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('codes', [])
        except Exception as e:
            logger.error(f"读取缓存失败: {e}")
            return []

    def _save_to_cache(self, codes: List[str]):
        """保存到缓存文件"""
        import json
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({'codes': codes, 'updated': str(__import__('datetime').date.today())}, f)
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")

    def _fetch_from_tdx(self) -> List[str]:
        """从通达信获取股票列表"""
        try:
            from pytdx.hq import TdxHq_API
            api = TdxHq_API(heartbeat=True, auto_retry=True)

            # 尝试连接通达信服务器
            servers = [
                ('119.147.212.81', 7709),
                ('119.147.212.80', 7709),
                ('124.74.236.94', 7709),
                ('61.152.107.141', 7709),
            ]
            
            connected = False
            for host, port in servers:
                try:
                    if api.connect(host, port):
                        connected = True
                        logger.info(f"成功连接通达信服务器 {host}:{port}")
                        break
                except:
                    continue
            
            if not connected:
                logger.warning("无法连接通达信服务器")
                return []

            codes = []

            # 获取上海股票列表
            try:
                data = api.get_security_list(1, 0)
                sh_codes = [str(item['code']).zfill(6) for item in data
                           if str(item['code']).startswith(tuple(self.SH_PREFIXES))]
                codes.extend(sh_codes)
            except Exception as e:
                logger.warning(f"获取上海列表失败: {e}")

            # 获取深圳股票列表
            try:
                data = api.get_security_list(0, 0)
                sz_codes = [str(item['code']).zfill(6) for item in data
                           if str(item['code']).startswith(tuple(self.SZ_PREFIXES))]
                codes.extend(sz_codes)
            except Exception as e:
                logger.warning(f"获取深圳列表失败: {e}")

            api.disconnect()

            if codes:
                self._save_to_cache(codes)
                logger.info(f"获取股票列表成功: {len(codes)} 只")
                return codes

        except ImportError:
            logger.warning("pytdx 未安装")

        return []

    def get_codes_with_names(self) -> Dict[str, str]:
        """
        获取股票代码和名称的字典
        
        Returns:
            Dict[str, str]: {code: name} 字典
        """
        try:
            from pytdx.hq import TdxHq_API
            api = TdxHq_API(heartbeat=True, auto_retry=True)

            # 尝试连接通达信服务器
            servers = [
                ('119.147.212.81', 7709),
                ('119.147.212.80', 7709),
                ('124.74.236.94', 7709),
                ('61.152.107.141', 7709),
            ]
            
            connected = False
            for host, port in servers:
                try:
                    if api.connect(host, port):
                        connected = True
                        logger.info(f"成功连接通达信服务器 {host}:{port}")
                        break
                except:
                    continue
            
            if not connected:
                logger.warning("无法连接通达信服务器")
                return {}

            code_name_dict = {}

            # 获取上海股票列表
            try:
                data = api.get_security_list(1, 0)
                for item in data:
                    code = str(item['code']).zfill(6)
                    if code.startswith(tuple(self.SH_PREFIXES)):
                        name = item['name'].decode('gbk') if isinstance(item['name'], bytes) else item['name']
                        code_name_dict[code] = name
            except Exception as e:
                logger.warning(f"获取上海列表失败: {e}")

            # 获取深圳股票列表
            try:
                data = api.get_security_list(0, 0)
                for item in data:
                    code = str(item['code']).zfill(6)
                    if code.startswith(tuple(self.SZ_PREFIXES)):
                        name = item['name'].decode('gbk') if isinstance(item['name'], bytes) else item['name']
                        code_name_dict[code] = name
            except Exception as e:
                logger.warning(f"获取深圳列表失败: {e}")

            api.disconnect()

            logger.info(f"获取股票代码和名称成功: {len(code_name_dict)} 只")
            return code_name_dict

        except ImportError:
            logger.warning("pytdx 未安装")

        return {}

    def _get_default_list(self) -> List[str]:
        """
        获取默认股票列表（基于常见代码段）
        这是备用方案，建议优先使用 pytdx
        """
        codes = []

        # 上海主板 (60xxxx)
        for i in range(600000, 601000):
            codes.append(str(i))

        # 科创板 (688xxx)
        for i in range(688000, 689100):
            codes.append(str(i))

        # 深圳主板 (00xxxx)
        for i in range(1, 1000):
            codes.append(str(i).zfill(6))

        # 创业板 (300xxx)
        for i in range(300000, 301000):
            codes.append(str(i))

        return codes

    def filter_codes(self, codes: List[str],
                     market: str = None,
                     prefix: List[str] = None) -> List[str]:
        """
        过滤股票代码

        Args:
            codes: 原始股票代码列表
            market: 市场过滤 ("sh", "sz", "bj")
            prefix: 代码前缀过滤

        Returns:
            List[str]: 过滤后的股票代码
        """
        if market == "sh":
            codes = [c for c in codes if c.startswith(tuple(self.SH_PREFIXES))]
        elif market == "sz":
            codes = [c for c in codes if c.startswith(tuple(self.SZ_PREFIXES))]

        if prefix:
            codes = [c for c in codes if c.startswith(tuple(prefix))]

        return codes

    @staticmethod
    def validate_code(code: str) -> bool:
        """
        验证股票代码格式

        Args:
            code: 股票代码

        Returns:
            bool: 是否有效
        """
        if not code or len(code) != 6:
            return False

        if not code.isdigit():
            return False

        # 检查常见前缀
        valid_prefixes = ['60', '68', '00', '30']
        return any(code.startswith(p) for p in valid_prefixes)

    @staticmethod
    def get_market(code: str) -> Optional[str]:
        """
        根据代码判断市场

        Args:
            code: 股票代码

        Returns:
            str: 市场标识 ("sh", "sz", "bj") 或 None
        """
        if code.startswith('60'):
            return 'sh'
        elif code.startswith('68'):
            return 'sh'
        elif code.startswith('00'):
            return 'sz'
        elif code.startswith('30'):
            return 'sz'
        elif code.startswith('8') or code.startswith('4'):
            return 'bj'
        return None
