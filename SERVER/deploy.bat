@echo off
chcp 65001 >nul
echo ==========================================
echo       激活系统服务端部署脚本
echo ==========================================

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo 检测到Python版本:
python --version

REM 创建虚拟环境
echo.
echo 创建虚拟环境...
python -m venv venv

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo.
echo 安装依赖包...
pip install -r requirements.txt

REM 配置环境变量
echo.
echo ==========================================
echo 请配置环境变量...
echo ==========================================
echo.
echo 复制 .env.example 到 .env 并修改配置
copy .env.example .env

echo.
echo ==========================================
echo 部署完成！
echo ==========================================
echo.
echo 下一步操作：
echo 1. 编辑 .env 文件，配置数据库和邮件
echo 2. 启动服务器: python app.py
echo 3. 访问 http://localhost:5000 查看API文档
echo.
pause
