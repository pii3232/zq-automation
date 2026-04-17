@echo off
chcp 65001 >nul

echo 启动激活系统服务端...

REM 激活虚拟环境
'call venv\Scripts\activate.bat

REM 启动服务器
python app.py
