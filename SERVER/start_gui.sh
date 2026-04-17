#!/bin/bash

# 启动激活系统服务端（带GUI管理界面）

echo "启动激活系统服务端（带GUI管理界面）..."

# 激活虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "虚拟环境不存在，请先运行 deploy.sh 创建虚拟环境"
    exit 1
fi

# 启动服务器（带GUI界面）
python3 server_gui.py
