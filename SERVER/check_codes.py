#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的激活码
"""

from app import create_app
from models import db, ActivationCode

def check_codes():
    """检查激活码"""
    app = create_app()

    with app.app_context():
        codes = ActivationCode.query.all()
        print(f'\n激活码总数: {len(codes)}\n')
        print('-' * 80)

        for i, code in enumerate(codes, 1):
            print(f'{i}. ID: {code.id}')
            print(f'   激活码: {code.code}')
            print(f'   状态: {code.status}')
            print(f'   订单ID: {code.order_id}')
            print(f'   创建时间: {code.created_at}')
            print('-' * 80)

if __name__ == '__main__':
    check_codes()
