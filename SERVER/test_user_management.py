#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用户管理功能
"""

import requests
import time

def test_user_management():
    """测试用户管理功能"""
    base_url = "http://localhost:5000/api"

    print("=== 测试用户管理功能 ===\n")

    # 1. 获取用户列表
    print("1. 获取用户列表...")
    response = requests.get(f"{base_url}/admin/users", timeout=10)
    result = response.json()
    print(f"   状态码: {response.status_code}")
    if result.get('success'):
        users = result.get('data', {}).get('users', [])
        print(f"   ✓ 成功获取 {len(users)} 个用户")
        for user in users:
            status = "正常" if user['is_active'] else "禁用"
            print(f"     - {user['username']} ({status})")
    else:
        print(f"   ✗ 失败: {result.get('message')}")
        return

    if not users:
        print("\n没有用户，创建测试用户...")
        response = requests.post(f"{base_url}/register", json={
            'username': 'testuser_admin',
            'email': 'test_admin@test.com',
            'password': 'test123456',
            'repeat_password': 'test123456'
        }, timeout=10)
        result = response.json()
        if result.get('success'):
            print("✓ 测试用户创建成功")
            user_id = result.get('data', {}).get('user_id')
        else:
            print(f"✗ 创建失败: {result.get('message')}")
            return

        # 重新获取用户列表
        response = requests.get(f"{base_url}/admin/users", timeout=10)
        result = response.json()
        users = result.get('data', {}).get('users', [])
        if users:
            user_id = users[0]['id']
            username = users[0]['username']
        else:
            return
    else:
        user_id = users[0]['id']
        username = users[0]['username']

    # 2. 测试禁用用户
    print(f"\n2. 禁用用户 '{username}' (ID: {user_id})...")
    response = requests.post(f"{base_url}/admin/user/toggle", json={
        'user_id': user_id
    }, timeout=10)
    result = response.json()
    print(f"   状态码: {response.status_code}")
    if result.get('success'):
        print(f"   ✓ 用户已禁用")
        print(f"   消息: {result.get('message')}")
    else:
        print(f"   ✗ 失败: {result.get('message')}")
        return

    # 3. 验证禁用后无法登录
    print(f"\n3. 验证禁用后无法登录...")
    response = requests.post(f"{base_url}/login", json={
        'username': username,
        'password': 'test123456'
    }, timeout=10)
    result = response.json()
    print(f"   状态码: {response.status_code}")
    if not result.get('success'):
        print(f"   ✓ 登录被拒绝")
        print(f"   消息: {result.get('message')}")
    else:
        print(f"   ✗ 错误：禁用后仍能登录")

    # 4. 验证禁用后无法激活
    print(f"\n4. 验证禁用后无法激活...")
    # 先创建一个激活码用于测试
    from app import create_app
    from models import db, ActivationCode
    app = create_app()
    with app.app_context():
        test_code = "TEST00000000000001"
        code = ActivationCode(code=test_code, order_id=None)
        db.session.add(code)
        db.session.commit()

    response = requests.post(f"{base_url}/activation/activate", json={
        'username': username,
        'code': test_code
    }, timeout=10)
    result = response.json()
    print(f"   状态码: {response.status_code}")
    if not result.get('success'):
        print(f"   ✓ 激活被拒绝")
        print(f"   消息: {result.get('message')}")
    else:
        print(f"   ✗ 错误：禁用后仍能激活")

    # 5. 重新启用用户
    print(f"\n5. 重新启用用户 '{username}'...")
    response = requests.post(f"{base_url}/admin/user/toggle", json={
        'user_id': user_id
    }, timeout=10)
    result = response.json()
    print(f"   状态码: {response.status_code}")
    if result.get('success'):
        print(f"   ✓ 用户已启用")
        print(f"   消息: {result.get('message')}")

    # 6. 验证启用后可以登录
    print(f"\n6. 验证启用后可以登录...")
    response = requests.post(f"{base_url}/login", json={
        'username': username,
        'password': 'test123456'
    }, timeout=10)
    result = response.json()
    print(f"   状态码: {response.status_code}")
    if result.get('success'):
        print(f"   ✓ 登录成功")
    else:
        print(f"   ✗ 登录失败: {result.get('message')}")

    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_user_management()
