from flask import Blueprint, request, jsonify, send_from_directory
from datetime import datetime, timedelta
from models import db, User, VerificationCode, Order, ActivationCode, Activation, Ticket, Workgroup, WorkgroupMember
from utils import (EmailService, VerificationCodeGenerator, ResponseHelper,
                   validate_email, validate_username, validate_password)
from config import Config
from audit_logger import audit_logger
from crypto_utils import CryptoManager, AuthHelper
import json
import logging
import os
import shutil
import time
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)

# ==================== 请求限流 ====================
_rate_limit_store = {}

def rate_limit(max_per_minute=10, path_key=None):
    """请求限流装饰器 - 防止高频请求压垮服务端"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr or 'unknown'
            key = path_key or f.__name__
            now = time.time()
            if client_ip not in _rate_limit_store:
                _rate_limit_store[client_ip] = {}
            ip_store = _rate_limit_store[client_ip]
            if key not in ip_store:
                ip_store[key] = []
            ip_store[key] = [t for t in ip_store[key] if now - t < 60]
            if len(ip_store[key]) >= max_per_minute:
                logger.warning(f"限流: {client_ip} -> {key} ({len(ip_store[key])}次/分)")
                return jsonify(ResponseHelper.error('请求过于频繁，请稍后再试')), 429
            ip_store[key].append(now)
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def decrypt_request_data(data):
    """解密请求数据（如果加密）"""
    if isinstance(data, dict):
        # 检查是否是加密请求
        if 'encrypted' in data and data['encrypted']:
            try:
                decrypted = CryptoManager.decrypt_to_dict(data['data'])
                return decrypted
            except Exception as e:
                logger.error(f"解密请求数据失败: {e}")
                return None
    return data


def encrypt_response_data(data):
    """加密响应数据"""
    try:
        return {'encrypted': True, 'data': CryptoManager.encrypt_dict(data)}
    except Exception as e:
        logger.error(f"加密响应数据失败: {e}")
        return data


@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify(ResponseHelper.success({'status': 'ok'}))


@api_bp.route('/direct_connect', methods=['GET'])
def get_direct_connect():
    """获取直连地址（绕过花生壳转发）"""
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'direct_connect.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            direct_url = config.get('direct_url', '').strip()
            logger.info(f"[直连配置] direct_url: '{direct_url}'")
            if direct_url:
                return jsonify(ResponseHelper.success({
                    'direct_url': direct_url,
                    'updated_at': config.get('updated_at', ''),
                    'note': config.get('note', '')
                }))
        else:
            logger.warning(f"[直连配置] 文件不存在: {config_path}")
    except Exception as e:
        logger.error(f"读取直连配置失败: {e}")
    return jsonify(ResponseHelper.success({'direct_url': '', 'updated_at': '', 'note': '直连地址未配置'}))


@api_bp.route('/secure/login', methods=['POST'])
def secure_login():
    """加密登录接口 - 客户端使用加密数据请求"""
    try:
        data = request.get_json()
        
        # 解密请求数据
        encrypted_data = data.get('data')
        if not encrypted_data:
            return jsonify(ResponseHelper.error('缺少加密数据'))
        
        try:
            decrypted = CryptoManager.decrypt_to_dict(encrypted_data)
        except Exception as e:
            return jsonify(ResponseHelper.error(f'数据解密失败: {str(e)}'))
        
        username = decrypted.get('username', '').strip()
        password = decrypted.get('password', '').strip()
        
        # 验证admin凭证（用于程序内部通信）
        if username == AuthHelper.get_admin_username():
            if password == AuthHelper.get_admin_password():
                # 返回加密的响应
                response_data = ResponseHelper.success({
                    'user_id': 0,
                    'username': 'admin',
                    'role': 'admin',
                    'message': '管理员认证成功'
                }, '登录成功')
                return jsonify(encrypt_response_data(response_data))
        
        # 普通用户登录
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify(ResponseHelper.error('用户名或密码错误'))

        if not user.is_active:
            return jsonify(ResponseHelper.error('账号已被禁用'))

        # 检查激活状态
        activation = Activation.query.filter_by(
            user_id=user.id,
            is_active=True
        ).order_by(Activation.expires_at.desc()).first()

        days_remaining = 0
        if activation and not activation.is_expired():
            days_remaining = activation.get_days_remaining()

        response_data = ResponseHelper.success({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'days_remaining': days_remaining,
            'is_expired': not (activation and not activation.is_expired())
        }, '登录成功')
        
        return jsonify(encrypt_response_data(response_data))

    except Exception as e:
        logger.error(f"加密登录失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/secure/data', methods=['POST'])
def secure_data():
    """加密数据传输接口"""
    try:
        data = request.get_json()
        encrypted_data = data.get('data')
        
        if not encrypted_data:
            return jsonify(ResponseHelper.error('缺少加密数据'))
        
        try:
            decrypted = CryptoManager.decrypt_to_dict(encrypted_data)
        except Exception as e:
            return jsonify(ResponseHelper.error(f'数据解密失败: {str(e)}'))
        
        action = decrypted.get('action')
        params = decrypted.get('params', {})
        
        # 处理不同的数据请求
        result = handle_secure_action(action, params)
        
        response_data = ResponseHelper.success(result)
        return jsonify(encrypt_response_data(response_data))

    except Exception as e:
        logger.error(f"安全数据请求失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


def handle_secure_action(action, params):
    """处理安全动作"""
    if action == 'get_activation_status':
        username = params.get('username')
        user = User.query.filter_by(username=username).first()
        if user:
            activation = Activation.query.filter_by(
                user_id=user.id,
                is_active=True
            ).order_by(Activation.expires_at.desc()).first()
            
            if activation and not activation.is_expired():
                return {
                    'active': True,
                    'days_remaining': activation.get_days_remaining(),
                    'expires_at': activation.expires_at.isoformat()
                }
        return {'active': False}
    
    elif action == 'activate_code':
        username = params.get('username')
        code = params.get('code')
        # 实现激活逻辑...
        return {'success': False, 'message': '功能未实现'}
    
    return {'success': False, 'message': '未知操作'}


# ==================== 用户注册和登录 ====================

@api_bp.route('/register/check', methods=['POST'])
def check_username():
    """检查用户名是否可用"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()

        if not username:
            return jsonify(ResponseHelper.error('用户名不能为空'))

        valid, message = validate_username(username)
        if not valid:
            return jsonify(ResponseHelper.error(message))

        # 检查用户名是否已存在
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify(ResponseHelper.error('用户名已存在'))

        return jsonify(ResponseHelper.success({'available': True}))
    except Exception as e:
        logger.error(f"检查用户名失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        repeat_password = data.get('repeat_password', '').strip()
        email = data.get('email', '').strip()

        # 验证输入
        if not all([username, password, repeat_password, email]):
            return jsonify(ResponseHelper.error('所有字段都必须填写'))

        valid, message = validate_username(username)
        if not valid:
            return jsonify(ResponseHelper.error(message))

        if password != repeat_password:
            return jsonify(ResponseHelper.error('两次输入的密码不一致'))

        valid, message = validate_password(password)
        if not valid:
            return jsonify(ResponseHelper.error(message))

        if not validate_email(email):
            return jsonify(ResponseHelper.error('邮箱格式不正确'))

        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify(ResponseHelper.error('用户名已存在'))

        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify(ResponseHelper.error('该邮箱已被注册'))

        # 创建用户
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        logger.info(f"用户 {username} 注册成功")
        return jsonify(ResponseHelper.success({'user_id': user.id}, '注册成功'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"注册失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        # 解密请求数据
        data = decrypt_request_data(data)
        if data is None:
            return jsonify(ResponseHelper.error('请求数据解密失败'))
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not all([username, password]):
            return jsonify(ResponseHelper.error('用户名和密码不能为空'))

        # 查找用户
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify(ResponseHelper.error('用户名或密码错误'))

        if not user.is_active:
            return jsonify(ResponseHelper.error('账号已被禁用'))

        # 检查是否有有效的激活
        activation = Activation.query.filter_by(
            user_id=user.id,
            is_active=True
        ).order_by(Activation.expires_at.desc()).first()

        days_remaining = 0
        if activation and not activation.is_expired():
            days_remaining = activation.get_days_remaining()

        logger.info(f"用户 {username} 登录成功")
        
        response_data = ResponseHelper.success({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'days_remaining': days_remaining,
            'is_expired': not (activation and not activation.is_expired())
        }, '登录成功')
        
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


# ==================== 用户管理 ====================

@api_bp.route('/admin/users', methods=['GET'])
def get_all_users():
    """获取所有用户列表（管理员功能）"""
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        users_list = []

        for user in users:
            # 获取激活信息
            activation = Activation.query.filter_by(
                user_id=user.id,
                is_active=True
            ).order_by(Activation.expires_at.desc()).first()

            days_remaining = 0
            if activation and not activation.is_expired():
                days_remaining = activation.get_days_remaining()

            users_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'days_remaining': days_remaining,
                'activation_status': 'active' if (activation and not activation.is_expired()) else 'inactive'
            })

        return jsonify(ResponseHelper.success({'users': users_list}, '获取用户列表成功'))

    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/admin/user/toggle', methods=['POST'])
def toggle_user_status():
    """禁用/启用用户（管理员功能）"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify(ResponseHelper.error('用户ID不能为空'))

        user = User.query.get(user_id)
        if not user:
            return jsonify(ResponseHelper.error('用户不存在'))

        # 切换状态
        user.is_active = not user.is_active
        db.session.commit()

        action = '启用' if user.is_active else '禁用'
        
        # 记录审计日志
        audit_logger.log_admin_action(
            'USER_TOGGLE_STATUS',
            target_user=user.username,
            details={'new_status': 'active' if user.is_active else 'disabled'}
        )
        
        logger.info(f"用户 {user.username} (ID: {user_id}) 已被{action}")

        return jsonify(ResponseHelper.success({
            'user_id': user.id,
            'username': user.username,
            'is_active': user.is_active
        }, f'用户已成功{action}'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"切换用户状态失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/admin/user/delete', methods=['POST'])
def delete_user():
    """删除用户（管理员功能）"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify(ResponseHelper.error('用户ID不能为空'))

        user = User.query.get(user_id)
        if not user:
            return jsonify(ResponseHelper.error('用户不存在'))

        username = user.username

        # 删除用户（级联删除相关数据）
        db.session.delete(user)
        db.session.commit()

        # 记录审计日志
        audit_logger.log_admin_action(
            'USER_DELETE',
            target_user=username,
            details={'user_id': user_id}
        )
        
        logger.info(f"用户 {username} (ID: {user_id}) 已被删除")

        return jsonify(ResponseHelper.success({'user_id': user_id}, '用户已成功删除'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除用户失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


# ==================== 激活码相关 ====================

@api_bp.route('/activation/sync', methods=['POST'])
def sync_activation():
    """同步激活状态"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify(ResponseHelper.error('用户不存在'))

        # 检查用户是否被禁用
        if not user.is_active:
            return jsonify(ResponseHelper.error('账号已被禁用，无法同步状态'))

        # 获取最新的激活记录
        activation = Activation.query.filter_by(
            user_id=user.id,
            is_active=True
        ).order_by(Activation.expires_at.desc()).first()

        if not activation:
            return jsonify(ResponseHelper.success({'active': False}))

        # 更新最后同步时间
        activation.last_sync_at = datetime.utcnow()
        db.session.commit()

        result = {
            'active': True,
            'expires_at': activation.expires_at.isoformat(),
            'days_remaining': activation.get_days_remaining(),
            'is_expired': activation.is_expired()
        }

        return jsonify(ResponseHelper.success(result))

    except Exception as e:
        logger.error(f"同步激活状态失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/activation/activate', methods=['POST'])
def activate():
    """使用激活码激活"""
    try:
        data = request.get_json()
        username = data.get('username', '') or ''
        code = data.get('code', '') or ''
        invite_code = data.get('invite_code', '') or ''
        
        username = username.strip()
        code = code.strip()
        invite_code = invite_code.strip()

        if not all([username, code]):
            return jsonify(ResponseHelper.error('用户名和激活码不能为空'))

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify(ResponseHelper.error('用户不存在'))

        # 检查用户是否被禁用
        if not user.is_active:
            return jsonify(ResponseHelper.error('账号已被禁用，请联系管理员'))

        # 验证邀请码（如果提供）
        if invite_code:
            invite_user = User.query.filter_by(username=invite_code).first()
            if not invite_user:
                return jsonify(ResponseHelper.error('无效邀请码'))
            logger.info(f"用户 {username} 使用邀请码 {invite_code}")

        # 查找激活码
        activation_code = ActivationCode.query.filter_by(code=code).first()
        if not activation_code:
            return jsonify(ResponseHelper.error('激活码不存在'))

        if activation_code.status != 'unused':
            return jsonify(ResponseHelper.error('激活码已被使用'))

        # 获取当前激活记录
        current_activation = Activation.query.filter_by(
            user_id=user.id,
            is_active=True
        ).order_by(Activation.expires_at.desc()).first()

        # 计算过期时间
        days_to_add = Config.ACTIVATION_CODE_EXPIRE_DAYS
        if current_activation and not current_activation.is_expired():
            # 在剩余时间基础上增加30天
            base_time = current_activation.expires_at
        else:
            # 从当前时间开始
            base_time = datetime.utcnow()
            if current_activation:
                current_activation.is_active = False

        expires_at = base_time + timedelta(days=days_to_add)

        # 标记激活码已使用
        activation_code.status = 'used'

        # 创建或更新激活记录（包含邀请码）
        if current_activation and not current_activation.is_expired():
            current_activation.code_id = activation_code.id
            current_activation.expires_at = expires_at
            current_activation.invite_code = invite_code if invite_code else None
        else:
            new_activation = Activation(
                user_id=user.id,
                code_id=activation_code.id,
                invite_code=invite_code if invite_code else None,
                expires_at=expires_at
            )
            db.session.add(new_activation)

        db.session.commit()

        logger.info(f"用户 {username} 成功激活，有效期至 {expires_at}，邀请码：{invite_code if invite_code else '无'}")
        
        # 计算实际剩余天数（叠加后的总天数）
        actual_days_remaining = (expires_at - datetime.utcnow()).days
        if (expires_at - datetime.utcnow()).seconds > 0:
            actual_days_remaining += 1  # 不足1天算1天
        
        return jsonify(ResponseHelper.success({
            'expires_at': expires_at.isoformat(),
            'days_remaining': actual_days_remaining
        }, '激活成功'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"激活失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


# ==================== 订单和支付 ====================

@api_bp.route('/order/create', methods=['POST'])
def create_order():
    """创建订单"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        quantity = data.get('quantity', 1)

        if not username:
            return jsonify(ResponseHelper.error('用户名不能为空'))

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify(ResponseHelper.error('用户不存在'))

        quantity = max(1, int(quantity))
        amount = quantity * Config.ACTIVATION_CODE_EXPIRE_DAYS  # 假设每激活码50元

        # 生成订单号
        import time
        order_no = f"ORD{int(time.time() * 1000)}{user.id}"

        order = Order(
            order_no=order_no,
            user_id=user.id,
            amount=amount,
            quantity=quantity,
            unit_price=50.0,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()

        # 返回支付二维码信息（模拟）
        # 实际项目中需要调用微信支付API
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=ORDER_{order_no}"

        logger.info(f"订单 {order_no} 创建成功")
        return jsonify(ResponseHelper.success({
            'order_no': order_no,
            'amount': amount,
            'quantity': quantity,
            'qr_code_url': qr_code_url,
            'payment_info': '请使用微信扫描二维码完成支付'
        }, '订单创建成功'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建订单失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/order/check', methods=['POST'])
def check_order():
    """检查订单支付状态"""
    try:
        data = request.get_json()
        order_no = data.get('order_no', '').strip()

        order = Order.query.filter_by(order_no=order_no).first()
        if not order:
            return jsonify(ResponseHelper.error('订单不存在'))

        return jsonify(ResponseHelper.success({
            'order_no': order.order_no,
            'status': order.status,
            'amount': order.amount,
            'paid_at': order.paid_at.isoformat() if order.paid_at else None
        }))

    except Exception as e:
        logger.error(f"检查订单失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/payment/notify', methods=['POST'])
def payment_notify():
    """支付通知（微信支付回调）"""
    try:
        # 实际项目中这里需要验证微信支付签名
        data = request.get_json()
        order_no = data.get('order_no', '').strip()
        transaction_id = data.get('transaction_id', '')

        order = Order.query.filter_by(order_no=order_no).first()
        if not order or order.status == 'paid':
            return jsonify(ResponseHelper.error('订单无效或已支付'))

        # 更新订单状态
        order.status = 'paid'
        order.transaction_id = transaction_id
        order.paid_at = datetime.utcnow()

        # 生成激活码
        activation_codes = []
        for _ in range(order.quantity):
            code_str = ActivationCode.generate_code(Config.ACTIVATION_CODE_LENGTH)
            # 检查是否重复
            while ActivationCode.query.filter_by(code=code_str).first():
                code_str = ActivationCode.generate_code(Config.ACTIVATION_CODE_LENGTH)

            activation_code = ActivationCode(
                code=code_str,
                order_id=order.id
            )
            db.session.add(activation_code)
            activation_codes.append(code_str)

        db.session.commit()

        # 记录审计日志 - 激活码生成
        audit_logger.log_code_generation(
            codes_generated=activation_codes,
            order_no=order_no,
            user_id=order.user_id
        )
        
        logger.info(f"订单 {order_no} 支付成功，生成 {len(activation_codes)} 个激活码")
        return jsonify(ResponseHelper.success({
            'activation_codes': activation_codes
        }, '支付成功'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"处理支付通知失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


# ==================== 报障系统 ====================

@api_bp.route('/ticket/create', methods=['POST'])
def create_ticket():
    """创建报障工单"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        contact_person = data.get('contact_person', '').strip()
        contact_phone = data.get('contact_phone', '').strip()

        if not all([username, title, content]):
            return jsonify(ResponseHelper.error('用户名、标题和内容不能为空'))

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify(ResponseHelper.error('用户不存在'))

        # 创建报障工单
        ticket = Ticket(
            user_id=user.id,
            title=title,
            content=content,
            contact_person=contact_person or user.username,
            contact_phone=contact_phone
        )
        db.session.add(ticket)
        db.session.commit()

        # 已取消发送确认邮件功能
        # EmailService.send_ticket_confirmation(user.email, ticket.id)

        logger.info(f"用户 {username} 创建报障工单 #{ticket.id}")
        return jsonify(ResponseHelper.success({
            'ticket_id': ticket.id,
            'status': ticket.status
        }, '报障工单已创建，请耐心等待后台处理'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建报障工单失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/ticket/list', methods=['POST'])
def list_tickets():
    """获取用户的报障工单列表"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify(ResponseHelper.error('用户不存在'))

        tickets = Ticket.query.filter_by(user_id=user.id).order_by(
            Ticket.created_at.desc()
        ).all()

        tickets_data = [ticket.to_dict() for ticket in tickets]
        return jsonify(ResponseHelper.success({
            'tickets': tickets_data,
            'total': len(tickets_data)
        }))

    except Exception as e:
        logger.error(f"获取报障工单列表失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


# ==================== 数据库备份管理 ====================

def get_backup_dir():
    """获取备份目录"""
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    return backup_dir

def get_db_path():
    """获取数据库路径"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'activation.db')

@api_bp.route('/backup/manual', methods=['POST'])
def manual_backup():
    """手动备份数据库"""
    try:
        backup_dir = get_backup_dir()
        db_path = get_db_path()

        if not os.path.exists(db_path):
            return jsonify(ResponseHelper.error('数据库文件不存在'))

        # 生成备份文件名（带时间戳）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'activation_db_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)

        # 复制数据库文件
        shutil.copy2(db_path, backup_path)

        # 记录审计日志
        audit_logger.log_backup_operation('CREATE', backup_filename, success=True)
        
        logger.info(f"手动备份成功: {backup_path}")
        return jsonify(ResponseHelper.success({
            'filename': backup_filename,
            'path': backup_path,
            'timestamp': timestamp
        }, '备份成功'))

    except Exception as e:
        audit_logger.log_backup_operation('CREATE', '', success=False)
        logger.error(f"手动备份失败: {str(e)}")
        return jsonify(ResponseHelper.error(f'备份失败: {str(e)}'))

@api_bp.route('/backup/list', methods=['GET'])
def list_backups():
    """获取备份文件列表"""
    try:
        backup_dir = get_backup_dir()

        if not os.path.exists(backup_dir):
            return jsonify(ResponseHelper.success({'backups': []}))

        # 获取所有备份文件
        backups = []
        for filename in os.listdir(backup_dir):
            if filename.endswith('.db'):
                filepath = os.path.join(backup_dir, filename)
                stat = os.stat(filepath)

                # 解析时间戳
                try:
                    # 文件名格式: activation_db_YYYYMMDD_HHMMSS.db
                    timestamp_str = filename.replace('activation_db_', '').replace('.db', '')
                    created_time = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                    created_time_str = created_time.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    created_time_str = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

                # 计算文件大小
                size = stat.st_size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.2f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.2f} MB"

                backups.append({
                    'filename': filename,
                    'size': size_str,
                    'created_time': created_time_str
                })

        # 按创建时间倒序排列
        backups.sort(key=lambda x: x['created_time'], reverse=True)

        return jsonify(ResponseHelper.success({
            'backups': backups,
            'total': len(backups)
        }))

    except Exception as e:
        logger.error(f"获取备份列表失败: {str(e)}")
        return jsonify(ResponseHelper.error(f'获取备份列表失败: {str(e)}'))

@api_bp.route('/backup/restore', methods=['POST'])
def restore_backup():
    """恢复数据库"""
    try:
        data = request.get_json()
        filename = data.get('filename', '').strip()

        if not filename:
            return jsonify(ResponseHelper.error('备份文件名不能为空'))

        backup_dir = get_backup_dir()
        backup_path = os.path.join(backup_dir, filename)

        if not os.path.exists(backup_path):
            return jsonify(ResponseHelper.error('备份文件不存在'))

        db_path = get_db_path()

        # 先备份当前数据库
        current_backup_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        current_backup_filename = f'activation_db_before_restore_{current_backup_timestamp}.db'
        current_backup_path = os.path.join(backup_dir, current_backup_filename)

        if os.path.exists(db_path):
            shutil.copy2(db_path, current_backup_path)
            logger.info(f"当前数据库已备份到: {current_backup_path}")

        # 恢复选定的备份文件
        shutil.copy2(backup_path, db_path)

        # 记录审计日志
        audit_logger.log_database_operation('RESTORE', 'activation.db', {
            'restored_from': filename,
            'backup_created': current_backup_filename
        })

        logger.info(f"数据库恢复成功: {backup_path} -> {db_path}")
        return jsonify(ResponseHelper.success({
            'restored_from': filename,
            'current_backup': current_backup_filename
        }, f'数据库恢复成功\n当前数据库已备份为: {current_backup_filename}'))

    except Exception as e:
        db.session.rollback()
        audit_logger.log_database_operation('RESTORE', 'activation.db', {'error': str(e)})
        logger.error(f"数据库恢复失败: {str(e)}")
        return jsonify(ResponseHelper.error(f'数据库恢复失败: {str(e)}'))

@api_bp.route('/backup/delete', methods=['POST'])
def delete_backup():
    """删除备份文件"""
    try:
        data = request.get_json()
        filename = data.get('filename', '').strip()

        if not filename:
            return jsonify(ResponseHelper.error('备份文件名不能为空'))

        backup_dir = get_backup_dir()
        backup_path = os.path.join(backup_dir, filename)

        if not os.path.exists(backup_path):
            return jsonify(ResponseHelper.error('备份文件不存在'))

        # 删除备份文件
        os.remove(backup_path)

        logger.info(f"备份文件已删除: {backup_path}")
        return jsonify(ResponseHelper.success({
            'filename': filename
        }, '备份文件已删除'))

    except Exception as e:
        logger.error(f"删除备份文件失败: {str(e)}")
        return jsonify(ResponseHelper.error(f'删除备份文件失败: {str(e)}'))

@api_bp.route('/backup/download/<filename>', methods=['GET'])
def download_backup(filename):
    """下载备份文件"""
    try:
        backup_dir = get_backup_dir()
        backup_path = os.path.join(backup_dir, filename)

        if not os.path.exists(backup_path):
            return jsonify(ResponseHelper.error('备份文件不存在'))

        return send_from_directory(backup_dir, filename, as_attachment=True)

    except Exception as e:
        logger.error(f"下载备份文件失败: {str(e)}")
        return jsonify(ResponseHelper.error(f'下载备份文件失败: {str(e)}'))


# ==================== 管理员激活码管理 ====================

@api_bp.route('/admin/codes/generate', methods=['POST'])
def admin_generate_codes():
    """管理员生成激活码"""
    try:
        data = request.get_json()
        quantity = data.get('quantity', 1)

        if not isinstance(quantity, int) or quantity < 1 or quantity > 9999:
            return jsonify(ResponseHelper.error('生成数量必须在1-9999之间'))

        new_codes = []
        for _ in range(quantity):
            # 生成激活码
            code_str = ActivationCode.generate_code(Config.ACTIVATION_CODE_LENGTH)

            # 检查是否重复
            while ActivationCode.query.filter_by(code=code_str).first():
                code_str = ActivationCode.generate_code(Config.ACTIVATION_CODE_LENGTH)

            # 保存到数据库（不关联订单）
            activation_code = ActivationCode(
                code=code_str,
                order_id=None
            )
            db.session.add(activation_code)
            new_codes.append(code_str)

        db.session.commit()

        # 记录审计日志
        audit_logger.log_admin_action(
            'GENERATE_CODES',
            f'生成了 {quantity} 个激活码'
        )

        logger.info(f"管理员生成 {quantity} 个激活码")
        return jsonify(ResponseHelper.success({
            'codes': new_codes,
            'count': len(new_codes)
        }, f'成功生成 {quantity} 个激活码'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"生成激活码失败: {str(e)}")
        return jsonify(ResponseHelper.error(f'生成激活码失败: {str(e)}'))


@api_bp.route('/admin/codes/list', methods=['GET'])
def admin_list_codes():
    """管理员获取激活码列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)

        pagination = ActivationCode.query.order_by(
            ActivationCode.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        codes_list = []
        for code in pagination.items:
            try:
                order_no = code.order.order_no if code.order else None
            except Exception:
                order_no = None
            codes_list.append({
                'id': code.id,
                'code': code.code,
                'status': code.status,
                'created_at': code.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'order_no': order_no
            })

        return jsonify(ResponseHelper.success({
            'codes': codes_list,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }))

    except Exception as e:
        logger.error(f"获取激活码列表失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


# ==================== 管理员用户管理 ====================

@api_bp.route('/admin/users', methods=['GET'])
def admin_list_users():
    """管理员获取用户列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)

        pagination = User.query.order_by(
            User.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        users_list = []
        for user in pagination.items:
            # 计算剩余天数
            days_remaining = 0
            activation = Activation.query.filter_by(user_id=user.id).first()
            if activation and activation.expires_at:
                if activation.expires_at > datetime.utcnow():
                    days_remaining = (activation.expires_at - datetime.utcnow()).days
            
            users_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active,
                'days_remaining': days_remaining,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })

        return jsonify(ResponseHelper.success({
            'users': users_list,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }))

    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/admin/user/toggle', methods=['POST'])
def admin_toggle_user():
    """管理员启用/禁用用户"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify(ResponseHelper.error('用户ID不能为空'))

        user = User.query.get(user_id)
        if not user:
            return jsonify(ResponseHelper.error('用户不存在'))

        user.is_active = not user.is_active
        db.session.commit()

        action = '启用' if user.is_active else '禁用'
        logger.info(f"管理员{action}用户: {user.username}")
        
        # 记录审计日志
        audit_logger.log_admin_action('TOGGLE_USER', f'{action}用户: {user.username}')

        return jsonify(ResponseHelper.success({
            'is_active': user.is_active
        }, f'{action}用户成功'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"切换用户状态失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/admin/user/delete', methods=['POST'])
def admin_delete_user():
    """管理员删除用户"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify(ResponseHelper.error('用户ID不能为空'))

        user = User.query.get(user_id)
        if not user:
            return jsonify(ResponseHelper.error('用户不存在'))

        username = user.username
        
        # 删除用户的所有相关数据
        # 删除激活记录
        Activation.query.filter_by(user_id=user_id).delete()
        # 删除验证码
        VerificationCode.query.filter_by(user_id=user_id).delete()
        # 删除订单
        Order.query.filter_by(user_id=user_id).delete()
        # 删除工单
        Ticket.query.filter_by(user_id=user_id).delete()
        # 删除用户
        db.session.delete(user)
        db.session.commit()

        logger.info(f"管理员删除用户: {username}")
        
        # 记录审计日志
        audit_logger.log_admin_action('DELETE_USER', f'删除用户: {username}')

        return jsonify(ResponseHelper.success(message='用户删除成功'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除用户失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


# ==================== 工作组管理API ====================

@api_bp.route('/workgroup/create', methods=['POST'])
def workgroup_create():
    """创建工作组"""
    try:
        data = decrypt_request_data(request.get_json() or {})
        name = data.get('name', '').strip()
        password = data.get('password', '').strip()
        note = data.get('note', '').strip()
        username = data.get('username', '').strip()

        if not name or not password or not username:
            return jsonify(ResponseHelper.error('工作组名称、口令和用户名不能为空'))

        # 检查名称唯一性
        if Workgroup.query.filter_by(name=name).first():
            return jsonify(ResponseHelper.error('工作组名称已存在'))

        # 创建服务端同步目录
        sync_base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'workgroup_data')
        sync_dir = os.path.join(sync_base, name)
        os.makedirs(sync_dir, exist_ok=True)
        os.makedirs(os.path.join(sync_dir, 'commands'), exist_ok=True)

        # 创建工作组
        wg = Workgroup(name=name, password=password, note=note, creator=username,
                       sync_dir=sync_dir)
        db.session.add(wg)
        db.session.flush()

        # 创建者自动加入，拥有最高权限
        member = WorkgroupMember(workgroup_id=wg.id, username=username, role='owner')
        db.session.add(member)
        db.session.commit()

        logger.info(f"用户 {username} 创建工作组: {name}")
        return jsonify(ResponseHelper.success(message='工作组创建成功',
                                              data={**wg.to_dict(), 'role': 'owner'}))

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建工作组失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/workgroup/join', methods=['POST'])
def workgroup_join():
    """加入工作组"""
    try:
        data = decrypt_request_data(request.get_json() or {})
        password = data.get('password', '').strip()
        username = data.get('username', '').strip()
        game_id = data.get('game_id', '').strip()

        if not password or not username:
            return jsonify(ResponseHelper.error('口令和用户名不能为空'))

        wg = Workgroup.query.filter_by(password=password).first()
        if not wg:
            return jsonify(ResponseHelper.error('口令错误，未找到对应工作组'))

        if not wg.is_active:
            return jsonify(ResponseHelper.error('该工作组已被禁用'))

        # 检查是否已在组中
        existing = WorkgroupMember.query.filter_by(
            workgroup_id=wg.id, username=username).first()
        if existing:
            if existing.is_disabled:
                return jsonify(ResponseHelper.error('你已被该工作组禁用，无法加入'))
            return jsonify(ResponseHelper.success(message='你已在工作组中',
                                                  data={'workgroup': wg.to_dict(),
                                                        'role': existing.role}))

        # 加入工作组
        member = WorkgroupMember(workgroup_id=wg.id, username=username,
                                 game_id=game_id, role='member')
        db.session.add(member)
        db.session.commit()

        logger.info(f"用户 {username} 加入工作组: {wg.name}")
        return jsonify(ResponseHelper.success(message='加入工作组成功',
                                              data={'workgroup': wg.to_dict(),
                                                    'role': 'member'}))

    except Exception as e:
        db.session.rollback()
        logger.error(f"加入工作组失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify(ResponseHelper.error(f'服务器错误: {str(e)}', 500))


@api_bp.route('/workgroup/leave', methods=['POST'])
def workgroup_leave():
    """退出工作组"""
    try:
        data = decrypt_request_data(request.get_json() or {})
        username = data.get('username', '').strip()
        workgroup_id = data.get('workgroup_id')

        if not username or not workgroup_id:
            return jsonify(ResponseHelper.error('参数不完整'))

        member = WorkgroupMember.query.filter_by(
            workgroup_id=workgroup_id, username=username).first()
        if not member:
            return jsonify(ResponseHelper.error('你不在该工作组中'))

        if member.role == 'owner':
            return jsonify(ResponseHelper.error('创建者不能退出工作组，请先转让权限'))

        db.session.delete(member)
        db.session.commit()

        logger.info(f"用户 {username} 退出工作组ID: {workgroup_id}")
        return jsonify(ResponseHelper.success(message='已退出工作组'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"退出工作组失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/workgroup/manage', methods=['POST'])
def workgroup_manage():
    """管理工作组 - 获取成员列表"""
    try:
        data = decrypt_request_data(request.get_json() or {})
        username = data.get('username', '').strip()
        workgroup_id = data.get('workgroup_id')

        if not username or not workgroup_id:
            return jsonify(ResponseHelper.error('参数不完整'))

        # 检查权限 (owner 或 admin)
        member = WorkgroupMember.query.filter_by(
            workgroup_id=workgroup_id, username=username).first()
        if not member or member.role not in ('owner', 'admin'):
            return jsonify(ResponseHelper.error('权限不足'))

        members = WorkgroupMember.query.filter_by(workgroup_id=workgroup_id).all()
        return jsonify(ResponseHelper.success(data={
            'members': [m.to_dict() for m in members]
        }))

    except Exception as e:
        logger.error(f"获取工作组成员失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/workgroup/set_role', methods=['POST'])
def workgroup_set_role():
    """设置成员角色 - 仅owner可操作，管理员最多10名"""
    try:
        data = decrypt_request_data(request.get_json() or {})
        operator = data.get('username', '').strip()
        workgroup_id = data.get('workgroup_id')
        target_username = data.get('target_username', '').strip()
        role = data.get('role', 'member').strip()

        if not operator or not workgroup_id or not target_username:
            return jsonify(ResponseHelper.error('参数不完整'))

        if role not in ('owner', 'admin', 'member'):
            return jsonify(ResponseHelper.error('无效的角色'))

        # 检查操作者权限 (仅owner)
        op = WorkgroupMember.query.filter_by(
            workgroup_id=workgroup_id, username=operator).first()
        if not op or op.role != 'owner':
            return jsonify(ResponseHelper.error('仅创建者可执行此操作'))

        target = WorkgroupMember.query.filter_by(
            workgroup_id=workgroup_id, username=target_username).first()
        if not target:
            return jsonify(ResponseHelper.error('目标用户不在该工作组中'))

        # 检查管理员数量上限（设为管理员时）
        if role == 'admin' and target.role != 'admin':
            admin_count = WorkgroupMember.query.filter_by(
                workgroup_id=workgroup_id, role='admin').count()
            if admin_count >= 10:
                return jsonify(ResponseHelper.error('管理员数量已达上限（最多10名）'))

        target.role = role
        db.session.commit()

        logger.info(f"用户 {operator} 设置 {target_username} 角色: {role}")
        return jsonify(ResponseHelper.success(message=f'已将 {target_username} 设置为 {role}'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"设置角色失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/workgroup/toggle_disable', methods=['POST'])
def workgroup_toggle_disable():
    """禁用/启用成员 - 仅owner可操作"""
    try:
        data = decrypt_request_data(request.get_json() or {})
        operator = data.get('username', '').strip()
        workgroup_id = data.get('workgroup_id')
        target_username = data.get('target_username', '').strip()

        if not operator or not workgroup_id or not target_username:
            return jsonify(ResponseHelper.error('参数不完整'))

        op = WorkgroupMember.query.filter_by(
            workgroup_id=workgroup_id, username=operator).first()
        if not op or op.role != 'owner':
            return jsonify(ResponseHelper.error('仅创建者可执行此操作'))

        target = WorkgroupMember.query.filter_by(
            workgroup_id=workgroup_id, username=target_username).first()
        if not target:
            return jsonify(ResponseHelper.error('目标用户不在该工作组中'))

        if target.role == 'owner':
            return jsonify(ResponseHelper.error('不能禁用创建者'))

        target.is_disabled = not target.is_disabled
        action = '禁用' if target.is_disabled else '启用'
        db.session.commit()

        logger.info(f"用户 {operator} {action}了 {target_username}")
        return jsonify(ResponseHelper.success(message=f'已{action} {target_username}'))

    except Exception as e:
        db.session.rollback()
        logger.error(f"禁用/启用成员失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/workgroup/upload_commands', methods=['POST'])
def workgroup_upload_commands():
    """上传共享命令列表到工作组（创建者/管理员）"""
    try:
        data = decrypt_request_data(request.get_json() or {})
        username = data.get('username', '').strip()
        workgroup_id = data.get('workgroup_id')
        commands = data.get('commands', [])

        if not username or not workgroup_id:
            return jsonify(ResponseHelper.error('参数不完整'))

        member = WorkgroupMember.query.filter_by(
            workgroup_id=workgroup_id, username=username).first()
        if not member:
            return jsonify(ResponseHelper.error('你不在该工作组中'))
        if member.is_disabled:
            return jsonify(ResponseHelper.error('你已被禁用'))
        if member.role not in ('owner', 'admin'):
            return jsonify(ResponseHelper.error('只有创建者或管理员才能编辑共享命令'))

        wg = Workgroup.query.get(workgroup_id)
        if not wg:
            return jsonify(ResponseHelper.error('工作组不存在'))

        import json as _json
        wg.shared_commands = _json.dumps(commands, ensure_ascii=False, indent=2)
        db.session.commit()

        logger.info(f"用户 {username} 更新工作组 {wg.name} 的共享命令，共 {len(commands)} 条")
        return jsonify(ResponseHelper.success(message='共享命令更新成功',
                                              data={'count': len(commands)}))

    except Exception as e:
        logger.error(f"更新共享命令失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/workgroup/get_shared_commands', methods=['GET'])
def workgroup_get_shared_commands():
    """获取工作组的共享命令列表"""
    try:
        username = request.args.get('username', '').strip()
        workgroup_id = request.args.get('workgroup_id', type=int)

        if not username or not workgroup_id:
            return jsonify(ResponseHelper.error('参数不完整'))

        member = WorkgroupMember.query.filter_by(
            workgroup_id=workgroup_id, username=username).first()
        if not member:
            return jsonify(ResponseHelper.error('你不在该工作组中'))

        wg = Workgroup.query.get(workgroup_id)
        if not wg:
            return jsonify(ResponseHelper.error('工作组不存在'))

        import json as _json
        import hashlib
        commands = _json.loads(wg.shared_commands or '[]')
        # 计算命令列表哈希，客户端可用来跳过无更新的同步
        commands_hash = hashlib.md5((wg.shared_commands or '').encode()).hexdigest()

        # 如果客户端传了 hash 参数且匹配，直接返回空命令列表（省带宽）
        client_hash = request.args.get('hash', '').strip()
        if client_hash and client_hash == commands_hash:
            return jsonify(ResponseHelper.success(data={
                'commands': [],
                'member': {'role': member.role, 'is_disabled': member.is_disabled},
                'updated_at': wg.created_at.isoformat() if wg.created_at else None,
                'commands_hash': commands_hash,
                'not_modified': True
            }))

        return jsonify(ResponseHelper.success(data={
            'commands': commands,
            'member': {'role': member.role, 'is_disabled': member.is_disabled},
            'updated_at': wg.created_at.isoformat() if wg.created_at else None,
            'commands_hash': commands_hash
        }))

    except Exception as e:
        logger.error(f"获取共享命令失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/workgroup/upload_files', methods=['POST'])
def workgroup_upload_files():
    """上传本地同步目录内容到服务端（模板文件、图片等）"""
    try:
        data = decrypt_request_data(request.get_json() or {})
        username = data.get('username', '').strip()
        workgroup_id = data.get('workgroup_id')

        if not username or not workgroup_id:
            return jsonify(ResponseHelper.error('参数不完整'))

        member = WorkgroupMember.query.filter_by(
            workgroup_id=workgroup_id, username=username).first()
        if not member:
            return jsonify(ResponseHelper.error('你不在该工作组中'))
        if member.is_disabled:
            return jsonify(ResponseHelper.error('你已被禁用'))
        if member.role not in ('owner', 'admin'):
            return jsonify(ResponseHelper.error('只有创建者或管理员才能上传'))

        wg = Workgroup.query.get(workgroup_id)
        if not wg:
            return jsonify(ResponseHelper.error('工作组不存在'))

        sync_dir = wg.sync_dir
        files = data.get('files', [])

        uploaded_count = 0
        for file_info in files:
            rel_path = file_info.get('path', '')
            content = file_info.get('content', '')
            mtime = file_info.get('mtime', '')

            if not rel_path or content is None:
                continue

            server_path = os.path.join(sync_dir, rel_path)
            server_dir = os.path.dirname(server_path)

            if server_dir and not os.path.exists(server_dir):
                os.makedirs(server_dir, exist_ok=True)

            existing_mtime = ''
            if os.path.exists(server_path):
                existing_mtime = datetime.fromtimestamp(os.path.getmtime(server_path)).strftime('%Y%m%d_%H%M%S')

            if existing_mtime and mtime <= existing_mtime:
                continue

            try:
                with open(server_path, 'w', encoding='utf-8' if rel_path.endswith('.json') else 'wb') as f:
                    if rel_path.endswith('.json'):
                        f.write(content)
                    else:
                        import base64
                        f.write(base64.b64decode(content))
                uploaded_count += 1
            except Exception:
                continue

        logger.info(f"用户 {username} 上传 {uploaded_count} 个文件到工作组 {wg.name}")
        return jsonify(ResponseHelper.success(message=f'上传成功 ({uploaded_count} 个文件)',
                                              data={'uploaded': uploaded_count}))

    except Exception as e:
        logger.error(f"上传文件失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/workgroup/get_files', methods=['POST'])
def workgroup_get_files():
    """获取服务端同步目录中的所有文件列表"""
    try:
        data = decrypt_request_data(request.get_json() or {})
        username = data.get('username', '').strip()
        workgroup_id = data.get('workgroup_id')

        if not username or not workgroup_id:
            return jsonify(ResponseHelper.error('参数不完整'))

        member = WorkgroupMember.query.filter_by(
            workgroup_id=workgroup_id, username=username).first()
        if not member:
            return jsonify(ResponseHelper.error('你不在该工作组中'))
        if member.is_disabled:
            return jsonify(ResponseHelper.error('你已被禁用'))

        wg = Workgroup.query.get(workgroup_id)
        if not wg:
            return jsonify(ResponseHelper.error('工作组不存在'))

        sync_dir = wg.sync_dir
        file_list = []

        if os.path.exists(sync_dir):
            for root, dirs, files in os.walk(sync_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    rel_path = os.path.relpath(fpath, sync_dir)
                    mtime = datetime.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y%m%d_%H%M%S')
                    try:
                        if fname.endswith('.json'):
                            with open(fpath, 'r', encoding='utf-8') as f:
                                content = f.read()
                            file_list.append({'path': rel_path, 'mtime': mtime, 'content': content})
                        else:
                            with open(fpath, 'rb') as f:
                                import base64
                                content = base64.b64encode(f.read()).decode('utf-8')
                            file_list.append({'path': rel_path, 'mtime': mtime, 'content': content})
                    except Exception:
                        continue

        return jsonify(ResponseHelper.success(data={'files': file_list}))

    except Exception as e:
        logger.error(f"获取文件列表失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/workgroup/sync', methods=['POST'])
@rate_limit(max_per_minute=8)
def workgroup_sync():
    """同步 - 返回工作组最新的命令文件列表"""
    try:
        data = decrypt_request_data(request.get_json() or {})
        username = data.get('username', '').strip()
        workgroup_id = data.get('workgroup_id')
        last_sync = data.get('last_sync', '')  # 客户端上次同步时间

        if not username or not workgroup_id:
            return jsonify(ResponseHelper.error('参数不完整'))

        member = WorkgroupMember.query.filter_by(
            workgroup_id=workgroup_id, username=username).first()
        if not member:
            return jsonify(ResponseHelper.error('你不在该工作组中'))
        if member.is_disabled:
            return jsonify(ResponseHelper.error('你已被禁用'))

        wg = Workgroup.query.get(workgroup_id)
        if not wg:
            return jsonify(ResponseHelper.error('工作组不存在'))

        # 扫描同步目录中的命令文件
        cmd_dir = os.path.join(wg.sync_dir, 'commands')
        new_files = []
        if os.path.exists(cmd_dir):
            import json as _json
            from datetime import datetime as _dt
            for fname in sorted(os.listdir(cmd_dir)):
                if not fname.endswith('.json'):
                    continue
                fpath = os.path.join(cmd_dir, fname)
                mtime = _dt.fromtimestamp(os.path.getmtime(fpath)).strftime('%Y%m%d_%H%M%S')
                if last_sync and mtime <= last_sync:
                    continue
                try:
                    with open(fpath, 'r', encoding='utf-8') as f:
                        file_commands = _json.load(f)
                    new_files.append({
                        'filename': fname,
                        'mtime': mtime,
                        'commands': file_commands
                    })
                except Exception:
                    continue

        from datetime import datetime as _dt
        current_sync = _dt.now().strftime('%Y%m%d_%H%M%S')
        return jsonify(ResponseHelper.success(data={
            'new_files': new_files,
            'current_sync': current_sync
        }))

    except Exception as e:
        logger.error(f"同步失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/workgroup/my_info', methods=['POST'])
def workgroup_my_info():
    """获取当前用户的工作组信息"""
    try:
        data = decrypt_request_data(request.get_json() or {})
        username = data.get('username', '').strip()

        if not username:
            return jsonify(ResponseHelper.error('用户名不能为空'))

        members = WorkgroupMember.query.filter_by(username=username).all()
        result = []
        for m in members:
            if not m.is_disabled:
                result.append({
                    'workgroup': m.workgroup.to_dict() if m.workgroup else None,
                    'role': m.role,
                    'game_id': m.game_id
                })

        return jsonify(ResponseHelper.success(data={'workgroups': result}))

    except Exception as e:
        logger.error(f"获取工作组信息失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))


@api_bp.route('/admin/workgroups', methods=['GET'])
def admin_workgroups():
    """管理员查看所有工作组"""
    try:
        workgroups = Workgroup.query.all()
        return jsonify(ResponseHelper.success(data={
            'workgroups': [wg.to_dict() for wg in workgroups]
        }))

    except Exception as e:
        logger.error(f"获取工作组列表失败: {str(e)}")
        return jsonify(ResponseHelper.error('服务器错误', 500))
