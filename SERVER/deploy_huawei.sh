#!/bin/bash
# 华为云函数计算部署脚本
# Huawei Cloud FunctionGraph Deployment Script

set -e

echo "========================================="
echo "华为云激活服务部署脚本"
echo "========================================="

# 检查环境变量
if [ -z "$RDS_HOST" ] || [ -z "$RDS_USER" ] || [ -z "$RDS_DATABASE" ]; then
    echo "错误: 请设置以下环境变量:"
    echo "  RDS_HOST - 华为云RDS主机地址"
    echo "  RDS_USER - RDS用户名"
    echo "  RDS_PASSWORD - RDS密码"
    echo "  RDS_DATABASE - 数据库名"
    exit 1
fi

# 默认配置
FUNCTION_NAME=${FUNCTION_NAME:-"activation-server"}
FUNCTION_NAMESPACE=${FUNCTION_NAMESPACE:-"default"}
REGION=${REGION:-"cn-north-4"}

echo "配置信息:"
echo "  函数名称: $FUNCTION_NAME"
echo "  命名空间: $FUNCTION_NAMESPACE"
echo "  区域: $REGION"
echo "  RDS主机: $RDS_HOST"

# 打包函数代码
echo ""
echo "步骤1: 打包函数代码..."
mkdir -p build
pip install -r requirements.txt -t build/
cp -r app.py models.py routes.py config.py utils.py crypto_utils.py audit_logger.py check_codes.py reports.py healthcheck.py init_db.py build/
cd build
zip -r ../function.zip ./
cd ..
echo "  打包完成: function.zip"

# 部署函数（需要先安装华为云CLI）
echo ""
echo "步骤2: 部署函数..."
if command -v hwcloud &> /dev/null || command -v functiongraph &> /dev/null; then
    # 使用华为云CLI部署
    hwcloud functiongraph function create \
        --name $FUNCTION_NAME \
        --namespace $FUNCTION_NAMESPACE \
        --runtime Python3.9 \
        --handler app.app \
        --memory-size 512 \
        --timeout 30 \
        --zip-file function.zip
    echo "  部署完成!"
else
    echo "  警告: 未安装华为云CLI，请手动部署"
    echo "  请在华为云控制台手动部署 function.zip"
fi

# 创建触发器（HTTP触发）
echo ""
echo "步骤3: 创建HTTP触发器..."
echo "  提示: 请在华为云控制台创建HTTP触发器获取公网访问地址"

echo ""
echo "========================================="
echo "部署完成!"
echo "========================================="
echo ""
echo "请在华为云控制台完成以下配置:"
echo "1. 创建HTTP触发器获取访问地址"
echo "2. 配置域名绑定（可选）"
echo "3. 更新客户端配置中的服务器地址"
