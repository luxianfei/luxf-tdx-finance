#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增量行情信息更新API服务
提供市场快照和盈利预测的增量更新接口，支持进度反馈
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MYSQL_CONFIG
from database.mysql_client import MySQLClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 全局更新状态
update_status = {
    'running': False,
    'progress': 0,
    'message': '',
    'current_task': '',
    'start_time': None
}


def generate_update_progress():
    """生成更新进度流"""
    import time
    
    while update_status['running']:
        progress_data = {
            'progress': update_status['progress'],
            'message': update_status['message'],
            'current_task': update_status['current_task'],
            'running': update_status['running']
        }
        yield f"data: {json.dumps(progress_data)}\n\n"
        time.sleep(0.5)
    
    # 发送最终结果
    progress_data = {
        'progress': update_status['progress'],
        'message': update_status['message'],
        'current_task': update_status['current_task'],
        'running': False
    }
    yield f"data: {json.dumps(progress_data)}\n\n"


@app.route('/api/update/progress', methods=['GET'])
def get_update_progress():
    """获取更新进度（SSE流）"""
    return Response(
        generate_update_progress(),
        content_type='text/event-stream'
    )


@app.route('/api/update/status', methods=['GET'])
def get_update_status():
    """获取当前更新状态"""
    return jsonify({
        'success': True,
        'data': {
            'running': update_status['running'],
            'progress': update_status['progress'],
            'message': update_status['message'],
            'current_task': update_status['current_task']
        }
    })


@app.route('/api/update/market_snapshot', methods=['POST'])
def update_market_snapshot():
    """
    更新市场快照数据
    从通达信本地目录采集最新行情信息到market_snapshot表
    """
    if update_status['running']:
        return jsonify({
            'success': False,
            'message': '正在执行更新，请等待完成',
            'data': None
        }), 400
    
    try:
        from fetchers.incremental_updater import IncrementalUpdater
        
        # 设置更新状态
        update_status['running'] = True
        update_status['progress'] = 0
        update_status['message'] = '开始更新市场行情快照...'
        update_status['current_task'] = 'market_snapshot'
        
        updater = IncrementalUpdater()
        try:
            # 执行更新（带进度回调）
            result = updater.update_market_snapshot(callback=update_progress_callback)
            
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
        update_status['message'] = f"更新失败: {str(e)}"
        
        return jsonify({
            'success': False,
            'message': str(e),
            'data': None
        }), 500


@app.route('/api/update/profit_forecast', methods=['POST'])
def update_profit_forecast():
    """
    更新盈利预测数据
    检查是否有新的机构盈利预测数据
    """
    if update_status['running']:
        return jsonify({
            'success': False,
            'message': '正在执行更新，请等待完成',
            'data': None
        }), 400
    
    try:
        from fetchers.incremental_updater import IncrementalUpdater
        
        force_update = request.args.get('force_update', False, type=bool)
        
        # 设置更新状态
        update_status['running'] = True
        update_status['progress'] = 0
        update_status['message'] = '开始更新盈利预测数据...'
        update_status['current_task'] = 'profit_forecast'
        
        updater = IncrementalUpdater()
        try:
            # 执行更新（带进度回调）
            result = updater.update_profit_forecast(
                force_update=force_update,
                callback=update_progress_callback
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
        update_status['message'] = f"更新失败: {str(e)}"
        
        return jsonify({
            'success': False,
            'message': str(e),
            'data': None
        }), 500


@app.route('/api/update/all', methods=['POST'])
def update_all():
    """
    执行完整的增量更新
    包括：市场快照 + 盈利预测
    """
    if update_status['running']:
        return jsonify({
            'success': False,
            'message': '正在执行更新，请等待完成',
            'data': None
        }), 400
    
    try:
        from fetchers.incremental_updater import IncrementalUpdater
        
        # 设置更新状态
        update_status['running'] = True
        update_status['progress'] = 0
        update_status['message'] = '开始执行完整增量更新...'
        update_status['current_task'] = 'full_update'
        
        updater = IncrementalUpdater()
        result = {}
        
        try:
            # 更新市场快照 (占50%)
            update_status['message'] = '正在更新市场行情快照...'
            snapshot_result = updater.update_market_snapshot(
                callback=lambda p, m: update_progress_callback(p * 0.5, m)
            )
            result['market_snapshot'] = snapshot_result
            
            # 更新盈利预测 (占50%)
            update_status['message'] = '正在更新盈利预测数据...'
            forecast_result = updater.update_profit_forecast(
                callback=lambda p, m: update_progress_callback(50 + p * 0.5, m)
            )
            result['profit_forecast'] = forecast_result
            
            # 汇总结果
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
        update_status['message'] = f"更新失败: {str(e)}"
        
        return jsonify({
            'success': False,
            'message': str(e),
            'data': None
        }), 500


def update_progress_callback(progress, message):
    """更新进度回调函数"""
    update_status['progress'] = progress
    update_status['message'] = message
    logger.info(f"更新进度: {progress:.1f}% - {message}")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9529, threaded=True)
