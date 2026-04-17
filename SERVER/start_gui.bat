@echo off
chcp 65001 >nul

echo 启动激活系统服务端（带GUI管理界面）...

REM 激活虚拟环境
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo 虚拟环境不存在，请先运行 deploy.bat 创建虚拟环境
    pause
    exit /b 1
)

REM 启动服务器（带GUI界面）
python server_gui.py

pause
