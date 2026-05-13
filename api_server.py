#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API Server - 股票财务数据API服务
包含增量更新接口
"""

import os
import sys
import json
import logging
import re
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MYSQL_CONFIG
from database import MySQLClient
from fetchers.f10_collector import F10Collector
from fetchers.luxf_fetch_ths_hudong import fetch_qa_data

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='web')
CORS(app)

# 全局更新状态
update_status = {
    'running': False,
    'progress': 0,
    'message': '',
    'current_task': '',
    'start_time': None
}

# ============================================================
# 增量行情信息更新接口
# ============================================================

@app.route('/api/update/market_snapshot', methods=['POST'])
def update_market_snapshot():
    if update_status['running']:
        return jsonify({
            'success': False,
            'message': '正在执行更新，请等待完成',
            'data': None
        }), 400
    
    try:
        from fetchers.incremental_updater import IncrementalUpdater
        
        update_status['running'] = True
        update_status['progress'] = 0
        update_status['message'] = '开始更新市场行情快照...'
        
        updater = IncrementalUpdater()
        try:
            def callback(progress, message):
                update_status['progress'] = progress
                update_status['message'] = message
            
            result = updater.update_market_snapshot(callback=callback)
            
            update_status['progress'] = 100
            update_status['message'] = result['message']
            update_status['running'] = False
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': result
            })
        finally:
            updater.close()
            update_status['running'] = False
            
    except Exception as e:
        logger.error(f"更新市场快照失败: {e}")
        update_status['running'] = False
        return jsonify({
            'success': False,
            'message': str(e),
            'data': None
        }), 500


@app.route('/api/update/profit_forecast', methods=['POST'])
def update_profit_forecast():
    if update_status['running']:
        return jsonify({
            'success': False,
            'message': '正在执行更新，请等待完成',
            'data': None
        }), 400
    
    try:
        from fetchers.incremental_updater import IncrementalUpdater
        
        force_update = request.args.get('force_update', False, type=bool)
        
        update_status['running'] = True
        update_status['progress'] = 0
        update_status['message'] = '开始更新盈利预测数据...'
        
        updater = IncrementalUpdater()
        try:
            def callback(progress, message):
                update_status['progress'] = progress
                update_status['message'] = message
            
            result = updater.update_profit_forecast(
                force_update=force_update,
                callback=callback
            )
            
            update_status['progress'] = 100
            update_status['message'] = result['message']
            update_status['running'] = False
            
            return jsonify({
                'success': True,
                'message': result['message'],
                'data': result
            })
        finally:
            updater.close()
            update_status['running'] = False
            
    except Exception as e:
        logger.error(f"更新盈利预测失败: {e}")
        update_status['running'] = False
        return jsonify({
            'success': False,
            'message': str(e),
            'data': None
        }), 500


@app.route('/api/update/all', methods=['POST'])
def update_all():
    if update_status['running']:
        return jsonify({
            'success': False,
            'message': '正在执行更新，请等待完成',
            'data': None
        }), 400
    
    try:
        from fetchers.incremental_updater import IncrementalUpdater
        
        update_status['running'] = True
        update_status['progress'] = 0
        update_status['message'] = '开始执行完整增量更新...'
        
        updater = IncrementalUpdater()
        result = {}
        
        try:
            def callback(progress, message):
                update_status['progress'] = progress
                update_status['message'] = message
            
            update_status['message'] = '正在更新市场行情快照...'
            snapshot_result = updater.update_market_snapshot(callback=callback)
            result['market_snapshot'] = snapshot_result
            
            update_status['message'] = '正在更新盈利预测数据...'
            forecast_result = updater.update_profit_forecast(callback=callback)
            result['profit_forecast'] = forecast_result
            
            result['summary'] = {
                'total_stocks': snapshot_result['total'],
                'snapshot_success': snapshot_result['success'],
                'forecast_success': forecast_result['success'],
                'message': f"增量更新完成！市场快照成功 {snapshot_result['success']} 条，盈利预测成功 {forecast_result['success']} 条"
            }
            
            update_status['progress'] = 100
            update_status['message'] = result['summary']['message']
            update_status['running'] = False
            
            return jsonify({
                'success': True,
                'message': result['summary']['message'],
                'data': result
            })
        finally:
            updater.close()
            update_status['running'] = False
            
    except Exception as e:
        logger.error(f"执行增量更新失败: {e}")
        update_status['running'] = False
        return jsonify({
            'success': False,
            'message': str(e),
            'data': None
        }), 500


@app.route('/api/update/status', methods=['GET'])
def get_update_status():
    return jsonify({
        'success': True,
        'data': {
            'running': update_status['running'],
            'progress': update_status['progress'],
            'message': update_status['message'],
            'current_task': update_status['current_task']
        }
    })

def generate_update_progress():
    """生成更新进度流（SSE）"""
    import time
    
    last_progress = -1
    last_message = ""
    
    # 持续监听，直到客户端断开连接
    while True:
        # 只在进度或消息变化时发送
        if update_status['progress'] != last_progress or update_status['message'] != last_message:
            last_progress = update_status['progress']
            last_message = update_status['message']
            
            progress_data = {
                'progress': update_status['progress'],
                'message': update_status['message'],
                'current_task': update_status['current_task'],
                'running': update_status['running']
            }
            yield f"data: {json.dumps(progress_data)}\n\n"
        
        # 如果更新已经完成，发送最终消息后退出
        if not update_status['running'] and update_status['progress'] == 100:
            break
        
        time.sleep(0.3)

@app.route('/api/update/progress', methods=['GET'])
def get_update_progress():
    """获取更新进度（SSE流）"""
    from flask import Response
    return Response(
        generate_update_progress(),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

# ============================================================
# 股票详情相关API接口
# ============================================================

@app.route('/api/stock/<code>/info', methods=['GET'])
def get_stock_info(code):
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        # 从stock_list获取基本信息
        sql = "SELECT name, industry, market_cap, current_price FROM stock_list WHERE code = %s"
        result = db_client.query_one(sql, (code,))
        
        if result:
            db_client.close()
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': {
                    'code': code,
                    'name': result['name'],
                    'industry': result.get('industry', ''),
                    'market_cap': result.get('market_cap'),
                    'current_price': result.get('current_price')
                }
            })
        else:
            db_client.close()
            return jsonify({
                'success': True,
                'message': '未找到股票信息',
                'data': {
                    'code': code,
                    'name': '股票' + code
                }
            })
    except Exception as e:
        logger.error(f"获取股票信息失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

@app.route('/api/stock/<code>/f10/market', methods=['GET'])
def get_f10_market(code):
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        # 从market_snapshot获取最新行情数据
        sql = """
            SELECT price, `change`, change_percent, market_cap, 
                   volume, amount, high, low, open, prev_close, snapshot_time
            FROM market_snapshot 
            WHERE code = %s 
            ORDER BY snapshot_time DESC 
            LIMIT 1
        """
        result = db_client.query_one(sql, (code,))
        
        if result:
            # 格式化时间
            snapshot_time = result['snapshot_time']
            if snapshot_time:
                snapshot_time = snapshot_time.strftime('%Y-%m-%d %H:%M:%S')
            
            db_client.close()
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': {
                    'code': code,
                    'price': float(result['price']) if result['price'] else None,
                    'change': float(result['change']) if result['change'] else None,
                    'change_percent': float(result['change_percent']) if result['change_percent'] else None,
                    'market_cap': float(result['market_cap']) if result['market_cap'] else None,
                    'volume': result['volume'],
                    'amount': float(result['amount']) if result['amount'] else None,
                    'high': float(result['high']) if result['high'] else None,
                    'low': float(result['low']) if result['low'] else None,
                    'open': float(result['open']) if result['open'] else None,
                    'prev_close': float(result['prev_close']) if result['prev_close'] else None,
                    'snapshot_time': snapshot_time
                }
            })
        else:
            # 如果没有快照数据，从stock_list获取基本信息
            sql = "SELECT name, market_cap, current_price FROM stock_list WHERE code = %s"
            result = db_client.query_one(sql, (code,))
            
            db_client.close()
            if result:
                return jsonify({
                    'success': True,
                    'message': '获取成功',
                    'data': {
                        'code': code,
                        'price': float(result['current_price']) if result['current_price'] else None,
                        'change': None,
                        'change_percent': None,
                        'market_cap': float(result['market_cap']) if result['market_cap'] else None,
                        'snapshot_time': None
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'message': '未找到行情数据',
                    'data': None
                })
    except Exception as e:
        logger.error(f"获取F10行情数据失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

@app.route('/api/stock/<code>/f10/profile', methods=['GET'])
def get_f10_profile(code):
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        # 从stock_list获取公司概况（只查询存在的字段）
        sql = """
            SELECT name, industry, market_cap, pe_ratio
            FROM stock_list 
            WHERE code = %s
        """
        result = db_client.query_one(sql, (code,))
        
        if result:
            db_client.close()
            return jsonify({
                'success': True,
                'message': '获取成功',
                'data': {
                    'code': code,
                    'name': result['name'],
                    'industry': result.get('industry', ''),
                    'market_cap': float(result['market_cap']) if result['market_cap'] else None,
                    'total_shares': None,  # 数据库中没有这个字段
                    'float_shares': None,  # 数据库中没有这个字段
                    'eps': None,  # 数据库中没有这个字段
                    'pe': float(result['pe_ratio']) if result['pe_ratio'] else None,
                    'pb': None,  # 数据库中没有这个字段
                    'business_scope': '',
                    'company_profile': ''
                }
            })
        else:
            db_client.close()
            return jsonify({'success': False, 'message': '未找到公司概况', 'data': None})
    except Exception as e:
        logger.error(f"获取F10公司概况失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

@app.route('/api/stock/<code>/f10/forecast', methods=['GET'])
def get_f10_forecast(code):
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        # 获取盈利预测数据（使用数据库中实际存在的字段）
        sql = """
            SELECT year, forecast_type, eps, revenue, net_profit, roe, book_value_ps, updated_at
            FROM profit_forecast 
            WHERE code = %s 
            ORDER BY year DESC
        """
        results = db_client.query_all(sql, (code,))
        
        data = []
        for row in results:
            update_time = row['updated_at']
            if update_time:
                update_time = update_time.strftime('%Y-%m-%d')
            
            data.append({
                'report_year': row['year'],
                'report_quarter': 4,  # 默认为年报
                'eps': float(row['eps']) if row['eps'] else None,
                # 数据库中单位是百万，转换为亿元
                'revenue': float(row['revenue']) / 100 if row['revenue'] else None,
                'net_profit': float(row['net_profit']) / 100 if row['net_profit'] else None,
                'pe': None,  # 数据库中没有这个字段
                'roe': float(row['roe']) if row['roe'] else None,
                'book_value_ps': float(row['book_value_ps']) if row['book_value_ps'] else None,
                'update_time': update_time
            })
        
        db_client.close()
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': {'data': data}
        })
    except Exception as e:
        logger.error(f"获取盈利预测失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

@app.route('/api/stock/<code>/metrics', methods=['GET'])
def get_stock_metrics(code):
    limit = request.args.get('limit', 16, type=int)
    
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        sql = """
            SELECT report_date, gross_margin, revenue_yoy, 
                   revenue_quarterly_w, kfe_np_yoy, kfe_np_ttm_w, 
                   kfe_np_quarterly_w, net_profit_attr_w,
                   eps_basic, roe_diluted
            FROM quarterly_finance 
            WHERE code = %s 
            ORDER BY report_date DESC 
            LIMIT %s
        """
        results = db_client.query_all(sql, (code, limit + 4))
        
        metrics = []
        for i, row in enumerate(results[:limit]):
            prev_row = results[i + 1] if i + 1 < len(results) else None
            last_year_row = results[i + 4] if i + 4 < len(results) else None
            
            revenue_qoq = None
            if prev_row and row['revenue_quarterly_w'] and prev_row['revenue_quarterly_w']:
                current_revenue = float(row['revenue_quarterly_w'])
                prev_revenue = float(prev_row['revenue_quarterly_w'])
                if prev_revenue != 0:
                    revenue_qoq = ((current_revenue - prev_revenue) / prev_revenue) * 100
            
            kfe_np_qoq = None
            if prev_row and row['kfe_np_quarterly_w'] and prev_row['kfe_np_quarterly_w']:
                current_kfe = float(row['kfe_np_quarterly_w'])
                prev_kfe = float(prev_row['kfe_np_quarterly_w'])
                if prev_kfe != 0:
                    kfe_np_qoq = ((current_kfe - prev_kfe) / prev_kfe) * 100
            
            np_yoy = None
            if last_year_row and row['net_profit_attr_w'] and last_year_row['net_profit_attr_w']:
                current_np = float(row['net_profit_attr_w'])
                last_year_np = float(last_year_row['net_profit_attr_w'])
                if last_year_np != 0:
                    np_yoy = ((current_np - last_year_np) / last_year_np) * 100
            
            metrics.append({
                'report_date': str(row['report_date']),
                'gross_margin': float(row['gross_margin']) if row['gross_margin'] else None,
                'revenue_yoy': float(row['revenue_yoy']) if row['revenue_yoy'] else None,
                'revenue_qoq': revenue_qoq,
                'np_yoy': np_yoy,
                'kfe_np_yoy': float(row['kfe_np_yoy']) if row['kfe_np_yoy'] else None,
                'kfe_np_qoq': kfe_np_qoq,
                'kfe_np_ttm_w': float(row['kfe_np_ttm_w']) if row['kfe_np_ttm_w'] else None,
                'revenue': float(row['revenue_quarterly_w']) if row['revenue_quarterly_w'] else None,
                'net_profit': float(row['net_profit_attr_w']) if row['net_profit_attr_w'] else None,
                'eps': float(row['eps_basic']) if row['eps_basic'] else None,
                'roe': float(row['roe_diluted']) if row['roe_diluted'] else None
            })
        
        db_client.close()
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': {'metrics': metrics}
        })
    except Exception as e:
        logger.error(f"获取股票指标失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

@app.route('/api/stocks/filter', methods=['GET'])
def filter_stocks():
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        offset = (page - 1) * limit
        
        # 获取筛选类型
        quarter_type = request.args.get('quarter_type', 'single')
        
        # 获取报告期
        report_date = request.args.get('report_date', '')
        report_date2 = request.args.get('report_date2', '')
        
        # 获取第一季度数值筛选条件（只使用数据库中存在的字段）
        filters_q1 = {}
        filters_q2 = {}
        numeric_fields = ['gross_margin', 'revenue_yoy', 'revenue_qoq',
                         'net_profit_yoy', 'net_profit_qoq', 'net_profit_ttm']
        
        for field in numeric_fields:
            min_val = request.args.get(f'{field}_min')
            max_val = request.args.get(f'{field}_max')
            if min_val or max_val:
                filters_q1[field] = {'min': float(min_val) if min_val else None, 'max': float(max_val) if max_val else None}
            
            # 第二季度筛选条件
            min_val2 = request.args.get(f'{field}_min2')
            max_val2 = request.args.get(f'{field}_max2')
            if min_val2 or max_val2:
                filters_q2[field] = {'min': float(min_val2) if min_val2 else None, 'max': float(max_val2) if max_val2 else None}
        
        # 获取排序参数
        sort_field = request.args.get('sort_field', 'code')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 优化：双季度筛选采用分步查询
        if quarter_type == 'two' and report_date and report_date2:
            # 直接使用简单的JOIN，不在子查询中使用LAG函数
            sql = """
                SELECT q1.code, sl.name, 
                       q1.gross_margin, q1.revenue_yoy, q1.kfe_np_yoy,
                       q1.kfe_np_ttm_w, q1.revenue_quarterly_w, q1.net_profit_attr_w, q1.eps_basic, q1.roe_diluted,
                       %s as report_date,
                       -- 计算营收环比
                       CASE WHEN prev.revenue_quarterly_w IS NULL OR prev.revenue_quarterly_w = 0 THEN NULL 
                            ELSE (q1.revenue_quarterly_w - prev.revenue_quarterly_w) / prev.revenue_quarterly_w * 100 END AS revenue_qoq,
                       -- 计算扣非环比
                       CASE WHEN prev.kfe_np_quarterly_w IS NULL OR prev.kfe_np_quarterly_w = 0 THEN NULL 
                            ELSE (q1.kfe_np_quarterly_w - prev.kfe_np_quarterly_w) / prev.kfe_np_quarterly_w * 100 END AS net_profit_qoq
                FROM quarterly_finance q1
                JOIN quarterly_finance q2 ON q1.code = q2.code
                LEFT JOIN quarterly_finance prev ON q1.code = prev.code AND prev.report_date = (
                    SELECT MAX(report_date) FROM quarterly_finance WHERE code = q1.code AND report_date < q1.report_date
                )
                JOIN stock_list sl ON q1.code = sl.code
                WHERE sl.status = 'active'
                  AND q1.report_date = %s
                  AND q2.report_date = %s
            """
            params = [report_date, report_date, report_date2]
            
            # 添加第一季度筛选条件（只筛选数据库中存在的字段，避免计算字段）
            for field, range_vals in filters_q1.items():
                db_field = {
                    'gross_margin': 'q1.gross_margin',
                    'revenue_yoy': 'q1.revenue_yoy',
                    'net_profit_yoy': 'q1.kfe_np_yoy',
                    'net_profit_ttm': 'q1.kfe_np_ttm_w'
                }.get(field)
                
                if db_field:
                    if range_vals['min'] is not None:
                        sql += f" AND {db_field} >= %s"
                        params.append(range_vals['min'])
                    if range_vals['max'] is not None:
                        sql += f" AND {db_field} <= %s"
                        params.append(range_vals['max'])
            
            # 添加第二季度筛选条件
            for field, range_vals in filters_q2.items():
                db_field = {
                    'gross_margin': 'q2.gross_margin',
                    'revenue_yoy': 'q2.revenue_yoy',
                    'net_profit_yoy': 'q2.kfe_np_yoy',
                    'net_profit_ttm': 'q2.kfe_np_ttm_w'
                }.get(field)
                
                if db_field:
                    if range_vals['min'] is not None:
                        sql += f" AND {db_field} >= %s"
                        params.append(range_vals['min'])
                    if range_vals['max'] is not None:
                        sql += f" AND {db_field} <= %s"
                        params.append(range_vals['max'])
        else:
            # 单季度筛选：直接使用索引查询，不使用窗口函数
            sql = """
                SELECT qf.code, sl.name, 
                       qf.gross_margin, qf.revenue_yoy, qf.kfe_np_yoy,
                       qf.kfe_np_ttm_w, qf.revenue_quarterly_w, qf.net_profit_attr_w, qf.eps_basic, qf.roe_diluted,
                       qf.report_date,
                       -- 计算营收环比
                       CASE WHEN prev.revenue_quarterly_w IS NULL OR prev.revenue_quarterly_w = 0 THEN NULL 
                            ELSE (qf.revenue_quarterly_w - prev.revenue_quarterly_w) / prev.revenue_quarterly_w * 100 END AS revenue_qoq,
                       -- 计算扣非环比
                       CASE WHEN prev.kfe_np_quarterly_w IS NULL OR prev.kfe_np_quarterly_w = 0 THEN NULL 
                            ELSE (qf.kfe_np_quarterly_w - prev.kfe_np_quarterly_w) / prev.kfe_np_quarterly_w * 100 END AS net_profit_qoq
                FROM quarterly_finance qf
                LEFT JOIN quarterly_finance prev 
                    ON qf.code = prev.code AND prev.report_date = (
                        SELECT MAX(report_date) FROM quarterly_finance 
                        WHERE code = qf.code AND report_date < qf.report_date
                    )
                JOIN stock_list sl ON qf.code = sl.code
                WHERE sl.status = 'active'
            """
            params = []
            
            # 添加报告期筛选（这是最关键的筛选条件，放在最前面）
            if report_date:
                sql += " AND qf.report_date = %s"
                params.append(report_date)
            
            # 添加数值筛选条件（只筛选数据库中存在的字段）
            for field, range_vals in filters_q1.items():
                db_field = {
                    'gross_margin': 'qf.gross_margin',
                    'revenue_yoy': 'qf.revenue_yoy',
                    'net_profit_yoy': 'qf.kfe_np_yoy',
                    'net_profit_ttm': 'qf.kfe_np_ttm_w'
                }.get(field)
                
                if db_field:
                    if range_vals['min'] is not None:
                        sql += f" AND {db_field} >= %s"
                        params.append(range_vals['min'])
                    if range_vals['max'] is not None:
                        sql += f" AND {db_field} <= %s"
                        params.append(range_vals['max'])
        
        # 保存不带排序的SQL用于COUNT查询
        sql_without_order = sql
        
        # 添加排序（尽量使用数据库字段排序）
        valid_sort_fields = ['code', 'gross_margin', 'revenue_yoy', 'revenue_qoq',
                           'net_profit_yoy', 'net_profit_qoq', 'net_profit_ttm']
        if sort_field in valid_sort_fields:
            # 根据查询类型使用正确的表别名
            if quarter_type == 'two' and report_date and report_date2:
                db_sort_field = {
                    'net_profit_yoy': 'q1.kfe_np_yoy',
                    'net_profit_ttm': 'q1.kfe_np_ttm_w'
                }.get(sort_field, sort_field)
            else:
                db_sort_field = {
                    'net_profit_yoy': 'qf.kfe_np_yoy',
                    'net_profit_ttm': 'qf.kfe_np_ttm_w'
                }.get(sort_field, sort_field)
            sql += f" ORDER BY {db_sort_field} {'ASC' if sort_order == 'asc' else 'DESC'}"
        else:
            sql += " ORDER BY qf.report_date DESC, qf.code ASC"
        
        # 优化：先获取数据再计算总数（对于分页查询，先查数据更高效）
        sql_with_limit = sql + " LIMIT %s OFFSET %s"
        results = db_client.query_all(sql_with_limit, params + [limit, offset])
        
        # 转换数据
        items = []
        for row in results:
            items.append({
                'code': row['code'],
                'name': row['name'],
                'gross_margin': round(row['gross_margin'], 2) if row['gross_margin'] else None,
                'revenue_yoy': round(row['revenue_yoy'], 2) if row['revenue_yoy'] else None,
                'revenue_qoq': round(row['revenue_qoq'], 2) if row['revenue_qoq'] else None,
                'net_profit_yoy': round(row['kfe_np_yoy'], 2) if row['kfe_np_yoy'] else None,
                'net_profit_qoq': round(row['net_profit_qoq'], 2) if row['net_profit_qoq'] else None,
                'net_profit_ttm': round(row['kfe_np_ttm_w'] / 10000, 4) if row['kfe_np_ttm_w'] else None,
                'revenue': round(row['revenue_quarterly_w'] / 10000, 4) if row['revenue_quarterly_w'] else None,
                'net_profit': round(row['net_profit_attr_w'] / 10000, 4) if row['net_profit_attr_w'] else None,
                'eps': round(row['eps_basic'], 4) if row['eps_basic'] else None,
                'roe': round(row['roe_diluted'], 4) if row['roe_diluted'] else None,
                'report_date': row['report_date']
            })
        
        # 优化：只在第一页时计算总数，避免每次都执行COUNT查询
        total = 0
        if page == 1:
            # 使用不带ORDER BY的SQL进行COUNT查询
            count_sql = "SELECT COUNT(*) as total FROM (" + sql_without_order + ") as sub"
            total = db_client.query_one(count_sql, params)['total']
        else:
            # 如果不是第一页，假设总数足够大
            total = (page * limit) + 1
        
        db_client.close()
        
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': {
                'items': items,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_items': total,
                    'limit': limit
                }
            }
        })
    except Exception as e:
        logger.error(f"筛选股票失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

@app.route('/api/stocks', methods=['GET'])
def search_stocks():
    q = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        if q:
            sql = """
                SELECT code, name FROM stock_list 
                WHERE (code LIKE %s OR name LIKE %s) AND status = 'active'
                ORDER BY code 
                LIMIT %s
            """
            results = db_client.query_all(sql, (f'%{q}%', f'%{q}%', limit))
        else:
            sql = "SELECT code, name FROM stock_list WHERE status = 'active' ORDER BY code LIMIT %s"
            results = db_client.query_all(sql, (limit,))
        
        stocks = []
        for row in results:
            stocks.append({
                'code': row['code'],
                'name': row['name']
            })
        
        db_client.close()
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': {'stocks': stocks}
        })
    except Exception as e:
        logger.error(f"搜索股票失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

# ============================================================
# 自选股相关API接口
# ============================================================

@app.route('/api/my_stocks', methods=['GET'])
def get_my_stocks():
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        # 获取股票列表
        sql = """
            SELECT code, name, pool_type, notes, added_at 
            FROM my_stock 
            ORDER BY pool_type, added_at DESC
        """
        results = db_client.query_all(sql)
        
        stocks = []
        core_count = 0
        watch_count = 0
        
        for row in results:
            added_at = row['added_at']
            if added_at:
                added_at = added_at.strftime('%Y-%m-%d %H:%M')
            
            stocks.append({
                'code': row['code'],
                'name': row['name'],
                'pool_type': row['pool_type'],
                'notes': row.get('notes', ''),
                'created_at': added_at
            })
            
            # 统计数量
            if row['pool_type'] == 'core':
                core_count += 1
            else:
                watch_count += 1
        
        db_client.close()
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': {
                'stocks': stocks,
                'counts': {
                    'core': core_count,
                    'watch': watch_count
                }
            }
        })
    except Exception as e:
        logger.error(f"获取自选股失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

@app.route('/api/my_stock/<code>', methods=['POST'])
def add_my_stock(code):
    try:
        data = request.get_json()
        
        db_client = MySQLClient(MYSQL_CONFIG)
        
        sql = """
            INSERT INTO my_stock (code, name, pool_type, notes, added_at)
            VALUES (%s, %s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
            name = VALUES(name), pool_type = VALUES(pool_type), 
            notes = VALUES(notes), updated_at = NOW()
        """
        db_client.execute(sql, (code, data.get('name', ''), data.get('pool_type', 'watch'), data.get('notes', '')))
        db_client.commit()
        
        db_client.close()
        return jsonify({'success': True, 'message': '添加成功', 'data': None})
    except Exception as e:
        logger.error(f"添加自选股失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

@app.route('/api/my_stock/<code>', methods=['DELETE'])
def delete_my_stock(code):
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        pool_type = request.args.get('pool_type', None)
        
        if pool_type:
            sql = "DELETE FROM my_stock WHERE code = %s AND pool_type = %s"
            db_client.execute(sql, (code, pool_type))
        else:
            sql = "DELETE FROM my_stock WHERE code = %s"
            db_client.execute(sql, (code,))
        
        db_client.commit()
        db_client.close()
        return jsonify({'success': True, 'message': '删除成功', 'data': None})
    except Exception as e:
        logger.error(f"删除自选股失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

@app.route('/api/my_stock/batch', methods=['POST'])
def batch_add_my_stock():
    try:
        data = request.get_json()
        input_text = data.get('input', '').strip()
        pool_type = data.get('pool_type', 'watch')
        
        if not input_text:
            return jsonify({'success': False, 'message': '输入不能为空', 'data': None})
        
        db_client = MySQLClient(MYSQL_CONFIG)
        
        # 尝试先按代码查找，如果找不到再按名称查找
        code = None
        name = None
        
        # 尝试从输入中提取股票代码
        # 支持格式：纯代码(688456)、代码+名称(688456 有研粉材)、纯名称(有研粉材)
        code_match = re.match(r'^(\d{6})', input_text)
        if code_match:
            # 提取前6位数字作为代码
            code = code_match.group(1)
            # 按代码查询名称
            sql = "SELECT name FROM stock_list WHERE code = %s"
            result = db_client.query_one(sql, (code,))
            if result:
                name = result['name']
        else:
            # 按名称查询代码
            sql = "SELECT code, name FROM stock_list WHERE name LIKE %s"
            result = db_client.query_one(sql, (f"%{input_text}%",))
            if result:
                code = result['code']
                name = result['name']
        
        if not code:
            db_client.close()
            return jsonify({'success': False, 'message': f'未找到股票: {input_text}', 'data': None})
        
        # 检查是否已存在
        sql = "SELECT * FROM my_stock WHERE code = %s"
        exists = db_client.query_one(sql, (code,))
        
        # 插入或更新
        sql = """
            INSERT INTO my_stock (code, name, pool_type, added_at)
            VALUES (%s, %s, %s, NOW())
            ON DUPLICATE KEY UPDATE
            name = VALUES(name), pool_type = VALUES(pool_type), updated_at = NOW()
        """
        db_client.execute(sql, (code, name, pool_type))
        db_client.commit()
        
        db_client.close()
        
        return jsonify({
            'success': True, 
            'message': '添加成功', 
            'data': {'code': code, 'name': name},
            'exists': exists is not None
        })
    except Exception as e:
        logger.error(f"批量添加自选股失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

@app.route('/api/my_stock/<code>/move', methods=['PUT'])
def move_my_stock(code):
    try:
        data = request.get_json()
        to_pool = data.get('to_pool', 'watch')
        
        db_client = MySQLClient(MYSQL_CONFIG)
        
        sql = "UPDATE my_stock SET pool_type = %s WHERE code = %s"
        db_client.execute(sql, (to_pool, code))
        db_client.commit()
        
        db_client.close()
        return jsonify({'success': True, 'message': '移动成功', 'data': None})
    except Exception as e:
        logger.error(f"移动自选股失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

# ============================================================
# 互动问答API接口
# ============================================================

@app.route('/api/stock/<code>/qa', methods=['GET'])
def get_stock_qa(code):
    """获取股票互动问答数据（支持分页）"""
    limit = request.args.get('limit', 20, type=int)
    page = request.args.get('page', 1, type=int)
    keyword = request.args.get('keyword', '').strip()
    
    offset = (page - 1) * limit
    
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        if keyword:
            # 搜索模式
            qa_data = db_client.search_stock_qa(code, keyword, limit, offset)
            total = db_client.get_qa_search_count(code, keyword)
        else:
            # 普通分页模式
            qa_data = db_client.get_stock_qa(code, limit, offset)
            total = db_client.get_qa_count(code)
        
        db_client.close()
        
        total_pages = (total + limit - 1) // limit
        
        return jsonify({
            'success': True,
            'message': '获取成功',
            'data': {
                'qa_list': qa_data,
                'total': total,
                'total_pages': total_pages,
                'current_page': page,
                'limit': limit,
                'keyword': keyword
            }
        })
    except Exception as e:
        logger.error(f"获取互动问答数据失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500


@app.route('/api/stock/<code>/qa/fetch', methods=['POST'])
def fetch_stock_qa(code):
    """采集股票互动问答数据并保存到数据库（支持增量更新）"""
    full_sync = request.args.get('full_sync', 'false').lower() == 'true'
    
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        
        # 获取最新回答时间（用于增量更新）
        latest_time = None
        if not full_sync:
            latest_time = db_client.get_latest_answer_time(code)
            logger.info(f"股票 {code} 最新回答时间: {latest_time}")
        
        db_client.close()
        
        # 调用采集脚本获取数据（获取所有3年内已回复的数据）
        qa_data = fetch_qa_data(code, fetch_all=True, max_years=3)
        
        if not qa_data:
            return jsonify({
                'success': True,
                'message': '未采集到新数据',
                'data': {'count': 0}
            })
        
        # 增量更新：只保留比最新时间新的数据
        new_data = []
        if latest_time and not full_sync:
            # 将latest_time转换为datetime对象进行比较
            from datetime import datetime
            latest_dt = datetime.strptime(str(latest_time), '%Y-%m-%d %H:%M:%S')
            
            for item in qa_data:
                answer_time = item.get('answer_time', '')
                if answer_time:
                    try:
                        answer_dt = datetime.strptime(answer_time, '%Y-%m-%d %H:%M:%S')
                        if answer_dt > latest_dt:
                            new_data.append(item)
                    except:
                        # 时间格式不正确，跳过
                        continue
        else:
            new_data = qa_data
        
        logger.info(f"股票 {code} 新增数据: {len(new_data)} 条")
        
        if not new_data:
            return jsonify({
                'success': True,
                'message': '数据库已是最新，无需更新',
                'data': {'count': 0}
            })
        
        # 转换数据格式
        data_list = []
        for item in new_data:
            data = {
                'code': code,
                'ask_user': item.get('ask_user', '') or '',
                'ask_time': item.get('ask_time'),
                'answer_time': item.get('answer_time'),
                'question': item.get('content', '') or item.get('question', '') or '',
                'answer': item.get('answer', '') or '',
                'status': 1 if (item.get('status') == '1' or (item.get('answer') and item.get('answer').strip())) else 0,
                'source_id': str(item.get('id', '')) or ''
            }
            data_list.append(data)
        
        # 保存到数据库
        db_client = MySQLClient(MYSQL_CONFIG)
        count = db_client.batch_insert_stock_qa(data_list)
        db_client.close()
        
        return jsonify({
            'success': True,
            'message': f'成功增量更新 {count} 条问答数据',
            'data': {'count': count}
        })
    except Exception as e:
        logger.error(f"采集互动问答数据失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500


# ============================================================
# 其他API接口
# ============================================================

@app.route('/api/report_dates', methods=['GET'])
def get_report_dates():
    try:
        db_client = MySQLClient(MYSQL_CONFIG)
        sql = """
            SELECT DISTINCT report_date 
            FROM quarterly_finance 
            ORDER BY report_date DESC 
            LIMIT 4
        """
        results = db_client.query_all(sql)
        
        report_dates = []
        for row in results:
            report_date = str(row['report_date'])
            year = report_date[:4]
            month = int(report_date[4:6])
            
            if month == 3:
                label = f"{year}年一季度 ({report_date})"
            elif month == 6:
                label = f"{year}年二季度 ({report_date})"
            elif month == 9:
                label = f"{year}年三季度 ({report_date})"
            elif month == 12:
                label = f"{year}年年报 ({report_date})"
            else:
                label = f"{year}-{month:02d} ({report_date})"
            
            report_dates.append({
                'report_date': report_date,
                'label': label
            })
        
        db_client.close()
        return jsonify({'success': True, 'message': '获取成功', 'data': report_dates})
    except Exception as e:
        logger.error(f"获取报告期失败: {e}")
        return jsonify({'success': False, 'message': str(e), 'data': None}), 500

# ============================================================
# 前端页面服务
# ============================================================

@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('web', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9528, debug=True)
