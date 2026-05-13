#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度财经股票数据抓取器
使用完善的反爬机制访问百度财经页面
"""

import os
import sys
import time
import random
import re
import json
from datetime import datetime
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup
import pymysql

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MYSQL_CONFIG


class BaiduFinanceFetcher:
    """百度财经数据抓取器（带反爬机制）"""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    ]
    
    ACCEPT_LANGUAGES = [
        'zh-CN,zh;q=0.9,en;q=0.8',
        'zh-CN,zh;q=0.9',
        'zh;q=1.0,en;q=0.5',
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """配置Session，添加反爬相关设置"""
        # 随机User-Agent
        self.session.headers.update({
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Language': random.choice(self.ACCEPT_LANGUAGES),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # 设置超时时间
        self.session.timeout = 30
        
        # 设置连接池大小
        self.session.adapters.DEFAULT_RETRIES = 3
    
    def _random_delay(self, min_delay=1.5, max_delay=3.5):
        """随机延迟，避免被识别为爬虫"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def _rotate_user_agent(self):
        """轮换User-Agent"""
        self.session.headers['User-Agent'] = random.choice(self.USER_AGENTS)
    
    def _get_url(self, code: str) -> str:
        """构建百度财经URL"""
        return f'https://finance.baidu.com/stock/ab-{code}?mainTab=%E6%A6%82%E8%A7%88'
    
    def fetch_stock_data(self, code: str) -> Optional[Dict]:
        """
        抓取股票数据
        
        Args:
            code: 股票代码
            
        Returns:
            Dict: 股票数据
        """
        try:
            # 轮换User-Agent
            self._rotate_user_agent()
            
            # 随机延迟
            self._random_delay()
            
            # 获取页面
            url = self._get_url(code)
            print(f"正在访问: {url}")
            
            response = self.session.get(url)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"请求失败: {response.status_code}")
                # 尝试重新请求
                self._random_delay(2, 4)
                self._rotate_user_agent()
                response = self.session.get(url)
                if response.status_code != 200:
                    print(f"再次请求失败: {response.status_code}")
                    return None
            
            html_content = response.text
            
            # 检查是否被拦截
            if '验证' in html_content or '安全验证' in html_content or '请稍后重试' in html_content:
                print("请求被拦截，需要验证")
                return None
            
            # 解析页面中的JSON数据
            # 百度财经页面使用JavaScript渲染，数据通常在<script>标签中的JSON对象里
            data = self._parse_html(html_content, code)
            
            if data:
                print(f"成功抓取股票 {code} 的数据")
                return data
            else:
                print("未找到有效数据")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"网络请求失败 {code}: {e}")
            return None
        except Exception as e:
            print(f"抓取失败 {code}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_html(self, html_content: str, code: str) -> Optional[Dict]:
        """解析HTML页面提取数据"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 首先尝试从页面中的script标签提取数据
        scripts = soup.find_all('script')
        
        for script in scripts:
            script_content = script.string
            if not script_content:
                continue
            
            # 尝试提取各种格式的JSON数据
            # 格式1: window.__INITIAL_STATE__ = {...}
            json_match = re.search(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', script_content, re.DOTALL)
            if json_match:
                try:
                    json_data = json.loads(json_match.group(1))
                    result = self._parse_json_data(json_data, code)
                    if result:
                        return result
                except:
                    pass
            
            # 格式2: window.__DATA__ = {...}
            json_match = re.search(r'window\.__DATA__\s*=\s*({.*?});', script_content, re.DOTALL)
            if json_match:
                try:
                    json_data = json.loads(json_match.group(1))
                    result = self._parse_json_data(json_data, code)
                    if result:
                        return result
                except:
                    pass
            
            # 格式3: var data = {...}
            json_match = re.search(r'var\s+data\s*=\s*({.*?});', script_content, re.DOTALL)
            if json_match:
                try:
                    json_data = json.loads(json_match.group(1))
                    result = self._parse_json_data(json_data, code)
                    if result:
                        return result
                except:
                    pass
            
            # 格式4: 查找包含股票代码的数组
            if code in script_content:
                # 尝试查找数组格式
                array_match = re.search(r'\[\s*\{[^\}]+\}\s*\]', script_content)
                if array_match:
                    try:
                        json_data = json.loads(array_match.group(0))
                        if isinstance(json_data, list) and len(json_data) > 0:
                            result = self._parse_json_data(json_data[0], code)
                            if result:
                                return result
                    except:
                        pass
        
        # 如果没有找到JSON数据，尝试解析页面中的静态内容
        static_result = self._parse_static_content(soup, code)
        if static_result:
            print(f"从静态内容获取到数据")
            return static_result
        
        # 如果都不行，尝试使用备用API
        print(f"尝试使用备用API获取数据")
        return self._try_alternative_api(code)
    
    def _parse_json_data(self, json_data: Dict, code: str) -> Optional[Dict]:
        """解析JSON数据"""
        try:
            # 尝试不同的数据结构
            data = {
                'code': code,
                'market': 'sh' if code.startswith('6') else 'sz',
                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 尝试从不同路径获取数据
            stock_data = json_data
            if 'data' in json_data:
                stock_data = json_data['data']
            if 'stockInfo' in stock_data:
                stock_data = stock_data['stockInfo']
            if isinstance(stock_data, list) and len(stock_data) > 0:
                stock_data = stock_data[0]
            
            # 提取股票名称
            if 'name' in stock_data:
                data['name'] = stock_data['name']
            elif 'stockName' in stock_data:
                data['name'] = stock_data['stockName']
            
            # 提取交易所和板块信息
            if 'exchange' in stock_data:
                data['exchange'] = stock_data['exchange']
            else:
                data['exchange'] = '上海交易所' if code.startswith('6') else '深圳交易所'
            
            if 'plate' in stock_data:
                data['plate'] = stock_data['plate']
            if 'industry' in stock_data:
                data['industry'] = stock_data['industry']
            if 'sector' in stock_data:
                data['plate'] = stock_data['sector']
            
            # 提取价格信息
            price_fields = ['price', 'currentPrice', 'latestPrice', 'last']
            for field in price_fields:
                if field in stock_data and stock_data[field]:
                    data['current_price'] = self._parse_float(stock_data[field])
                    break
            
            change_fields = ['change', 'changeAmount', 'delta']
            for field in change_fields:
                if field in stock_data and stock_data[field]:
                    data['price_change'] = self._parse_float(stock_data[field])
                    break
            
            percent_fields = ['changePercent', 'percent', 'change_percent']
            for field in percent_fields:
                if field in stock_data and stock_data[field]:
                    data['change_percent'] = self._parse_float(stock_data[field])
                    break
            
            # 提取行情数据
            data['open_price'] = self._parse_float(stock_data.get('open'))
            data['prev_close'] = self._parse_float(stock_data.get('prevClose'))
            data['high_price'] = self._parse_float(stock_data.get('high'))
            data['low_price'] = self._parse_float(stock_data.get('low'))
            
            # 成交量（转换为手）
            volume = stock_data.get('volume')
            if volume:
                data['volume'] = int(float(volume) / 100)
            
            # 成交额（转换为元）
            amount = stock_data.get('amount')
            if amount:
                data['amount'] = float(amount)
            
            # 总市值（转换为元）
            market_cap = stock_data.get('marketCap') or stock_data.get('market_cap')
            if market_cap:
                mc = float(market_cap)
                if mc < 10000:  # 单位是亿
                    data['market_cap'] = mc * 100000000
                else:
                    data['market_cap'] = mc
            
            # 市盈率
            data['pe_ttm'] = self._parse_float(stock_data.get('pe') or stock_data.get('pe_ttm'))
            
            # 更新时间
            time_fields = ['time', 'updateTime', 'update_time', 'tradeTime']
            for field in time_fields:
                if field in stock_data and stock_data[field]:
                    data['update_time'] = str(stock_data[field])
                    break
            
            # 如果没有获取到核心数据，返回None
            if 'current_price' not in data:
                return None
            
            return data
            
        except Exception as e:
            print(f"解析JSON数据失败: {e}")
            return None
    
    def _parse_static_content(self, soup: BeautifulSoup, code: str) -> Optional[Dict]:
        """解析页面静态内容"""
        try:
            data = {
                'code': code,
                'market': 'sh' if code.startswith('6') else 'sz',
                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 查找股票名称
            name_elem = soup.find('h1', class_='stock-name')
            if not name_elem:
                name_elem = soup.find('span', class_='stock-name')
            if name_elem:
                data['name'] = name_elem.get_text(strip=True)
            
            # 查找价格信息
            price_elem = soup.find('span', class_='price') or soup.find('span', class_='num')
            if price_elem:
                data['current_price'] = self._parse_float(price_elem.get_text())
            
            # 查找涨跌信息
            change_elem = soup.find('span', class_='change')
            if change_elem:
                change_text = change_elem.get_text(strip=True)
                match = re.search(r'([+\-]?[\d.]+)', change_text)
                if match:
                    data['price_change'] = self._parse_float(match.group(1))
            
            # 查找涨跌幅
            percent_elem = soup.find('span', class_='changepercent')
            if not percent_elem:
                percent_elem = soup.find('span', class_='percent')
            if percent_elem:
                data['change_percent'] = self._parse_float(percent_elem.get_text().replace('%', ''))
            
            # 如果没有获取到核心数据，返回None
            if 'current_price' not in data:
                return None
            
            return data
            
        except Exception as e:
            print(f"解析静态内容失败: {e}")
            return None
    
    def _parse_float(self, value) -> Optional[float]:
        """解析浮点数值"""
        if value is None:
            return None
        try:
            return float(str(value).replace(',', '').replace('%', ''))
        except:
            return None
    
    def _parse_plate(self, plate_code: str) -> str:
        """解析板块代码为中文名称"""
        if not plate_code:
            return ''
        
        # 板块代码映射表
        plate_map = {
            'GP-A-KCB': '科创板',
            'GP-A-SZ': '创业板',
            'GP-A-SH': '沪市A股',
            'GP-A-SZA': '深市A股',
            'GP-B-SH': '沪市B股',
            'GP-B-SZ': '深市B股',
        }
        
        # 尝试精确匹配
        if plate_code in plate_map:
            return plate_map[plate_code]
        
        # 尝试模糊匹配
        if 'KCB' in plate_code:
            return '科创板'
        elif 'SZ' in plate_code:
            return '创业板'
        elif 'SH' in plate_code:
            return '沪市A股'
        
        return ''
    
    def _try_alternative_api(self, code: str) -> Optional[Dict]:
        """尝试使用备用API获取数据"""
        try:
            market = 'sh' if code.startswith('6') else 'sz'
            
            # 尝试腾讯财经API（最稳定）
            url = f'http://qt.gtimg.cn/q={market}{code}'
            
            self._rotate_user_agent()
            response = self.session.get(url)
            response.encoding = 'gbk'
            
            if response.status_code == 200:
                content = response.text
                # 腾讯财经格式: v_sh688456="1~有研粉材~688456~86.26~..."
                match = re.search(r'v_\w+=\s*["\']([^"\']+)["\']', content)
                if match:
                    data_str = match.group(1)
                    fields = data_str.split('~')
                    if len(fields) >= 73:
                        # 解析腾讯财经数据字段
                        # 字段索引:
                        # 1: 名称, 3: 当前价, 4: 开盘价, 5: 昨收
                        # 6: 成交量(股), 31: 涨跌额, 32: 涨跌幅%
                        # 33: 最高价, 34: 最低价, 37: 成交额(万)
                        # 38: 换手率%, 39: 市盈率, 45: 总市值(亿)
                        # 46: 流通市值(亿), 47: 市盈率TTM, 56: 量比
                        # 57: 成交额(万), 72: 总股本(股)
                        data = {
                            'code': code,
                            'market': market,
                            'name': fields[1],
                            'current_price': self._parse_float(fields[3]),
                            'open_price': self._parse_float(fields[4]),
                            'prev_close': self._parse_float(fields[5]),
                            'high_price': self._parse_float(fields[33]),
                            'low_price': self._parse_float(fields[34]),
                            'volume': int(float(fields[6])) if fields[6] else None,  # 成交量(股)
                            'amount': float(fields[57]) * 10000 if fields[57] else None,  # 成交金额(万)转元
                            'price_change': self._parse_float(fields[31]),
                            'change_percent': self._parse_float(fields[32]),
                            'turnover_rate': self._parse_float(fields[38]),  # 换手率
                            'pe_ttm': self._parse_float(fields[39]),  # 市盈率
                            'market_cap': float(fields[45]) * 100000000 if fields[45] else None,  # 总市值(亿)转元
                            'float_cap': float(fields[46]) * 100000000 if fields[46] else None,  # 流通市值(亿)转元
                            'total_shares': int(float(fields[72])) if fields[72] else None,  # 总股本(股)
                            'volume_ratio': self._parse_float(fields[56]),  # 量比
                            'update_time': fields[30],  # 更新时间
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'exchange': '上海交易所' if code.startswith('6') else '深圳交易所',
                            'plate': self._parse_plate(fields[61]) if len(fields) > 61 else '',  # 板块
                            'industry': fields[50].strip() if len(fields) > 50 and fields[50] else ''  # 行业代码
                        }
                        print(f"使用腾讯财经API获取到数据")
                        return data
            
            # 尝试新浪财经API
            url = f'https://hq.sinajs.cn/list={market}{code}'
            response = self.session.get(url)
            response.encoding = 'gbk'
            
            if response.status_code == 200:
                content = response.text
                # 新浪财经格式: var hq_str_sh600000="浦发银行,10.00,10.01,..."
                match = re.search(r'var hq_str_\w+=\s*["\']([^"\']+)["\']', content)
                if match:
                    data_str = match.group(1)
                    fields = data_str.split(',')
                    if len(fields) >= 30:
                        data = {
                            'code': code,
                            'market': market,
                            'name': fields[0],
                            'current_price': self._parse_float(fields[3]),
                            'open_price': self._parse_float(fields[1]),
                            'prev_close': self._parse_float(fields[2]),
                            'high_price': self._parse_float(fields[4]),
                            'low_price': self._parse_float(fields[5]),
                            'volume': int(float(fields[8])) if fields[8] else None,
                            'amount': float(fields[9]) * 100 if fields[9] else None,
                            'price_change': self._parse_float(fields[3]) - self._parse_float(fields[2]) if fields[3] and fields[2] else None,
                            'change_percent': self._parse_float(fields[32]) if len(fields) > 32 else None,
                            'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'exchange': '上海交易所' if code.startswith('6') else '深圳交易所'
                        }
                        print(f"使用新浪财经API获取到数据")
                        return data
            
            return None
            
        except Exception as e:
            print(f"备用API获取失败: {e}")
            import traceback
            traceback.print_exc()
            return None


class StockMarketDataDB:
    """股票行情数据数据库操作类"""
    
    def __init__(self, config):
        self.config = config
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        self.conn = pymysql.connect(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['user'],
            password=self.config['password'],
            database=self.config['database'],
            charset='utf8mb4'
        )
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
    
    def create_table(self):
        """创建股票行情数据表"""
        try:
            cursor = self.conn.cursor()
            
            sql = """
            CREATE TABLE IF NOT EXISTS stock_market_data (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                code VARCHAR(10) NOT NULL,
                name VARCHAR(50),
                market VARCHAR(10),
                exchange VARCHAR(50),
                plate VARCHAR(100),
                industry VARCHAR(100),
                current_price DECIMAL(10,2),
                price_change DECIMAL(10,2),
                change_percent DECIMAL(10,2),
                open_price DECIMAL(10,2),
                prev_close DECIMAL(10,2),
                high_price DECIMAL(10,2),
                low_price DECIMAL(10,2),
                volume BIGINT,
                amount DECIMAL(20,2),
                market_cap DECIMAL(20,2),
                total_shares DECIMAL(20,2),
                float_cap DECIMAL(20,2),
                turnover_rate DECIMAL(10,2),
                volume_ratio DECIMAL(10,2),
                order_ratio DECIMAL(10,2),
                amplitude DECIMAL(10,2),
                pe_ttm DECIMAL(10,2),
                pe_static DECIMAL(10,2),
                update_time VARCHAR(50),
                crawl_time DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uk_code (code)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
            
            cursor.execute(sql)
            self.conn.commit()
            print("表创建成功")
            
        except Exception as e:
            print(f"创建表失败: {e}")
    
    def save_data(self, data: Dict):
        """保存股票行情数据"""
        try:
            cursor = self.conn.cursor()
            
            sql = """
            INSERT INTO stock_market_data (
                code, name, market, exchange, plate, industry,
                current_price, price_change, change_percent,
                open_price, prev_close, high_price, low_price,
                volume, amount, market_cap, total_shares, float_cap,
                turnover_rate, volume_ratio, order_ratio, amplitude,
                pe_ttm, pe_static, update_time, crawl_time
            ) VALUES (
                %s, %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                name = VALUES(name),
                market = VALUES(market),
                exchange = VALUES(exchange),
                plate = VALUES(plate),
                industry = VALUES(industry),
                current_price = VALUES(current_price),
                price_change = VALUES(price_change),
                change_percent = VALUES(change_percent),
                open_price = VALUES(open_price),
                prev_close = VALUES(prev_close),
                high_price = VALUES(high_price),
                low_price = VALUES(low_price),
                volume = VALUES(volume),
                amount = VALUES(amount),
                market_cap = VALUES(market_cap),
                total_shares = VALUES(total_shares),
                float_cap = VALUES(float_cap),
                turnover_rate = VALUES(turnover_rate),
                volume_ratio = VALUES(volume_ratio),
                order_ratio = VALUES(order_ratio),
                amplitude = VALUES(amplitude),
                pe_ttm = VALUES(pe_ttm),
                pe_static = VALUES(pe_static),
                update_time = VALUES(update_time),
                crawl_time = VALUES(crawl_time),
                updated_at = CURRENT_TIMESTAMP
            """
            
            cursor.execute(sql, (
                data.get('code'),
                data.get('name'),
                data.get('market'),
                data.get('exchange'),
                data.get('plate'),
                data.get('industry'),
                data.get('current_price'),
                data.get('price_change'),
                data.get('change_percent'),
                data.get('open_price'),
                data.get('prev_close'),
                data.get('high_price'),
                data.get('low_price'),
                data.get('volume'),
                data.get('amount'),
                data.get('market_cap'),
                data.get('total_shares'),
                data.get('float_cap'),
                data.get('turnover_rate'),
                data.get('volume_ratio'),
                data.get('order_ratio'),
                data.get('amplitude'),
                data.get('pe_ttm'),
                data.get('pe_static'),
                data.get('update_time'),
                data.get('crawl_time')
            ))
            
            self.conn.commit()
            print(f"数据保存成功: {data.get('code')} {data.get('name')}")
            
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def get_stock_data(self, code: str) -> Optional[Dict]:
        """获取股票行情数据"""
        try:
            cursor = self.conn.cursor(pymysql.cursors.DictCursor)
            
            sql = "SELECT * FROM stock_market_data WHERE code = %s ORDER BY crawl_time DESC LIMIT 1"
            cursor.execute(sql, (code,))
            
            result = cursor.fetchone()
            return result
            
        except Exception as e:
            print(f"获取数据失败: {e}")
            return None


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python baidu_finance_fetcher.py <股票代码>")
        print("示例: python baidu_finance_fetcher.py 688456")
        sys.exit(1)
    
    code = sys.argv[1]
    
    # 初始化抓取器和数据库
    fetcher = BaiduFinanceFetcher()
    db = StockMarketDataDB(MYSQL_CONFIG)
    
    try:
        # 连接数据库并创建表
        db.connect()
        db.create_table()
        
        # 抓取数据
        print(f"开始抓取股票 {code} 的数据...")
        data = fetcher.fetch_stock_data(code)
        
        if data:
            print("抓取到的数据:")
            for key, value in data.items():
                print(f"  {key}: {value}")
            
            # 保存数据
            db.save_data(data)
        else:
            print("未抓取到数据")
            
    finally:
        db.close()


if __name__ == '__main__':
    main()
