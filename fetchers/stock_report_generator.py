#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票数据采集与展示工具
采集并生成HTML报告
"""

import os
import sys
import json
import datetime
import struct
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    print("警告: akshare 未安装")


def read_local_daily_data(tdx_path: str, code: str) -> dict:
    """
    从本地通达信日线文件读取数据
    
    Args:
        tdx_path: 通达信安装目录
        code: 股票代码 (如 sh688456)
        
    Returns:
        包含最新日线数据的字典
    """
    try:
        market = code[:2].lower()
        code_num = code[2:]
        
        day_file = Path(tdx_path) / "vipdoc" / market / "lday" / f"{market}{code_num}.day"
        
        if not day_file.exists():
            return {}
        
        with open(day_file, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            
            # 读取最后一条记录
            f.seek(max(0, file_size - 32), 0)
            data = f.read(32)
            
            if len(data) < 32:
                return {}
            
            # 解析数据 - 使用小端序
            date_int = struct.unpack('<I', data[0:4])[0]
            open_price = struct.unpack('<I', data[4:8])[0] / 100.0
            high_price = struct.unpack('<I', data[8:12])[0] / 100.0
            low_price = struct.unpack('<I', data[12:16])[0] / 100.0
            close_price = struct.unpack('<I', data[16:20])[0] / 100.0
            amount = struct.unpack('<I', data[20:24])[0]  # 成交额（亿元，需要除以10）
            volume = struct.unpack('<I', data[24:28])[0]           # 成交量（手）
            
            # 转换日期
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
        print(f"读取本地日线数据失败: {e}")
        return {}


def read_historical_data(tdx_path: str, code: str, days: int = 60) -> list:
    """
    读取历史日线数据
    
    Args:
        tdx_path: 通达信安装目录
        code: 股票代码
        days: 要读取的天数
        
    Returns:
        历史数据列表
    """
    try:
        market = code[:2].lower()
        code_num = code[2:]
        
        day_file = Path(tdx_path) / "vipdoc" / market / "lday" / f"{market}{code_num}.day"
        
        if not day_file.exists():
            return []
        
        with open(day_file, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            
            # 读取最后N条记录
            record_size = 32
            start_pos = max(0, file_size - days * record_size)
            f.seek(start_pos, 0)
            
            data = f.read()
            
            records = []
            for i in range(0, len(data), record_size):
                if i + record_size > len(data):
                    break
                    
                record = data[i:i+record_size]
                
                # 使用小端序解析
                date_int = struct.unpack('<I', record[0:4])[0]
                open_price = struct.unpack('<I', record[4:8])[0] / 100.0
                high_price = struct.unpack('<I', record[8:12])[0] / 100.0
                low_price = struct.unpack('<I', record[12:16])[0] / 100.0
                close_price = struct.unpack('<I', record[16:20])[0] / 100.0
                
                # 成交额和成交量单位调整（都是 uint32）
                amount = struct.unpack('<I', record[20:24])[0] / 100.0  # 成交额（元 -> 百元）
                volume = struct.unpack('<I', record[24:28])[0]            # 成交量（手）
                
                date_str = str(date_int)
                if len(date_str) == 8:
                    date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                else:
                    date = date_str
                
                # 计算涨跌幅（需要前一天的收盘价）
                if len(records) > 0:
                    prev_close = records[-1]['price']
                    change_pct = (close_price - prev_close) / prev_close * 100
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
        print(f"读取历史数据失败: {e}")
        return []


def get_realtime_from_akshare(code: str) -> dict:
    """从akshare获取实时行情"""
    if not AKSHARE_AVAILABLE:
        return {}
    
    try:
        code_num = code[-6:]
        df = ak.stock_zh_a_spot_em()
        row = df[df['代码'] == code_num]
        
        if row.empty:
            return {}
        
        row = row.iloc[0]
        
        return {
            'price': float(row.get('最新价', 0)),
            'change_pct': float(row.get('涨跌幅', 0)),
            'change_amount': float(row.get('涨跌额', 0)),
            'open': float(row.get('今开', 0)),
            'high': float(row.get('最高', 0)),
            'low': float(row.get('最低', 0)),
            'volume': int(row.get('成交量', 0)),
            'amount': float(row.get('成交额', 0)),
            'turnover': float(row.get('换手率', 0)),
            'pe_ratio': float(row.get('市盈率-动态', 0)) if str(row.get('市盈率-动态', '-')) != '-' else 0,
            'market_cap': float(row.get('总市值', 0)),
            'circulating_market_cap': float(row.get('流通市值', 0)),
            'source': 'akshare'
        }
    except Exception as e:
        print(f"从akshare获取实时行情失败: {e}")
        return {}


def get_company_info_from_akshare(code: str) -> dict:
    """从akshare获取公司信息"""
    if not AKSHARE_AVAILABLE:
        return {}
    
    try:
        code_num = code[-6:]
        df = ak.stock_individual_info_em(symbol=code_num)
        
        info = {}
        for _, row in df.iterrows():
            info[row['item']] = row['value']
        
        return {
            'name': info.get('股票简称', ''),
            'industry': info.get('行业', '未知'),
            'main_business': info.get('主营业务', '未知'),
            'listing_date': info.get('上市时间', ''),
            'total_shares': info.get('总股本', ''),
            'circulating_shares': info.get('流通股本', ''),
            'source': 'akshare'
        }
    except Exception as e:
        print(f"从akshare获取公司信息失败: {e}")
        return {}


def get_financial_data_from_akshare(code: str) -> list:
    """从akshare获取盈利预测"""
    if not AKSHARE_AVAILABLE:
        return []
    
    try:
        code_num = code[-6:]
        df = ak.stock_yjyg_em(indicator="预测指标")
        
        # 过滤出指定股票的数据
        df = df[df['股票代码'] == code_num]
        
        forecasts = []
        for _, row in df.iterrows():
            forecast = {
                'year': str(row.get('预测年度', '')),
                'eps': str(row.get('EPS', '')),
                'revenue': str(row.get('营业总收入', '')),
                'revenue_growth': str(row.get('营业总收入同比', '')),
                'net_profit': str(row.get('净利润', '')),
                'net_profit_growth': str(row.get('净利润同比增长', '')),
                'roe': str(row.get('ROE', '')),
            }
            forecasts.append(forecast)
        
        return forecasts
    except Exception as e:
        print(f"从akshare获取盈利预测失败: {e}")
        return []


def collect_stock_data(code: str, tdx_path: str = "D:/SoftwaresInstalled/dycy") -> dict:
    """
    采集股票的所有数据
    
    Args:
        code: 股票代码
        tdx_path: 通达信安装目录
        
    Returns:
        包含所有数据的字典
    """
    # 标准化代码
    code = code.strip().upper()
    if not code.startswith(('SH', 'SZ', 'BJ')):
        code_num = code.zfill(6)
        if code_num.startswith('6'):
            code = f"SH{code_num}"
        elif code_num.startswith(('0', '3')):
            code = f"SZ{code_num}"
        else:
            code = f"SH{code_num}"
    
    print(f"正在采集 {code} 的数据...")
    
    # 1. 获取本地日线数据
    local_daily = read_local_daily_data(tdx_path, code)
    historical = read_historical_data(tdx_path, code, 60)
    
    # 2. 从网络获取实时行情
    realtime = get_realtime_from_akshare(code)
    
    # 3. 获取公司信息
    company = get_company_info_from_akshare(code)
    
    # 4. 获取盈利预测
    forecasts = get_financial_data_from_akshare(code)
    
    # 合并数据
    result = {
        'code': code,
        'collect_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'local_daily': local_daily,
        'historical': historical,
        'realtime': realtime,
        'company': company,
        'forecasts': forecasts
    }
    
    return result


def generate_html_report(data: dict, output_file: str = "stock_report.html"):
    """
    生成HTML报告
    
    Args:
        data: 股票数据
        output_file: 输出文件路径
    """
    code = data['code']
    company = data.get('company', {})
    realtime = data.get('realtime', {})
    local_daily = data.get('local_daily', {})
    historical = data.get('historical', [])
    forecasts = data.get('forecasts', [])
    
    # 确定显示价格
    if realtime.get('price', 0) > 0:
        display_price = realtime['price']
        display_change_pct = realtime['change_pct']
        change_color = '#ff0000' if display_change_pct >= 0 else '#00aa00'
    elif local_daily.get('price', 0) > 0:
        display_price = local_daily['price']
        display_change_pct = 0
        change_color = '#888888'
    else:
        display_price = 0
        display_change_pct = 0
        change_color = '#888888'
    
    # 生成历史K线JSON数据
    kline_json = json.dumps(historical, ensure_ascii=False)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company.get('name', code)} ({code}) - 股票分析报告</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 24px;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        }}
        
        .stock-title {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .stock-code {{
            font-size: 18px;
            opacity: 0.9;
            margin-bottom: 20px;
        }}
        
        .price-section {{
            display: flex;
            align-items: baseline;
            gap: 30px;
            flex-wrap: wrap;
        }}
        
        .current-price {{
            font-size: 48px;
            font-weight: bold;
        }}
        
        .price-change {{
            font-size: 24px;
            color: {change_color};
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 24px;
        }}
        
        .card {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .card-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #667eea;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .card-title::before {{
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(180deg, #667eea, #764ba2);
            border-radius: 2px;
        }}
        
        .info-row {{
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        .info-row:last-child {{
            border-bottom: none;
        }}
        
        .info-label {{
            color: rgba(255, 255, 255, 0.7);
        }}
        
        .info-value {{
            font-weight: 500;
        }}
        
        .info-value.positive {{
            color: #ff6b6b;
        }}
        
        .info-value.negative {{
            color: #51cf66;
        }}
        
        .chart-container {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 16px;
            padding: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin-bottom: 24px;
        }}
        
        .chart {{
            width: 100%;
            height: 400px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }}
        
        th {{
            color: #667eea;
            font-weight: 600;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: rgba(255, 255, 255, 0.5);
            font-size: 14px;
        }}
        
        .data-source {{
            background: rgba(102, 126, 234, 0.2);
            border-radius: 8px;
            padding: 12px;
            margin-top: 20px;
            font-size: 14px;
        }}
        
        .highlight {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="stock-title">{company.get('name', '未知')}</div>
            <div class="stock-code">{code} | {company.get('industry', '未知行业')}</div>
            <div class="price-section">
                <div class="current-price">¥{display_price:.2f}</div>
                <div class="price-change">
                    {"▲" if display_change_pct >= 0 else "▼"} {abs(display_change_pct):.2f}%
                </div>
            </div>
        </div>
        
        <div class="info-grid">
            <div class="card">
                <div class="card-title">实时行情</div>
                <div class="info-row">
                    <span class="info-label">今开</span>
                    <span class="info-value">¥{realtime.get('open', local_daily.get('open', 0)):.2f}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">最高</span>
                    <span class="info-value positive">¥{realtime.get('high', local_daily.get('high', 0)):.2f}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">最低</span>
                    <span class="info-value negative">¥{realtime.get('low', local_daily.get('low', 0)):.2f}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">换手率</span>
                    <span class="info-value">{realtime.get('turnover', 0):.2f}%</span>
                </div>
                <div class="info-row">
                    <span class="info-label">成交量</span>
                    <span class="info-value">{(realtime.get('volume', 0) or local_daily.get('volume', 0)) / 10000:.2f}万手</span>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">市值指标</div>
                <div class="info-row">
                    <span class="info-label">总市值</span>
                    <span class="info-value">{realtime.get('market_cap', 0) / 1e8:.2f}亿</span>
                </div>
                <div class="info-row">
                    <span class="info-label">流通市值</span>
                    <span class="info-value">{realtime.get('circulating_market_cap', 0) / 1e8:.2f}亿</span>
                </div>
                <div class="info-row">
                    <span class="info-label">市盈率(动)</span>
                    <span class="info-value">{realtime.get('pe_ratio', 0):.2f}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">成交额</span>
                    <span class="info-value">¥{(realtime.get('amount', 0) or local_daily.get('amount', 0)) / 1e8:.2f}亿</span>
                </div>
            </div>
            
            <div class="card">
                <div class="card-title">公司概况</div>
                <div class="info-row">
                    <span class="info-label">所属行业</span>
                    <span class="info-value">{company.get('industry', '未知')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">上市时间</span>
                    <span class="info-value">{company.get('listing_date', '未知')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">总股本</span>
                    <span class="info-value">{company.get('total_shares', '未知')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">流通股本</span>
                    <span class="info-value">{company.get('circulating_shares', '未知')}</span>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-title">主营业务</div>
            <p style="line-height: 1.8; color: rgba(255,255,255,0.9);">
                {company.get('main_business', '暂无数据')}
            </p>
        </div>
        
        <div class="chart-container">
            <div class="card-title">近期K线走势 (近60个交易日)</div>
            <div id="kline-chart" class="chart"></div>
        </div>
        
        <div class="card">
            <div class="card-title">机构盈利预测</div>
            {"<table><thead><tr><th>预测年度</th><th>EPS</th><th>营业总收入</th><th>收入同比</th><th>净利润</th><th>净利同比</th><th>ROE</th></tr></thead><tbody>" if forecasts else "<p style='color: rgba(255,255,255,0.7);'>暂无盈利预测数据</p>"}
            {"".join([f"<tr><td>{f['year']}</td><td>{f['eps']}</td><td>{f['revenue']}</td><td>{f['revenue_growth']}</td><td>{f['net_profit']}</td><td>{f['net_profit_growth']}</td><td>{f['roe']}</td></tr>" for f in forecasts[:10]])}
            {"</tbody></table>" if forecasts else ""}
        </div>
        
        <div class="data-source">
            <strong>数据来源:</strong> 本地通达信 ({local_daily.get('source', 'N/A')}) | 
            akshare ({realtime.get('source', 'N/A')}) | 
            采集时间: {data['collect_time']}
        </div>
    </div>
    
    <script type="text/javascript">
        // 准备K线数据
        var klineData = {kline_json};
        
        // 分离日期、收盘价、成交量数据
        var dates = klineData.map(d => d.date);
        var prices = klineData.map(d => d.price);
        var volumes = klineData.map(d => d.volume);
        var changes = klineData.map(d => d.change_pct);
        
        // 计算MA
        function calcMA(data, period) {{
            var result = [];
            for (var i = 0; i < data.length; i++) {{
                if (i < period - 1) {{
                    result.push('-');
                }} else {{
                    var sum = 0;
                    for (var j = 0; j < period; j++) {{
                        sum += data[i - j];
                    }}
                    result.push((sum / period).toFixed(2));
                }}
            }}
            return result;
        }}
        
        var ma5 = calcMA(prices, 5);
        var ma10 = calcMA(prices, 10);
        var ma20 = calcMA(prices, 20);
        
        // 初始化图表
        var chart = echarts.init(document.getElementById('kline-chart'));
        
        var option = {{
            backgroundColor: 'transparent',
            tooltip: {{
                trigger: 'axis',
                axisPointer: {{ type: 'cross' }},
                formatter: function(params) {{
                    var i = params[0].dataIndex;
                    return `<strong>${{dates[i]}}</strong><br/>
                            收盘: ¥${{prices[i].toFixed(2)}}<br/>
                            开盘: ¥${{klineData[i].open.toFixed(2)}}<br/>
                            最高: ¥${{klineData[i].high.toFixed(2)}}<br/>
                            最低: ¥${{klineData[i].low.toFixed(2)}}<br/>
                            涨幅: <span style="color:${{changes[i] >= 0 ? '#ff6b6b' : '#51cf66'}}">${{changes[i].toFixed(2)}}%</span><br/>
                            MA5: ${{ma5[i]}}<br/>
                            MA10: ${{ma10[i]}}<br/>
                            MA20: ${{ma20[i]}}`;
                }}
            }},
            grid: [
                {{ left: '10%', right: '8%', top: '10%', height: '50%' }},
                {{ left: '10%', right: '8%', top: '68%', height: '20%' }}
            ],
            xAxis: [
                {{
                    type: 'category',
                    data: dates,
                    gridIndex: 0,
                    axisLine: {{ lineStyle: {{ color: '#667eea' }} }},
                    axisLabel: {{ color: 'rgba(255,255,255,0.7)' }},
                    splitLine: {{ show: false }}
                }},
                {{
                    type: 'category',
                    data: dates,
                    gridIndex: 1,
                    axisLine: {{ lineStyle: {{ color: '#667eea' }} }},
                    axisLabel: {{ color: 'rgba(255,255,255,0.7)' }},
                    splitLine: {{ show: false }}
                }}
            ],
            yAxis: [
                {{
                    scale: true,
                    gridIndex: 0,
                    axisLine: {{ lineStyle: {{ color: '#667eea' }} }},
                    axisLabel: {{ color: 'rgba(255,255,255,0.7)', formatter: '{{value}}' }},
                    splitLine: {{ color: 'rgba(255,255,255,0.1)' }}
                }},
                {{
                    scale: true,
                    gridIndex: 1,
                    axisLine: {{ lineStyle: {{ color: '#667eea' }} }},
                    axisLabel: {{ color: 'rgba(255,255,255,0.7)', formatter: function(v) {{return (v/10000).toFixed(0)+'万'}} }}
                }}
            ],
            series: [
                {{
                    name: 'K线',
                    type: 'candlestick',
                    data: klineData.map(d => [d.open, d.price, d.low, d.high]),
                    xAxisIndex: 0,
                    yAxisIndex: 0,
                    itemStyle: {{
                        color: '#ef5350',
                        color0: '#26a69a',
                        borderColor: '#ef5350',
                        borderColor0: '#26a69a'
                    }}
                }},
                {{
                    name: 'MA5',
                    type: 'line',
                    data: ma5,
                    xAxisIndex: 0,
                    yAxisIndex: 0,
                    smooth: true,
                    showSymbol: false,
                    lineStyle: {{ width: 1, color: '#ff6b6b' }}
                }},
                {{
                    name: 'MA10',
                    type: 'line',
                    data: ma10,
                    xAxisIndex: 0,
                    yAxisIndex: 0,
                    smooth: true,
                    showSymbol: false,
                    lineStyle: {{ width: 1, color: '#ffa726' }}
                }},
                {{
                    name: 'MA20',
                    type: 'line',
                    data: ma20,
                    xAxisIndex: 0,
                    yAxisIndex: 0,
                    smooth: true,
                    showSymbol: false,
                    lineStyle: {{ width: 1, color: '#42a5f5' }}
                }},
                {{
                    name: '成交量',
                    type: 'bar',
                    data: volumes,
                    xAxisIndex: 1,
                    yAxisIndex: 1,
                    itemStyle: {{
                        color: function(params) {{
                            var i = params.dataIndex;
                            return changes[i] >= 0 ? '#ef5350' : '#26a69a';
                        }}
                    }}
                }}
            ]
        }};
        
        chart.setOption(option);
        
        // 响应式
        window.addEventListener('resize', function() {{
            chart.resize();
        }});
    </script>
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"报告已生成: {output_file}")
    return output_file


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='股票数据采集与报告生成')
    parser.add_argument('code', nargs='?', default='688456', help='股票代码')
    parser.add_argument('--tdx-path', default='D:/SoftwaresInstalled/dycy', help='通达信安装目录')
    parser.add_argument('--output', '-o', default='stock_report.html', help='输出文件')
    
    args = parser.parse_args()
    
    # 采集数据
    data = collect_stock_data(args.code, args.tdx_path)
    
    # 生成报告
    output_file = generate_html_report(data, args.output)
    
    # 保存原始数据
    data_file = args.output.replace('.html', '_data.json')
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"原始数据已保存: {data_file}")
    
    return output_file


if __name__ == "__main__":
    main()
