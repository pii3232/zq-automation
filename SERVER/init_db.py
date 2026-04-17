"""
数据库初始化脚本
用于在 CloudBase MySQL 环境中创建数据库表
"""
import os
import sys
from flask import Flask
from models import db, User
from config import Config
from crypto_utils import AuthHelper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    with app.app_context():
        # 创建所有表
        logger.info("开始创建数据库表...")
        db.create_all()
        logger.info("数据库表创建完成")
        
        # 初始化 admin 用户
        init_admin_user(app)


def init_admin_user(app):
    """初始化 admin 用户"""
    try:
        # 检查 admin 用户是否存在
        admin = User.query.filter_by(username='admin').first()
        if admin:
            logger.info("Admin 用户已存在")
            return
        
        # 创建 admin 用户
        admin = User(
            username='admin',
            email='admin@system.local',
            is_active=True
        )
        # 使用加密后的密码
        admin.set_password(AuthHelper.get_admin_password())
        
        db.session.add(admin)
        db.session.commit()
        
        logger.info("Admin 用户创建成功")
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建 admin 用户失败: {str(e)}")


if __name__ == '__main__':
    init_database()
