#!/bin/bash

# 激活系统服务端部署脚本

echo "=========================================="
echo "      激活系统服务端部署脚本"
echo "=========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python3"
    exit 1
fi

echo "检测到Python版本: $(python3 --version)"

# 创建虚拟环境
echo ""
echo "创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo ""
echo "安装依赖包..."
pip install -r requirements.txt

# 配置环境变量
echo ""
echo "=========================================="
echo "请配置环境变量..."
echo "=========================================="
echo ""
echo "复制 .env.example 到 .env 并修改配置"
cp .env.example .env

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 编辑 .env 文件，配置数据库和邮件"
echo "2. 启动服务器: python app.py"
echo "3. 访问 http://localhost:5000 查看API文档"
echo ""
