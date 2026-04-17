#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置数据库脚本：删除旧数据库，创建新表结构
"""

from app import create_app
from models import db, User, Order, ActivationCode, Activation, Ticket, VerificationCode
import os

def reset_database():
    """重置数据库"""
    app = create_app()

    with app.app_context():
        # 获取数据库文件路径
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')

        print(f"数据库路径: {db_path}")

        # 检查数据库是否存在
        if os.path.exists(db_path):
            choice = input(f"确定要删除现有数据库吗？(y/n): ").strip().lower()
            if choice == 'y':
                os.remove(db_path)
                print("已删除旧数据库")
            else:
                print("取消操作")
                return
        else:
            print("数据库不存在，将创建新数据库")

        # 创建新表结构
        print("正在创建新表结构...")
        db.create_all()

        print("数据库重置完成！")
        print("\n现在可以启动服务器并生成激活码了。")

if __name__ == '__main__':
    reset_database()
