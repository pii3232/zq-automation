from flask import Flask, render_template_string
from flask_cors import CORS
from models import db, User
from routes import api_bp
from reports import reports_bp
from healthcheck import health_bp
from config import Config
from audit_logger import audit_logger
from crypto_utils import AuthHelper
import logging
import os
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_server_url():
    """获取服务端地址"""
    return 'https://9793tg1lo456.vicp.fun'


def init_admin_user():
    """初始化admin用户"""
    try:
        # 检查admin用户是否存在
        admin = User.query.filter_by(username='admin').first()
        if admin:
            logger.info("Admin用户已存在")
            return
        
        # 创建admin用户
        admin = User(
            username='admin',
            email='admin@system.local',
            is_active=True
        )
        # 使用加密后的密码
        admin.set_password(AuthHelper.get_admin_password())
        
        db.session.add(admin)
        db.session.commit()
        
        # 记录审计日志
        audit_logger.log_admin_action('USER_CREATED', 'admin', {'email': 'admin@system.local'})
        logger.info("Admin用户创建成功")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建admin用户失败: {str(e)}")


def create_app():
    """创建Flask应用"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 启用CORS
    CORS(app)

    # 初始化数据库
    db.init_app(app)

    # 注册蓝图
    app.register_blueprint(health_bp)  # 健康检查（无前缀）
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/reports')

    # 创建数据库表
    with app.app_context():
        db.create_all()
        logger.info("数据库表已创建")
        
        # 初始化admin用户
        init_admin_user()
    
    # 记录系统启动
    audit_logger.log_system_event('START', {'host': Config.SERVER_HOST, 'port': Config.SERVER_PORT})

    # 首页路由 - 显示API文档
    @app.route('/')
    def index():
        doc_template = """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>激活系统API文档</title>
            <style>
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                body {
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    padding: 20px;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                }
                h1 {
                    color: #667eea;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 10px;
                    margin-bottom: 30px;
                }
                h2 {
                    color: #764ba2;
                    margin-top: 30px;
                    margin-bottom: 15px;
                }
                .endpoint {
                    background: #f8f9fa;
                    border-left: 4px solid #667eea;
                    padding: 15px;
                    margin: 15px 0;
                    border-radius: 4px;
                }
                .method {
                    display: inline-block;
                    padding: 3px 10px;
                    border-radius: 3px;
                    color: white;
                    font-weight: bold;
                    margin-right: 10px;
                }
                .get { background: #28a745; }
                .post { background: #007bff; }
                .put { background: #ffc107; color: black; }
                .delete { background: #dc3545; }
                .url {
                    font-family: 'Courier New', monospace;
                    color: #333;
                }
                .description {
                    margin-top: 10px;
                    color: #666;
                }
                code {
                    background: #e9ecef;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }
                .section {
                    margin-top: 40px;
                }
                .info-box {
                    background: #e7f3ff;
                    border-left: 4px solid #007bff;
                    padding: 15px;
                    margin: 20px 0;
                }
                .warning-box {
                    background: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 激活系统API文档</h1>

                <div class="info-box">
                    <strong>服务器地址：</strong> <code>SERVER_URL</code><br>
                    <strong>所有API前缀：</strong> <code>/api</code><br>
                    <strong>报表API前缀：</strong> <code>/reports</code>
                </div>

                <div class="section">
                    <h2>📋 系统管理</h2>
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="url">/api/health</span>
                        <div class="description">健康检查 - 测试服务器是否正常运行</div>
                    </div>
                </div>

                <div class="section">
                    <h2>👤 用户注册和登录</h2>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="url">/api/register/check</span>
                        <div class="description">检查用户名是否可用</div>
                        <div class="description"><strong>参数：</strong> <code>{"username": "用户名"}</code></div>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="url">/api/register/send-code</span>
                        <div class="description">发送验证码到邮箱</div>
                        <div class="description"><strong>参数：</strong> <code>{"email": "邮箱地址"}</code></div>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="url">/api/register</span>
                        <div class="description">用户注册</div>
                        <div class="description"><strong>参数：</strong> <code>{"username": "用户名", "password": "密码", "repeat_password": "重复密码", "email": "邮箱", "code": "验证码"}</code></div>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="url">/api/login</span>
                        <div class="description">用户登录</div>
                        <div class="description"><strong>参数：</strong> <code>{"username": "用户名", "password": "密码"}</code></div>
                    </div>
                </div>

                <div class="section">
                    <h2>🔑 激活码管理</h2>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="url">/api/activation/sync</span>
                        <div class="description">同步激活状态（每天检查一次）</div>
                        <div class="description"><strong>参数：</strong> <code>{"username": "用户名"}</code></div>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="url">/api/activation/activate</span>
                        <div class="description">使用激活码激活</div>
                        <div class="description"><strong>参数：</strong> <code>{"username": "用户名", "code": "激活码"}</code></div>
                    </div>
                </div>

                <div class="section">
                    <h2>💳 订单和支付</h2>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="url">/api/order/create</span>
                        <div class="description">创建订单</div>
                        <div class="description"><strong>参数：</strong> <code>{"username": "用户名", "quantity": 数量}</code></div>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="url">/api/order/check</span>
                        <div class="description">检查订单支付状态</div>
                        <div class="description"><strong>参数：</strong> <code>{"order_no": "订单号"}</code></div>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="url">/api/payment/notify</span>
                        <div class="description">支付通知（微信支付回调）</div>
                    </div>
                </div>

                <div class="section">
                    <h2>🎫 报障系统</h2>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="url">/api/ticket/create</span>
                        <div class="description">创建报障工单</div>
                        <div class="description"><strong>参数：</strong> <code>{"username": "用户名", "title": "标题", "content": "内容", "contact_person": "联系人", "contact_phone": "电话"}</code></div>
                    </div>
                    <div class="endpoint">
                        <span class="method post">POST</span>
                        <span class="url">/api/ticket/list</span>
                        <div class="description">获取用户的报障工单列表</div>
                        <div class="description"><strong>参数：</strong> <code>{"username": "用户名"}</code></div>
                    </div>
                </div>

                <div class="section">
                    <h2>📊 报表系统</h2>
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="url">/reports/report/users</span>
                        <div class="description">生成用户注册报告（PDF）</div>
                    </div>
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="url">/reports/report/orders</span>
                        <div class="description">生成支付报告（PDF）</div>
                    </div>
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="url">/reports/report/codes</span>
                        <div class="description">生成激活码统计报告（PDF）</div>
                    </div>
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="url">/reports/report/tickets</span>
                        <div class="description">生成报障表报告（PDF）</div>
                    </div>
                    <div class="endpoint">
                        <span class="method get">GET</span>
                        <span class="url">/reports/report/all</span>
                        <div class="description">一键生成所有报告（ZIP压缩包）</div>
                    </div>
                </div>

                <div class="warning-box">
                    <strong>⚠️ 注意事项：</strong>
                    <ul>
                        <li>所有API返回JSON格式数据</li>
                        <li>成功响应：<code>{"success": true, "message": "...", "data": {...}}</code></li>
                        <li>错误响应：<code>{"success": false, "message": "...", "code": 400}</code></li>
                        <li>报表API返回PDF文件，可直接下载</li>
                    </ul>
                </div>

                <div class="info-box">
                    <strong>💡 快速开始：</strong>
                    <ol>
                        <li>1. 使用 <code>/api/register</code> 注册账号</li>
                        <li>2. 使用 <code>/api/login</code> 登录</li>
                        <li>3. 使用 <code>/api/order/create</code> 创建订单购买激活码</li>
                        <li>4. 使用 <code>/api/activation/activate</code> 激活</li>
                        <li>5. 使用报表API查看统计数据</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """
        server_url = _get_server_url()
        doc_template = doc_template.replace('SERVER_URL', server_url)
        return render_template_string(doc_template)

    return app


if __name__ == '__main__':
    server_url = _get_server_url()
    app = create_app()
    port = int(os.getenv('PORT', Config.SERVER_PORT))
    logger.info(f"服务器启动在 {server_url}")
    logger.info(f"本地地址: http://{Config.SERVER_HOST}:{port}")
    logger.info(f"数据库类型: {'MySQL (CloudBase)' if Config.IS_CLOUDBASE else 'SQLite (本地)'}")
    
    # 同时启动9000端口供直连使用（绕过花生壳转发）
    direct_port = int(os.getenv('DIRECT_PORT', '9000'))
    import threading
    def run_direct():
        logger.info(f"直连端口启动: http://{Config.SERVER_HOST}:{direct_port}")
        app.run(host=Config.SERVER_HOST, port=direct_port, debug=False, use_reloader=False)
    
    direct_thread = threading.Thread(target=run_direct, daemon=True)
    direct_thread.start()
    
    # 主端口（花生壳映射的5000端口）
    app.run(host=Config.SERVER_HOST, port=port, debug=False, use_reloader=False)
