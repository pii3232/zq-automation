#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：将 activation_codes.order_id 改为可空
"""

from app import create_app
from models import db
import os

def migrate():
    """执行迁移"""
    app = create_app()

    with app.app_context():
        # 检查数据库文件是否存在
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        backup_path = db_path + '.backup'

        if not os.path.exists(db_path):
            print("数据库文件不存在，无需迁移")
            return

        print(f"开始迁移数据库: {db_path}")

        # 备份数据库
        import shutil
        print(f"正在备份数据库到: {backup_path}")
        shutil.copy2(db_path, backup_path)

        try:
            # 创建新表结构
            print("正在创建新表结构...")
            db.create_all()

            # 使用 ALTER TABLE 修改 order_id 字段
            print("正在修改表结构...")
            with db.engine.connect() as conn:
                # SQLite 的 ALTER TABLE 有限制，需要重建表
                # 1. 创建新表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS activation_codes_new (
                        id INTEGER PRIMARY KEY,
                        code VARCHAR(50) UNIQUE NOT NULL,
                        order_id INTEGER,
                        status VARCHAR(20) DEFAULT 'unused',
                        created_at DATETIME,
                        FOREIGN KEY (order_id) REFERENCES orders (id)
                    )
                """)

                # 2. 复制数据
                conn.execute("""
                    INSERT INTO activation_codes_new (id, code, order_id, status, created_at)
                    SELECT id, code, order_id, status, created_at FROM activation_codes
                """)

                # 3. 删除旧表
                conn.execute("DROP TABLE activation_codes")

                # 4. 重命名新表
                conn.execute("ALTER TABLE activation_codes_new RENAME TO activation_codes")

                # 5. 重建索引
                conn.execute("CREATE INDEX IF NOT EXISTS ix_activation_codes_code ON activation_codes (code)")

            print("迁移成功！")

        except Exception as e:
            print(f"迁移失败: {e}")
            # 恢复备份
            if os.path.exists(backup_path):
                print("正在恢复备份...")
                shutil.copy2(backup_path, db_path)
            raise

if __name__ == '__main__':
    migrate()
