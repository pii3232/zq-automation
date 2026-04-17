@echo off
chcp 65001 >nul
cd /d E:\5-ZDZS-TXA5
echo 正在安装依赖...
venv_build\Scripts\python.exe -m pip install pyinstaller PyQt5 opencv-python pillow apscheduler requests pyautogui -q
echo 正在打包...
venv_build\Scripts\python.exe build_full.py
echo 完成!

