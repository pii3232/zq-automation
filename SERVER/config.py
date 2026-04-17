import os
from datetime import timedelta

def _get_database_uri():
    """获取数据库连接 URI - 支持腾讯云CloudBase和华为云"""
    
    # 华为云 RDS MySQL 配置（优先）
    rds_host = os.getenv('RDS_HOST', '')
    rds_port = os.getenv('RDS_PORT', '3306')
    rds_user = os.getenv('RDS_USER', '')
    rds_password = os.getenv('RDS_PASSWORD', '')
    rds_database = os.getenv('RDS_DATABASE', '')
    
    if rds_host and rds_user and rds_database:
        return f"mysql+pymysql://{rds_user}:{rds_password}@{rds_host}:{rds_port}/{rds_database}?charset=utf8mb4"
    
    # 腾讯云 CloudBase MySQL 配置
    mysql_host = os.getenv('MYSQL_HOST', '')
    mysql_port = os.getenv('MYSQL_PORT', '3306')
    mysql_user = os.getenv('MYSQL_USER', '')
    mysql_password = os.getenv('MYSQL_PASSWORD', '')
    mysql_database = os.getenv('MYSQL_DATABASE', '')
    
    # 如果配置了 MySQL，使用 MySQL 连接（CloudBase 生产环境）
    if mysql_host and mysql_user and mysql_database:
        return f"mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4"
    
    # 否则使用 SQLite（本地开发）
    base_dir = os.path.abspath(os.path.dirname(__file__))
    return os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(base_dir, "instance", "activation.db")}')


class Config:
    # 基础目录
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true'
    SQLALCHEMY_POOL_RECYCLE = 3600  # MySQL 连接池回收时间
    SQLALCHEMY_POOL_SIZE = 10  # 连接池大小
    SQLALCHEMY_MAX_OVERFLOW = 20  # 最大溢出连接数
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # 自动检测连接是否有效
        'pool_recycle': 3600,   # 连接回收时间
    }

    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)

    # 邮件配置
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@activation.com')

    # 验证码有效期（分钟）
    VERIFICATION_CODE_EXPIRE_MINUTES = 10

    # 激活码有效期（天）
    ACTIVATION_CODE_EXPIRE_DAYS = 30

    # 激活码长度
    ACTIVATION_CODE_LENGTH = 18

    # 服务器端口 - 华为云/CloudBase 会注入 PORT 环境变量
    SERVER_PORT = int(os.getenv('PORT', os.getenv('SERVER_PORT', '5000')))
    SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
    
    # 华为云环境标识
    IS_HUAWEI_CLOUD = bool(os.getenv('RDS_HOST') and os.getenv('RDS_USER'))
    
    # 腾讯云 CloudBase 环境标识
    IS_CLOUDBASE = bool(os.getenv('MYSQL_HOST') and os.getenv('MYSQL_USER'))
    
    # 云端环境标识（任一云平台）
    IS_CLOUD = IS_HUAWEI_CLOUD or IS_CLOUDBASE
