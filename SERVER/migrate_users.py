#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移用户数据：从根目录数据库迁移到SERVER目录数据库
"""

import sqlite3
import sys

def migrate_users():
    """迁移用户数据"""
    source_db = r'd:\3ZDZS-TX2\instance\activation.db'
    target_db = r'd:\3ZDZS-TX2\SERVER\instance\activation.db'

    print(f"源数据库: {source_db}")
    print(f"目标数据库: {target_db}\n")

    try:
        # 连接源数据库
        source_conn = sqlite3.connect(source_db)
        source_cursor = source_conn.cursor()

        # 获取用户数据
        source_cursor.execute("SELECT id, username, password_hash, email, created_at, is_active FROM users")
        users = source_cursor.fetchall()

        print(f"找到 {len(users)} 个用户:\n")
        for user in users:
            print(f"  ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[3]}")

        # 关闭源数据库
        source_conn.close()

        # 连接目标数据库
        target_conn = sqlite3.connect(target_db)
        target_cursor = target_conn.cursor()

        # 检查目标数据库中是否已有这些用户
        for user in users:
            user_id, username, password_hash, email, created_at, is_active = user

            # 检查邮箱是否已存在
            target_cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if target_cursor.fetchone():
                print(f"\n用户 {username} (邮箱: {email}) 已存在，跳过")
                continue

            # 检查ID是否已存在，如果存在则使用新的ID
            target_cursor.execute("SELECT MAX(id) FROM users")
            max_id = target_cursor.fetchone()[0]
            new_id = (max_id + 1) if max_id else 1

            target_cursor.execute("""
                INSERT INTO users (id, username, password_hash, email, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (new_id, username, password_hash, email, created_at, is_active))
            print(f"\n已迁移用户: {username} (邮箱: {email}), 原ID: {user_id}, 新ID: {new_id}")

        target_conn.commit()
        target_conn.close()

        print("\n迁移完成！")
        print("\n现在请重启服务端GUI和客户端")

    except Exception as e:
        print(f"迁移失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    migrate_users()
