@echo off
chcp 65001 >nul
echo ========================================
echo ZQ-Automation 打包脚本
echo ========================================
echo.

echo [1/3] 安装依赖...
E:\5-ZDZS-TXA5\venv_build\Scripts\pip.exe install pyautogui pillow requests opencv-python numpy apscheduler --quiet

echo [2/3] 开始打包...
E:\5-ZDZS-TXA5\venv_build\Scripts\python.exe E:\5-ZDZS-TXA5\build_full.py

echo.
echo [3/3] 打包完成!
echo 输出目录: E:\5-ZDZS-TXA5\dist\ZQ-Automation
echo.
pause
