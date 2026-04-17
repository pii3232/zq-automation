#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查找并检查所有数据库文件
"""

import os
import sqlite3

def find_databases():
    """查找所有数据库文件"""
    print("=== 查找数据库文件 ===\n")

    # 搜索 SERVER 目录
    server_dir = r'd:\3ZDZS-TX2\SERVER'
    if os.path.exists(server_dir):
        print(f"扫描目录: {server_dir}")
        for filename in os.listdir(server_dir):
            if filename.endswith('.db'):
                db_path = os.path.join(server_dir, filename)
                print(f"\n找到数据库: {db_path}")

                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    # 检查表
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    print(f"表: {[t[0] for t in tables]}")

                    # 检查用户表
                    if any('user' in t[0].lower() for t in tables):
                        cursor.execute("SELECT COUNT(*) FROM users")
                        user_count = cursor.fetchone()[0]
                        print(f"用户数量: {user_count}")

                        if user_count > 0:
                            cursor.execute("SELECT id, username, email FROM users LIMIT 5")
                            users = cursor.fetchall()
                            print("用户列表:")
                            for user in users:
                                print(f"  ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}")

                    # 检查激活码表
                    if any('activation_code' in t[0].lower() for t in tables):
                        cursor.execute("SELECT COUNT(*) FROM activation_codes")
                        code_count = cursor.fetchone()[0]
                        print(f"激活码数量: {code_count}")

                    conn.close()

                except Exception as e:
                    print(f"读取失败: {e}")

    # 搜索 CLIENT 目录
    client_dir = r'd:\3ZDZS-TX2\CLIENT'
    if os.path.exists(client_dir):
        print(f"\n扫描目录: {client_dir}")
        for filename in os.listdir(client_dir):
            if filename.endswith('.db'):
                db_path = os.path.join(client_dir, filename)
                print(f"\n找到数据库: {db_path}")

if __name__ == '__main__':
    find_databases()
