from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string

db = SQLAlchemy()

class User(db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # 关系
    orders = db.relationship('Order', backref='user', lazy=True)
    tickets = db.relationship('Ticket', backref='user', lazy=True)
    activations = db.relationship('Activation', backref='user', lazy=True)

    def set_password(self, password):
        """设置密码（加密）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }


class VerificationCode(db.Model):
    """验证码表"""
    __tablename__ = 'verification_codes'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    code_type = db.Column(db.String(20), default='register')  # register, reset

    def is_valid(self):
        """检查验证码是否有效"""
        return not self.used and datetime.utcnow() < self.expires_at

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'code_type': self.code_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'used': self.used
        }


class Order(db.Model):
    """订单表"""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=50.0)
    status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    wechat_order_no = db.Column(db.String(100))
    transaction_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)

    # 关系
    codes = db.relationship('ActivationCode', backref='order', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'amount': self.amount,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'status': self.status,
            'wechat_order_no': self.wechat_order_no,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }


class ActivationCode(db.Model):
    """激活码表"""
    __tablename__ = 'activation_codes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)  # 改为允许为空
    status = db.Column(db.String(20), default='unused')  # unused, used, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系
    activation = db.relationship('Activation', backref='activation_code', uselist=False)

    @staticmethod
    def generate_code(length=18):
        """生成随机激活码（包含大小写字母和数字）"""
        alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits
        # 使用时间戳增加唯一性
        timestamp = str(int(datetime.utcnow().timestamp()))
        random_part = ''.join(secrets.choice(alphabet) for _ in range(length - 6))
        code = random_part + timestamp[-6:]
        # 打乱顺序
        code_list = list(code)
        secrets.SystemRandom().shuffle(code_list)
        return ''.join(code_list)

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'order_id': self.order_id,
            'order_no': self.order.order_no if self.order else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Activation(db.Model):
    """激活记录表"""
    __tablename__ = 'activations'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code_id = db.Column(db.Integer, db.ForeignKey('activation_codes.id'), nullable=False)
    invite_code = db.Column(db.String(50), nullable=True)  # 邀请码（注册用户名）
    activated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_sync_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'code': self.activation_code.code if self.activation_code else None,
            'invite_code': self.invite_code,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'days_remaining': self.get_days_remaining()
        }

    def get_days_remaining(self):
        """获取剩余天数"""
        if not self.expires_at:
            return 0
        remaining = self.expires_at - datetime.utcnow()
        return max(0, remaining.days)

    def is_expired(self):
        """检查是否过期"""
        return datetime.utcnow() > self.expires_at


class Workgroup(db.Model):
    """工作组表"""
    __tablename__ = 'workgroups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(100), nullable=False)  # 进入口令
    note = db.Column(db.String(500), default='')
    creator = db.Column(db.String(50), nullable=False)  # 创建者用户名
    sync_dir = db.Column(db.String(500), default='')  # 服务端同步目录路径
    shared_commands = db.Column(db.Text, default='[]')  # 共享命令列表(JSON格式)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)  # 工作组是否启用

    # 关系
    members = db.relationship('WorkgroupMember', backref='workgroup', lazy=True,
                              cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'password': self.password,
            'note': self.note,
            'creator': self.creator,
            'sync_dir': self.sync_dir,
            'shared_commands': self.shared_commands,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'member_count': len(self.members) if self.members else 0
        }


class WorkgroupMember(db.Model):
    """工作组成员表"""
    __tablename__ = 'workgroup_members'

    id = db.Column(db.Integer, primary_key=True)
    workgroup_id = db.Column(db.Integer, db.ForeignKey('workgroups.id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)  # 用户名
    game_id = db.Column(db.String(100), default='')  # 游戏ID
    role = db.Column(db.String(20), default='member')  # owner/admin/member
    is_disabled = db.Column(db.Boolean, default=False)  # 是否被禁用
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'workgroup_id': self.workgroup_id,
            'workgroup_name': self.workgroup.name if self.workgroup else None,
            'username': self.username,
            'game_id': self.game_id,
            'role': self.role,
            'is_disabled': self.is_disabled,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None
        }


class Ticket(db.Model):
    """报障工单表"""
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    contact_person = db.Column(db.String(50))
    contact_phone = db.Column(db.String(20))
    status = db.Column(db.String(20), default='pending')  # pending, processing, resolved, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else None,
            'email': self.user.email if self.user else None,
            'title': self.title,
            'content': self.content,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
