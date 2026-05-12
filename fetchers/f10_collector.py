#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F10数据采集器
功能：从通达信远程服务器获取F10数据（公司概况、行情数据和盈利预测），并存储到数据库
"""

import os
import logging
import re
from typing import Dict, Optional, Any, List
import json

try:
    from pytdx.hq import TdxHq_API
    HAS_PYTDX = True
except ImportError:
    HAS_PYTDX = False

from config import TDX_DIR
from database.mysql_client import MySQLClient

logger = logging.getLogger(__name__)

# 通达信远程服务器列表
TDX_SERVERS = [
    ('120.25.129.112', 7709),
    ('183.239.132.37', 7709),
    ('180.153.18.178', 7709),
]


class F10Collector:
    """
    F10数据采集器
    
    从通达信远程服务器获取：
    1. 公司概况（行业、主营业务等）
    2. 行情数据（价格、涨跌幅、换手率、市值等）
    3. 盈利预测（机构预测数据）
    
    并支持将数据存储到数据库
    """

    def __init__(self, tdx_dir: str = TDX_DIR, db_client: Optional[MySQLClient] = None):
        """
        初始化采集器
        
        Args:
            tdx_dir: 通达信安装目录（保留兼容）
            db_client: MySQL客户端实例（可选）
        """
        self.tdx_dir = tdx_dir
        self.db_client = db_client
        self.hq_api = None
        self._init_apis()

    def _init_apis(self):
        """初始化TDX API"""
        if not HAS_PYTDX:
            logger.warning("pytdx未安装，无法采集行情数据")
            return
        
        try:
            # 初始化行情API（用于获取实时行情和F10数据）
            self.hq_api = TdxHq_API()
        except Exception as e:
            logger.error(f"初始化TDX API失败: {e}")

    def _connect_server(self) -> bool:
        """连接到通达信远程服务器"""
        if not self.hq_api:
            return False
            
        for host, port in TDX_SERVERS:
            try:
                if self.hq_api.connect(host, port):
                    logger.info(f"成功连接到通达信服务器 {host}:{port}")
                    return True
            except Exception as e:
                logger.debug(f"连接 {host}:{port} 失败: {e}")
        logger.error("无法连接到任何通达信服务器")
        return False

    def _get_market_code(self, code: str) -> int:
        """
        根据股票代码判断市场
        
        Args:
            code: 股票代码
            
        Returns:
            int: 市场代码 (0=深圳, 1=上海)
        """
        if code.startswith(('0', '2', '3')):
            return 0  # 深圳
        elif code.startswith(('6', '5')):
            return 1  # 上海
        return 1  # 默认上海

    def _read_f10_file(self, code: str, market: int, category: str) -> str:
        """
        读取F10数据文件
        
        Args:
            code: 股票代码
            market: 市场代码 (0=深圳, 1=上海)
            category: F10分类名称
            
        Returns:
            str: F10数据内容
        """
        # 构建F10文件路径
        market_str = 'sh' if market == 1 else 'sz'
        
        # F10数据可能存储在多个位置
        possible_paths = [
            os.path.join(self.tdx_dir, 'vipdoc', market_str, 'cw', f'{code}.txt'),
            os.path.join(self.tdx_dir, 'T0002', 'f10', market_str, f'{code}.dat'),
            os.path.join(self.tdx_dir, 'vipdoc', 'cw', market_str, f'{code}.txt'),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                        # 尝试多种编码解码
                        encodings = ['gbk', 'gb2312', 'utf-8', 'big5']
                        for encoding in encodings:
                            try:
                                return content.decode(encoding)
                            except:
                                continue
                        # 如果都失败，返回原始字节的十六进制表示
                        logger.warning(f"无法解码F10文件: {path}")
                        return content.hex()[:1000]
                except Exception as e:
                    logger.error(f"读取F10文件失败 {path}: {e}")
        
        logger.warning(f"未找到F10文件: {code}")
        return ""

    def get_company_profile(self, code: str) -> Dict[str, Any]:
        """
        获取公司概况信息（从远程服务器）
        
        Args:
            code: 股票代码
            
        Returns:
            Dict: 公司概况数据
        """
        result = {
            'code': code,
            'industry': '--',
            'business_scope': '--',
            'company_name': '--',
            'english_name': '--',
            'establish_date': '--',
            'list_date': '--',
            'reg_capital': '--',
            'chairman': '--',
            'general_manager': '--',
            'address': '--',
            'phone': '--',
            'website': '--'
        }
        
        if not self.hq_api:
            return result
        
        try:
            market = self._get_market_code(code)
            
            # 连接远程服务器
            if not self._connect_server():
                return result
            
            try:
                # 获取公司信息类别
                category = self.hq_api.get_company_info_category(market, code)
                if not category:
                    return result

                # 找到公司概况
                profile_info = None
                filename = None
                for item in category:
                    if item['name'] == '公司概况':
                        profile_info = item
                        filename = item['filename']
                        break

                if not profile_info:
                    return result

                # 获取公司概况内容
                content = self.hq_api.get_company_info_content(
                    market, code, filename,
                    profile_info['start'],
                    profile_info['length']
                )

                if not content:
                    return result

                # 解析表格格式的内容
                result = self._parse_profile_table(content, code)
                logger.info(f"成功获取 {code} 公司概况")
            finally:
                self.hq_api.disconnect()
                
        except Exception as e:
            logger.error(f"获取公司概况失败 {code}: {e}")
        
        return result

    def _parse_profile_table(self, content: str, code: str) -> Dict[str, Any]:
        """解析表格格式的公司概况"""
        result = {
            'code': code,
            'industry': '--',
            'business_scope': '--',
            'company_name': '--',
            'english_name': '--',
            'establish_date': '--',
            'list_date': '--',
            'reg_capital': '--',
            'chairman': '--',
            'general_manager': '--',
            'address': '--',
            'phone': '--',
            'website': '--'
        }

        # 按行分割
        lines = content.split('\n')

        for line in lines:
            # 去除表格边框字符
            line_clean = line.replace('┌', '').replace('┐', '').replace('├', '').replace('┤', '')
            line_clean = line_clean.replace('─', '').replace('│', '|').strip()

            # 按 | 分割
            parts = [p.strip() for p in line_clean.split('|') if p.strip()]

            if len(parts) >= 2:
                key = parts[0]
                value = parts[1] if len(parts) > 1 else ''

                if '公司名称' in key:
                    result['company_name'] = value
                elif '英文全称' in key:
                    result['english_name'] = value
                elif '行业' in key and result['industry'] == '--':
                    result['industry'] = value
                elif '主营业务' in key:
                    result['business_scope'] = value
                elif '上市日期' in key:
                    result['list_date'] = value
                elif '注册资本' in key:
                    result['reg_capital'] = value
                elif '法人代表' in key:
                    result['chairman'] = value
                elif '总经理' in key:
                    result['general_manager'] = value
                elif '注册地址' in key or '办公地址' in key:
                    result['address'] = value
                elif '联系电话' in key:
                    result['phone'] = value
                elif '公司网址' in key:
                    result['website'] = value

                # 处理双列格式
                if len(parts) >= 4:
                    key2 = parts[2]
                    value2 = parts[3] if len(parts) > 3 else ''
                    if '行业' in key2 and result['industry'] == '--':
                        result['industry'] = value2
                    elif '主营业务' in key2:
                        result['business_scope'] = value2

        return result

    def get_market_data(self, code: str) -> Dict[str, Any]:
        """
        获取最新行情数据（从远程服务器）
        
        Args:
            code: 股票代码
            
        Returns:
            Dict: 行情数据
        """
        result = {
            'code': code,
            'price': 0.0,
            'change': 0.0,
            'change_percent': 0.0,
            'turnover_rate': 0.0,
            'market_cap': 0.0,
            'pe': 0.0,
            'pb': 0.0,
            'volume': 0,
            'amount': 0.0,
            'high': 0.0,
            'low': 0.0,
            'open': 0.0,
            'prev_close': 0.0
        }
        
        if not self.hq_api:
            return result
            
        try:
            market = self._get_market_code(code)
            
            # 连接远程服务器
            if not self._connect_server():
                return result
            
            try:
                # 获取行情数据
                data = self.hq_api.get_security_quotes([(market, code)])
                
                if data and len(data) > 0:
                    quote = data[0]
                    result['price'] = quote.get('price', 0.0)
                    result['change'] = quote.get('change', 0.0) or quote.get('price', 0.0) - quote.get('last_close', 0.0)
                    result['change_percent'] = quote.get('changepercent', 0.0)
                    result['turnover_rate'] = quote.get('turnover', 0.0)
                    result['market_cap'] = quote.get('market', 0) / 10000  # 转换为亿元
                    result['pe'] = quote.get('pe', 0.0)
                    result['pb'] = quote.get('pb', 0.0)
                    result['volume'] = quote.get('vol', 0)
                    result['amount'] = quote.get('amount', 0) / 10000  # 转换为万元
                    result['high'] = quote.get('high', 0.0)
                    result['low'] = quote.get('low', 0.0)
                    result['open'] = quote.get('open', 0.0)
                    result['prev_close'] = quote.get('last_close', 0.0)
            
                logger.info(f"成功获取 {code} 行情数据")
            finally:
                self.hq_api.disconnect()
                
        except Exception as e:
            logger.error(f"获取行情数据失败 {code}: {e}")
        
        return result

    def get_profit_forecast(self, code: str) -> Dict[str, Any]:
        """
        获取盈利预测数据（从远程服务器）
        
        Args:
            code: 股票代码
            
        Returns:
            Dict: 盈利预测数据
        """
        result = {
            'code': code,
            'data': []
        }
        
        if not self.hq_api:
            return result
        
        try:
            market = self._get_market_code(code)
            
            # 连接远程服务器
            if not self._connect_server():
                return result
            
            try:
                # 获取公司信息类别
                category = self.hq_api.get_company_info_category(market, code)
                if not category:
                    return result

                # 找到研报评级（包含盈利预测）
                forecast_info = None
                filename = None
                for item in category:
                    if item['name'] == '研报评级':
                        forecast_info = item
                        filename = item['filename']
                        break

                if not forecast_info:
                    return result

                # 获取研报评级内容
                content = self.hq_api.get_company_info_content(
                    market, code, filename,
                    forecast_info['start'],
                    forecast_info['length']
                )

                if not content:
                    return result

                # 解析盈利预测表格
                table_data = self._parse_forecast_table(content)
                result['data'] = table_data
                logger.info(f"成功获取 {code} 盈利预测数据")
            finally:
                self.hq_api.disconnect()
                
        except Exception as e:
            logger.error(f"获取盈利预测数据失败 {code}: {e}")
        
        return result

    def _parse_forecast_table(self, content: str) -> List[Dict]:
        """解析盈利预测表格"""
        table_data = []
        lines = content.split('\n')
        
        # 找到【2.盈利预测统计】部分
        in_forecast_section = False
        header = []
        
        for line in lines:
            # 检测是否进入盈利预测统计部分
            if '【2.盈利预测统计】' in line:
                in_forecast_section = True
                continue
                
            if not in_forecast_section:
                continue
                
            # 跳过水平线和空行
            line_stripped = line.strip()
            if not line_stripped or all(c in '─┼┬┴' for c in line_stripped):
                continue
                
            # 使用 │ 分割（保留原始字符）
            parts = [p.strip() for p in line.split('│') if p.strip()]
            
            if not parts:
                continue
            
            # 识别表头（第一个字段是'财务指标'或包含多个年份）
            is_header = False
            if len(parts) >= 4:
                # 检查第一个字段是否是财务指标相关
                first_part = parts[0]
                if '财务指标' in first_part or '指标' in first_part:
                    is_header = True
                # 或者检查是否有多个年份字段（排除像'12.20'这样的数值）
                year_count = 0
                for p in parts[1:]:
                    p_str = str(p)
                    # 年份格式应该是 '20XX年' 或 '20XX年预测'
                    if len(p_str) >= 5 and p_str.startswith('20') and (p_str[4] == '年' or (len(p_str) >= 6 and p_str[4:6] == '年预')):
                        year_count += 1
                if year_count >= 3:
                    is_header = True
            
            if is_header:
                header = parts
            elif header and len(parts) >= 2:
                # 确保parts数量与header一致
                if len(parts) > len(header):
                    parts = parts[:len(header)]
                elif len(parts) < len(header):
                    # 补齐缺失的部分
                    parts += ['---'] * (len(header) - len(parts))
                
                row = {}
                for i, h in enumerate(header):
                    row[h] = parts[i]
                
                # 只添加有效数据行（指标名称不为空）
                if row and row.get(header[0]) and row[header[0]]:
                    table_data.append(row)
            
            # 如果遇到新的部分，停止解析
            if '【3.' in line or '【4.' in line:
                break
        
        return table_data

    def get_full_info(self, code: str) -> Dict[str, Any]:
        """
        获取完整的股票信息（公司概况+行情+盈利预测）
        
        Args:
            code: 股票代码
            
        Returns:
            Dict: 完整信息
        """
        return {
            'profile': self.get_company_profile(code),
            'market': self.get_market_data(code),
            'forecast': self.get_profit_forecast(code)
        }

    # ============================================================
    # 数据存储方法
    # ============================================================

    def _has_valid_profile_data(self, profile: Dict) -> bool:
        """
        检查公司概况是否包含有效数据
        
        Args:
            profile: 公司概况数据
            
        Returns:
            bool: 是否有有效数据
        """
        if not profile:
            return False
            
        # 检查关键字段是否有非默认值
        key_fields = ['industry', 'business_scope', 'company_name']
        for field in key_fields:
            if profile.get(field) and profile[field] != '--':
                return True
                
        return False

    def save_company_profile(self, code: str) -> bool:
        """
        采集并保存公司概况到数据库
        
        Args:
            code: 股票代码
            
        Returns:
            bool: 是否成功
        """
        if not self.db_client:
            logger.error("未配置数据库客户端")
            return False
            
        try:
            profile = self.get_company_profile(code)
            
            # 检查是否有有效数据
            if not self._has_valid_profile_data(profile):
                logger.warning(f"{code} 公司概况无有效数据，尝试从股票列表获取行业信息")
                
                # 尝试从股票列表表获取行业信息
                stock_info = self.db_client.query_one(
                    "SELECT industry, name FROM stock_list WHERE code = %s", 
                    (code,)
                )
                if stock_info and stock_info.get('industry'):
                    profile['industry'] = stock_info['industry']
                    profile['company_name'] = stock_info.get('name', '--')
                    logger.info(f"从股票列表获取到 {code} 的行业: {profile['industry']}")
            
            # 转换list_date为整数
            if profile.get('list_date') and profile['list_date'] != '--':
                try:
                    profile['list_date'] = int(profile['list_date'].replace('-', ''))
                except:
                    profile['list_date'] = None
            else:
                profile['list_date'] = None
            
            success = self.db_client.insert_company_profile(profile)
            if success:
                logger.info(f"成功保存 {code} 公司概况")
            return success
            
        except Exception as e:
            logger.error(f"保存公司概况失败 {code}: {e}")
            return False

    def save_market_snapshot(self, code: str) -> bool:
        """
        采集并保存行情快照到数据库
        
        Args:
            code: 股票代码
            
        Returns:
            bool: 是否成功
        """
        if not self.db_client:
            logger.error("未配置数据库客户端")
            return False
            
        try:
            market = self.get_market_data(code)
            if market and market.get('price') > 0:
                success = self.db_client.insert_market_snapshot(market)
                if success:
                    logger.info(f"成功保存 {code} 行情快照")
                return success
            return False
        except Exception as e:
            logger.error(f"保存行情快照失败 {code}: {e}")
            return False

    def save_profit_forecast(self, code: str) -> bool:
        """
        采集并保存盈利预测到数据库
        
        Args:
            code: 股票代码
            
        Returns:
            bool: 是否成功
        """
        if not self.db_client:
            logger.error("未配置数据库客户端")
            return False
            
        try:
            forecast = self.get_profit_forecast(code)
            if forecast and forecast.get('data'):
                # 数据格式: [{'财务指标': '每股收益(元)', '2023年': '0.53', '2024年': '0.57', ...}, ...]
                data_list = []
                
                # 先收集所有年份
                years = set()
                for row in forecast['data']:
                    for key in row.keys():
                        if key != '财务指标':
                            # 提取年份（处理 '2023年', '2026年预测' 等格式）
                            year_match = re.search(r'(\d{4})', key)
                            if year_match:
                                years.add(year_match.group(1))
                
                # 按年份组织数据
                for year in sorted(years):
                    data_item = {
                        'code': code,
                        'year': int(year),
                        'forecast_type': 'forecast',
                        'eps': None,
                        'net_profit': None,
                        'revenue': None,
                        'roe': None,
                        'book_value_ps': None
                    }
                    
                    # 遍历每一行数据，找到对应年份的值
                    for row in forecast['data']:
                        indicator = row.get('财务指标', '')
                        # 查找该年份对应的值（可能是 '2023年' 或 '2023年预测'）
                        value = None
                        for key in row.keys():
                            if key != '财务指标' and year in key:
                                value = row[key]
                                break
                        
                        if value and value != '---' and value != '--':
                            # 根据指标名称保存到对应字段
                            if '每股收益' in indicator:
                                try:
                                    data_item['eps'] = float(value)
                                except:
                                    pass
                            elif '归母净利润' in indicator:
                                try:
                                    data_item['net_profit'] = float(value)  # 已经是百万元
                                except:
                                    pass
                            elif '营业收入' in indicator:
                                try:
                                    data_item['revenue'] = float(value)  # 已经是百万元
                                except:
                                    pass
                            elif '净资产收益率' in indicator:
                                try:
                                    data_item['roe'] = float(value)
                                except:
                                    pass
                            elif '每股净资产' in indicator:
                                try:
                                    data_item['book_value_ps'] = float(value)
                                except:
                                    pass
                    
                    # 只保存有数据的年份
                    has_data = any(data_item[k] is not None for k in ['eps', 'net_profit', 'revenue', 'roe', 'book_value_ps'])
                    if has_data:
                        data_list.append(data_item)
                
                if data_list:
                    count = self.db_client.batch_insert_profit_forecast(data_list)
                    logger.info(f"成功保存 {code} 盈利预测数据 {count} 条")
                    return count > 0
            return False
        except Exception as e:
            logger.error(f"保存盈利预测失败 {code}: {e}")
            return False

    def collect_and_save_all(self, code: str) -> Dict[str, bool]:
        """
        采集并保存所有F10数据
        
        Args:
            code: 股票代码
            
        Returns:
            Dict: 各数据类型的保存结果
        """
        result = {
            'profile': self.save_company_profile(code),
            'market': self.save_market_snapshot(code),
            'forecast': self.save_profit_forecast(code)
        }
        return result


# 测试
if __name__ == '__main__':
    from database.config import DB_CONFIG
    
    # 创建数据库客户端
    db_client = MySQLClient(DB_CONFIG)
    
    # 创建采集器
    collector = F10Collector(db_client=db_client)
    
    # 测试获取公司概况
    profile = collector.get_company_profile('688456')
    print("=== 公司概况 ===")
    print(json.dumps(profile, ensure_ascii=False, indent=2))
    
    # 测试获取行情数据
    market = collector.get_market_data('688456')
    print("\n=== 行情数据 ===")
    print(json.dumps(market, ensure_ascii=False, indent=2))
    
    # 测试获取盈利预测
    forecast = collector.get_profit_forecast('688456')
    print("\n=== 盈利预测 ===")
    print(json.dumps(forecast, ensure_ascii=False, indent=2))
    
    # 测试保存到数据库
    print("\n=== 保存到数据库 ===")
    result = collector.collect_and_save_all('688456')
    print(f"保存结果: {result}")