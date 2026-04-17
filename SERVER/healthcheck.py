"""
健康检查端点 - 用于 CloudBase 负载均衡和监控
"""
from flask import Blueprint, jsonify
from datetime import datetime

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'activation-server'
    }), 200


@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """就绪检查接口 - 检查数据库连接"""
    try:
        from models import db
        # 执行简单查询测试数据库连接
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'ready',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'not ready',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503
