#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地数据采集器 - 基于workbuddy脚本
功能：从通达信本地目录采集所有A股数据
1. 从.day文件读取历史行情数据
2. 从F10本地文件解析公司信息（行业、主营业务）
3. 保存到数据库
"""

import os
import sys
import json
import struct
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import TDX_DIR, MYSQL_CONFIG
from database.mysql_client import MySQLClient

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class LocalDataCollector:
    """
    本地数据采集器
    """
    
    def __init__(self, tdx_dir: str = TDX_DIR):
        self.tdx_dir = tdx_dir
        self.vipdoc_dir = os.path.join(tdx_dir, "vipdoc")
        
    def get_market(self, code: str) -> int:
        """根据代码判断市场 (1=上海, 0=深圳)"""
        if code.startswith('6') or code.startswith('68'):
            return 1  # 上海
        return 0  # 深圳
        
    def get_market_prefix(self, code: str) -> str:
        """获取市场前缀 (sh/sz)"""
        return 'sh' if self.get_market(code) == 1 else 'sz'
        
    def read_local_daily_data(self, code: str) -> Optional[Dict]:
        """
        从本地通达信日线文件读取最新数据
        
        Args:
            code: 股票代码
            
        Returns:
            包含最新日线数据的字典
        """
        try:
            market = self.get_market_prefix(code)
            day_file = os.path.join(self.vipdoc_dir, market, "lday", f"{market}{code}.day")
            
            if not os.path.exists(day_file):
                return None
                
            with open(day_file, 'rb') as f:
                f.seek(0, 2)
                file_size = f.tell()
                
                if file_size < 32:
                    return None
                    
                f.seek(max(0, file_size - 32), 0)
                data = f.read(32)
                
                # 解析数据 - 使用小端序
                date_int = struct.unpack('<I', data[0:4])[0]
                open_price = struct.unpack('<I', data[4:8])[0] / 100.0
                high_price = struct.unpack('<I', data[8:12])[0] / 100.0
                low_price = struct.unpack('<I', data[12:16])[0] / 100.0
                close_price = struct.unpack('<I', data[16:20])[0] / 100.0
                amount = struct.unpack('<I', data[20:24])[0]
                volume = struct.unpack('<I', data[24:28])[0]
                
                date_str = str(date_int)
                if len(date_str) == 8:
                    date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                else:
                    date = date_str
                
                return {
                    'date': date,
                    'price': close_price,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'amount': amount,
                    'volume': volume,
                    'source': 'local_tdx'
                }
                
        except Exception as e:
            logger.warning(f"读取本地日线数据失败 {code}: {e}")
            return None
            
    def read_historical_data(self, code: str, days: int = 60) -> List[Dict]:
        """
        读取历史日线数据
        
        Args:
            code: 股票代码
            days: 要读取的天数
            
        Returns:
            历史数据列表
        """
        try:
            market = self.get_market_prefix(code)
            day_file = os.path.join(self.vipdoc_dir, market, "lday", f"{market}{code}.day")
            
            if not os.path.exists(day_file):
                return []
                
            with open(day_file, 'rb') as f:
                f.seek(0, 2)
                file_size = f.tell()
                
                record_size = 32
                start_pos = max(0, file_size - days * record_size)
                f.seek(start_pos, 0)
                
                data = f.read()
                
                records = []
                for i in range(0, len(data), record_size):
                    if i + record_size > len(data):
                        break
                        
                    record = data[i:i+record_size]
                    
                    date_int = struct.unpack('<I', record[0:4])[0]
                    open_price = struct.unpack('<I', record[4:8])[0] / 100.0
                    high_price = struct.unpack('<I', record[8:12])[0] / 100.0
                    low_price = struct.unpack('<I', record[12:16])[0] / 100.0
                    close_price = struct.unpack('<I', record[16:20])[0] / 100.0
                    amount = struct.unpack('<I', record[20:24])[0] / 100.0
                    volume = struct.unpack('<I', record[24:28])[0]
                    
                    date_str = str(date_int)
                    if len(date_str) == 8:
                        date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                    else:
                        date = date_str
                        
                    if len(records) > 0:
                        prev_close = records[-1]['price']
                        change_pct = (close_price - prev_close) / prev_close * 100 if prev_close > 0 else 0
                    else:
                        change_pct = 0
                        
                    records.append({
                        'date': date,
                        'price': close_price,
                        'open': open_price,
                        'high': high_price,
                        'low': low_price,
                        'change_pct': change_pct,
                        'amount': amount,
                        'volume': volume
                    })
                
                return records
                
        except Exception as e:
            logger.warning(f"读取历史数据失败 {code}: {e}")
            return []
            
    def get_company_info_from_local(self, code: str) -> Dict:
        """
        从通达信本地文件获取公司信息
        
        Args:
            code: 股票代码
            
        Returns:
            公司信息字典
        """
        info = {
            'code': code,
            'name': '',
            'industry': '',
            'main_business': '',
            'list_date': 0,
            'total_shares': '',
            'circulating_shares': ''
        }
        
        # 首先尝试从workbuddy的stock_report_data.json读取数据
        workbuddy_data = self._load_workbuddy_data(code)
        if workbuddy_data:
            info.update(workbuddy_data)
        
        # 如果workbuddy没有数据，再尝试从本地文件获取
        market = self.get_market_prefix(code)
        
        # 尝试从block.cfg获取行业信息
        block_file = os.path.join(self.vipdoc_dir, market, "blocknew", "block.cfg")
        if os.path.exists(block_file) and not info.get('industry'):
            industry = self._parse_block_file_for_industry(block_file, code)
            if industry:
                info['industry'] = industry
        
        # 尝试从base.dbf获取公司基本信息
        base_dbf = os.path.join(self.tdx_dir, "T0002", "hq_cache", "base.dbf")
        if os.path.exists(base_dbf) and not info.get('name'):
            base_info = self._parse_base_dbf(base_dbf, code)
            if base_info:
                info.update(base_info)
        
        # 尝试从F10文件获取主营业务
        f10_dir = os.path.join(self.vipdoc_dir, market, "fzline")
        if os.path.exists(f10_dir) and not info.get('main_business'):
            f10_info = self._parse_f10_files(f10_dir, code)
            if f10_info:
                info.update(f10_info)
        
        return info
        
    def _load_workbuddy_data(self, code: str) -> Optional[Dict]:
        """从workbuddy的stock_report_data.json加载数据"""
        workbuddy_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "workbuddy", "stock_report_data.json")
        if not os.path.exists(workbuddy_file):
            return None
            
        try:
            with open(workbuddy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 检查代码是否匹配
            data_code = data.get('code', '').replace('SH', '').replace('SZ', '')
            if data_code != code:
                return None
                
            company = data.get('company', {})
            if company:
                return {
                    'name': company.get('name', ''),
                    'industry': company.get('industry', ''),
                    'main_business': company.get('main_business', ''),
                    'list_date': company.get('listing_date', 0),
                    'total_shares': str(company.get('total_shares', ''))
                }
        except Exception as e:
            logger.debug(f'加载workbuddy数据失败: {e}')
            
        return None
        
    def _parse_block_file_for_industry(self, block_file: str, code: str) -> Optional[str]:
        """从block.cfg解析行业信息"""
        try:
            # 简化处理，实际需要根据通达信文件格式解析
            # 这里先尝试通过akshare作为备选方案
            try:
                import akshare as ak
                stock_info = ak.stock_individual_info_em(symbol=code)
                if not stock_info.empty:
                    industry = stock_info.loc[stock_info['item'] == '所属行业', 'value'].values[0] if '所属行业' in stock_info['item'].values else ''
                    return industry
            except:
                pass
            return None
        except Exception as e:
            logger.debug(f"解析block.cfg失败 {code}: {e}")
            return None
            
    def _parse_base_dbf(self, base_dbf: str, code: str) -> Optional[Dict]:
        """从base.dbf解析公司基本信息"""
        try:
            # 尝试使用dbf库读取
            try:
                from dbfread import DBF
                table = DBF(base_dbf, encoding='gbk')
                for record in table:
                    if record.get('DM') == code or record.get('CODE') == code:
                        return {
                            'name': record.get('NAME', ''),
                            'list_date': int(record.get('SSDATE', 0)) if record.get('SSDATE') else 0
                        }
            except ImportError:
                # 如果没有dbf库，尝试通过akshare
                try:
                    import akshare as ak
                    stock_info = ak.stock_individual_info_em(symbol=code)
                    if not stock_info.empty:
                        return {
                            'name': stock_info.loc[stock_info['item'] == '股票简称', 'value'].values[0] if '股票简称' in stock_info['item'].values else '',
                            'list_date': int(stock_info.loc[stock_info['item'] == '上市时间', 'value'].values[0]) if '上市时间' in stock_info['item'].values else 0
                        }
                except:
                    pass
            return None
        except Exception as e:
            logger.debug(f"解析base.dbf失败 {code}: {e}")
            return None
            
    def _parse_f10_files(self, f10_dir: str, code: str) -> Optional[Dict]:
        """从F10文件解析主营业务"""
        try:
            # 简化处理
            # 尝试通过akshare获取主营业务
            try:
                import akshare as ak
                stock_info = ak.stock_individual_info_em(symbol=code)
                if not stock_info.empty:
                    main_business = stock_info.loc[stock_info['item'] == '主营业务', 'value'].values[0] if '主营业务' in stock_info['item'].values else ''
                    return {'main_business': main_business}
            except:
                pass
            return None
        except Exception as e:
            logger.debug(f"解析F10文件失败 {code}: {e}")
            return None
            
    def collect_and_save(self, db_client: MySQLClient, code: str):
        """
        采集并保存单只股票的数据
        
        Args:
            db_client: 数据库客户端
            code: 股票代码
        """
        logger.info(f"开始采集 {code}...")
        
        # 1. 采集本地日线数据
        daily_data = self.read_local_daily_data(code)
        
        # 2. 采集公司信息
        company_info = self.get_company_info_from_local(code)
        
        # 3. 保存到数据库
        try:
            # 保存公司概况
            if company_info:
                self._save_company_profile(db_client, company_info)
                
            # 保存市场快照
            if daily_data:
                self._save_market_snapshot(db_client, code, daily_data)
                
            # 更新stock_list
            if company_info or daily_data:
                self._update_stock_list(db_client, code, company_info, daily_data)
                
            logger.info(f"{code} 采集完成")
            return True
            
        except Exception as e:
            logger.error(f"保存 {code} 数据失败: {e}")
            return False
            
    def _save_company_profile(self, db_client: MySQLClient, company_info: Dict):
        """保存公司概况"""
        try:
            conn = db_client.connect()
            sql = """
                INSERT INTO company_profile 
                (code, company_name, industry, business_scope, list_date, reg_capital)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                company_name=VALUES(company_name), industry=VALUES(industry),
                business_scope=VALUES(business_scope), list_date=VALUES(list_date),
                reg_capital=VALUES(reg_capital)
            """
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    company_info['code'],
                    company_info.get('name', ''),
                    company_info.get('industry', ''),
                    company_info.get('main_business', ''),
                    company_info.get('list_date', 0),
                    company_info.get('total_shares', '')
                ))
            db_client.commit()
        except Exception as e:
            logger.warning(f"保存公司概况失败 {company_info['code']}: {e}")
            
    def _save_market_snapshot(self, db_client: MySQLClient, code: str, daily_data: Dict):
        """保存市场快照"""
        try:
            conn = db_client.connect()
            sql = """
                INSERT INTO market_snapshot 
                (code, price, high, low, open, volume, amount, snapshot_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                price=VALUES(price), high=VALUES(high), low=VALUES(low),
                open=VALUES(open), volume=VALUES(volume), amount=VALUES(amount),
                snapshot_time=NOW()
            """
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    code,
                    daily_data['price'],
                    daily_data['high'],
                    daily_data['low'],
                    daily_data['open'],
                    daily_data['volume'],
                    daily_data['amount']
                ))
            db_client.commit()
        except Exception as e:
            logger.warning(f"保存市场快照失败 {code}: {e}")
            
    def _update_stock_list(self, db_client: MySQLClient, code: str, company_info: Dict, daily_data: Dict):
        """更新stock_list"""
        try:
            conn = db_client.connect()
            
            # 检查是否有需要的列
            try:
                check_sql = "SHOW COLUMNS FROM stock_list LIKE 'current_price'"
                has_col = db_client.query_one(check_sql)
                if not has_col:
                    add_sql = "ALTER TABLE stock_list ADD COLUMN current_price DECIMAL(10,2), ADD COLUMN change_pct DECIMAL(6,2), ADD COLUMN market_cap DECIMAL(20,2), ADD COLUMN pe_ratio DECIMAL(10,2)"
                    db_client.execute(add_sql)
            except Exception:
                pass
                
            # 更新股票信息
            name = company_info.get('name', f'股票{code}') if company_info else f'股票{code}'
            industry = company_info.get('industry', '') if company_info else ''
            market = self.get_market(code)
            
            sql = """
                INSERT INTO stock_list (code, name, market, industry, status)
                VALUES (%s, %s, %s, %s, 'active')
                ON DUPLICATE KEY UPDATE
                name=VALUES(name), industry=VALUES(industry)
            """
            with conn.cursor() as cursor:
                cursor.execute(sql, (code, name, market, industry))
            db_client.commit()
        except Exception as e:
            logger.warning(f"更新stock_list失败 {code}: {e}")
            
    def get_stock_codes_from_local(self) -> List[str]:
        """从本地获取股票代码列表"""
        codes = set()
        
        # 上海市场
        sh_dir = os.path.join(self.vipdoc_dir, "sh", "lday")
        if os.path.exists(sh_dir):
            for file_name in os.listdir(sh_dir):
                if file_name.endswith(".day"):
                    code = file_name.replace("sh", "").replace(".day", "")
                    if code.isdigit() and len(code) == 6:
                        codes.add(code)
        
        # 深圳市场
        sz_dir = os.path.join(self.vipdoc_dir, "sz", "lday")
        if os.path.exists(sz_dir):
            for file_name in os.listdir(sz_dir):
                if file_name.endswith(".day"):
                    code = file_name.replace("sz", "").replace(".day", "")
                    if code.isdigit() and len(code) == 6:
                        codes.add(code)
        
        return sorted(list(codes))
        
    def batch_collect(self, db_client: MySQLClient, codes: List[str] = None, limit: int = None):
        """批量采集"""
        if not codes:
            codes = self.get_stock_codes_from_local()
            
        if limit and limit > 0:
            codes = codes[:limit]
            
        logger.info(f"准备采集 {len(codes)} 只股票...")
        
        success_count = 0
        fail_count = 0
        
        for i, code in enumerate(codes, 1):
            logger.info(f"[{i}/{len(codes)}] 采集 {code}...")
            try:
                if self.collect_and_save(db_client, code):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"采集 {code} 异常: {e}")
                fail_count += 1
                
        logger.info(f"采集完成！成功: {success_count}, 失败: {fail_count}")
        return {'success': success_count, 'fail': fail_count, 'total': len(codes)}


def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("本地数据采集器启动 - 基于workbuddy脚本")
    logger.info("=" * 60)
    
    import argparse
    parser = argparse.ArgumentParser(description='本地数据采集器')
    parser.add_argument('--code', help='单只股票代码')
    parser.add_argument('--limit', type=int, help='限制采集数量')
    args = parser.parse_args()
    
    # 检查通达信目录
    if not os.path.exists(TDX_DIR):
        logger.error(f"通达信目录不存在: {TDX_DIR}")
        return
        
    # 创建数据库客户端
    db_client = MySQLClient(MYSQL_CONFIG)
    collector = LocalDataCollector(TDX_DIR)
    
    try:
        if args.code:
            # 单只股票采集
            collector.collect_and_save(db_client, args.code)
        else:
            # 批量采集
            collector.batch_collect(db_client, limit=args.limit)
            
    except Exception as e:
        logger.error(f"采集过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db_client.close()


if __name__ == '__main__':
    main()
