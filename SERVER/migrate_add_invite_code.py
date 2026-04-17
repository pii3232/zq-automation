#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为 activations 表添加 invite_code 列
"""

from app import create_app
from models import db
from sqlalchemy import text
import os

def migrate():
    """执行迁移"""
    app = create_app()

    with app.app_context():
        # 检查数据库文件是否存在
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        backup_path = db_path + '.backup2'

        if not os.path.exists(db_path):
            print("数据库文件不存在，无需迁移")
            return

        print(f"开始迁移数据库: {db_path}")

        # 备份数据库
        import shutil
        print(f"正在备份数据库到: {backup_path}")
        shutil.copy2(db_path, backup_path)

        try:
            # 使用 ALTER TABLE 添加 invite_code 列
            print("正在添加 invite_code 列...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE activations ADD COLUMN invite_code VARCHAR(50)"))
                conn.commit()

            print("迁移成功！")

        except Exception as e:
            print(f"迁移失败: {e}")
            # 如果列已存在，不视为错误
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("invite_code 列已存在，无需迁移")
            else:
                # 恢复备份
                if os.path.exists(backup_path):
                    print("正在恢复备份...")
                    shutil.copy2(backup_path, db_path)
                raise

if __name__ == '__main__':
    migrate()
