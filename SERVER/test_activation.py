#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试激活API
"""

from app import create_app
from models import db, User, ActivationCode, Activation
from config import Config
import requests

def test_activation():
    """测试激活功能"""
    app = create_app()

    # 先在数据库中检查
    with app.app_context():
        # 检查用户
        users = User.query.all()
        print(f"\n=== 数据库中的用户 ===")
        for user in users:
            print(f"用户名: {user.username}, ID: {user.id}")

        # 检查激活码
        codes = ActivationCode.query.all()
        print(f"\n=== 数据库中的激活码 ===")
        for code in codes:
            print(f"激活码: {code.code}, 状态: {code.status}, ID: {code.id}")

        # 检查激活记录
        activations = Activation.query.all()
        print(f"\n=== 数据库中的激活记录 ===")
        for act in activations:
            print(f"用户ID: {act.user_id}, 激活码ID: {act.code_id}, 有效期至: {act.expires_at}")

    # 测试API
    if not users:
        print("\n错误: 数据库中没有用户，请先注册用户")
        return

    if not codes:
        print("\n错误: 数据库中没有激活码")
        return

    username = users[0].username
    code = codes[0].code

    print(f"\n=== 测试API激活 ===")
    print(f"用户名: {username}")
    print(f"激活码: {code}")

    url = f"http://localhost:{Config.SERVER_PORT}/api/activation/activate"

    try:
        response = requests.post(url, json={
            'username': username,
            'code': code
        }, timeout=10)

        print(f"\n=== API响应 ===")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.json()}")

    except Exception as e:
        print(f"\n错误: {e}")
        print("请确保服务器正在运行")

if __name__ == '__main__':
    test_activation()
