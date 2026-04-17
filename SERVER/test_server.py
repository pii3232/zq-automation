#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试服务端连接和注册API
"""

import requests
import time

def test_server():
    """测试服务端连接"""
    url = "http://localhost:5000/api/register"

    print("=== 测试服务端连接 ===")
    print(f"URL: {url}\n")

    # 测试连接
    try:
        response = requests.get("http://localhost:5000", timeout=5)
        print(f"服务端状态: {response.status_code}")
    except Exception as e:
        print(f"无法连接到服务端: {e}")
        print("\n请确保服务端GUI正在运行！")
        return False

    # 测试注册API
    print("\n=== 测试注册API ===")
    test_user = {
        'username': 'testuser' + str(int(time.time())),
        'email': f'test{int(time.time())}@test.com',
        'password': 'test123456',
        'repeat_password': 'test123456'
    }

    try:
        response = requests.post(url, json=test_user, timeout=10)
        print(f"状态码: {response.status_code}")
        result = response.json()
        print(f"响应: {result}")

        if result.get('success'):
            print("\n✓ 注册API工作正常！")
            return True
        else:
            print(f"\n✗ 注册失败: {result.get('message')}")
            return False

    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == '__main__':
    test_server()
