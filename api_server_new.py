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
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MYSQL_CONFIG
from database import MySQLClient
from fetchers.f10_collector import F10Collector

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

# ============================================================
# 保留原有API接口（简化版本）
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
    return send_from_directory('web', 'stock_filter.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('web', path)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9528, debug=True)
