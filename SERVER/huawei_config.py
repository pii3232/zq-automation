# 华为云函数计算配置
# Huawei Cloud FunctionGraph 配置

import os

class HuaweiConfig:
    """华为云函数计算配置"""
    
    # 函数配置
    FUNCTION_NAME = os.getenv('FUNCTION_NAME', 'activation-server')
    FUNCTION_NAMESPACE = os.getenv('FUNCTION_NAMESPACE', 'default')
    
    # 华为云 RDS MySQL 配置
    # 环境变量名与华为云一致
    RDS_HOST = os.getenv('RDS_HOST', '')
    RDS_PORT = os.getenv('RDS_PORT', '3306')
    RDS_USER = os.getenv('RDS_USER', '')
    RDS_PASSWORD = os.getenv('RDS_PASSWORD', '')
    RDS_DATABASE = os.getenv('RDS_DATABASE', '')
    
    # 如果配置了 RDS MySQL，使用 MySQL 连接
    if RDS_HOST and RDS_USER and RDS_DATABASE:
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{RDS_USER}:{RDS_PASSWORD}@{RDS_HOST}:{RDS_PORT}/{RDS_DATABASE}?charset=utf8mb4"
        IS_HUAWEI_CLOUD = True
    else:
        SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///activation.db')
        IS_HUAWEI_CLOUD = False
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
    
    # 邮件配置
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.qq.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@activation.com')
    
    # 华为云函数入口
    HANDLER = os.getenv('HANDLER', 'app.app')
    RUNTIME = os.getenv('RUNTIME', 'Python3.9')
    
    # 日志级别
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


# 华为云函数打包配置
HUAWEI_FUNCTION_PACKAGE = {
    "runtime": "Python3.9",
    "handler": "app.app",
    "memory_size": 512,
    "timeout": 30,
    "description": "ZQ Activation Server - 激活服务系统",
    "environment_variables": {
        "RDS_HOST": "your-rds-host.rds.huaweicloud.com",
        "RDS_PORT": "3306",
        "RDS_USER": "your-username",
        "RDS_PASSWORD": "your-password",
        "RDS_DATABASE": "activation_db",
        "JWT_SECRET_KEY": "change-this-secret-key",
        "MAIL_SERVER": "smtp.qq.com",
        "MAIL_PORT": "587",
        "MAIL_USERNAME": "your-email@qq.com",
        "MAIL_PASSWORD": "your-email-password"
    }
}
