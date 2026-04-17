# -*- coding: utf-8 -*-
"""
完整打包脚本 - 创建虚拟环境并打包
"""
import subprocess
import sys
import os
import shutil

VENV_DIR = "venv_build"
PROJECT_NAME = "ZQ-Automation"

print("=" * 60)
print("ZQ-Automation 完整打包脚本")
print("=" * 60)

# 步骤1: 创建虚拟环境
if not os.path.exists(VENV_DIR):
    print("\n[1/4] 创建虚拟环境...")
    subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
    print(f"  虚拟环境已创建: {VENV_DIR}")
else:
    print(f"\n[1/4] 虚拟环境已存在: {VENV_DIR}")

# 获取虚拟环境的Python路径
if os.name == 'nt':
    venv_python = os.path.join(VENV_DIR, "Scripts", "python.exe")
    venv_pip = os.path.join(VENV_DIR, "Scripts", "pip.exe")
else:
    venv_python = os.path.join(VENV_DIR, "bin", "python")
    venv_pip = os.path.join(VENV_DIR, "bin", "pip")

# 步骤2: 安装依赖
print("\n[2/4] 安装依赖...")
subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], check=True)
subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements_build.txt"], check=True)
print("  依赖安装完成")

# 步骤3: 测试导入
print("\n[3/4] 测试导入...")
test_code = '''
import sys
print(f"Python: {sys.version}")
try:
    import tkinter
    print("  tkinter: OK")
except ImportError as e:
    print(f"  tkinter: FAILED - {e}")
    sys.exit(1)
try:
    import pyautogui
    print("  pyautogui: OK")
except ImportError as e:
    print(f"  pyautogui: FAILED - {e}")
    sys.exit(1)
try:
    import cv2
    print("  cv2: OK")
except ImportError as e:
    print(f"  cv2: FAILED - {e}")
    sys.exit(1)
try:
    import numpy
    print("  numpy: OK")
except ImportError as e:
    print(f"  numpy: FAILED - {e}")
    sys.exit(1)
try:
    from PIL import Image
    print("  PIL: OK")
except ImportError as e:
    print(f"  PIL: FAILED - {e}")
    sys.exit(1)
try:
    import requests
    print("  requests: OK")
except ImportError as e:
    print(f"  requests: FAILED - {e}")
    sys.exit(1)
try:
    import apscheduler
    print("  apscheduler: OK")
except ImportError as e:
    print(f"  apscheduler: FAILED - {e}")
    sys.exit(1)
print("所有依赖测试通过!")
'''
result = subprocess.run([venv_python, "-c", test_code])
if result.returncode != 0:
    print("依赖测试失败，请检查安装")
    sys.exit(1)

# 步骤4: 清理并打包
print("\n[4/4] 开始打包...")
for d in ["build", "dist"]:
    if os.path.exists(d):
        try:
            shutil.rmtree(d)
            print(f"  清理: {d}")
        except PermissionError:
            print(f"  警告: {d} 被占用，跳过清理")

for f in ["main.spec", "ZQ-Automation.spec"]:
    if os.path.exists(f):
        os.remove(f)
        print(f"  清理: {f}")

# PyInstaller命令
cmd = [
    venv_python,
    "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--console",
    "--name", PROJECT_NAME,
    # 排除不需要的模块
    "--exclude-module", "PyQt5",
    "--exclude-module", "PyQt6",
    "--exclude-module", "PySide2",
    "--exclude-module", "PySide6",
    "--exclude-module", "torch",
    "--exclude-module", "tensorflow",
    "--exclude-module", "matplotlib",
    "--exclude-module", "scipy",
    "--exclude-module", "pandas",
    "--exclude-module", "IPython",
    "--exclude-module", "jupyter",
    "--exclude-module", "notebook",
    # 隐藏导入
    "--hidden-import", "apscheduler",
    "--hidden-import", "apscheduler.schedulers.background",
    # 数据文件
    "--add-data", f"data{os.pathsep}data",
    "--add-data", f"SERVER{os.pathsep}SERVER",
    # 主脚本
    "main.py"
]

print(f"\n执行: {' '.join(cmd[:10])}...")
result = subprocess.run(cmd)

# 复制额外数据
if os.path.exists(f"dist/{PROJECT_NAME}"):
    print("\n复制额外数据目录...")
    for dir_name in ["3MCWB"]:
        src = os.path.join(os.getcwd(), dir_name)
        dst = os.path.join("dist", PROJECT_NAME, dir_name)
        if os.path.exists(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  复制: {dir_name}")

# 检查结果
print("\n" + "=" * 60)
if os.path.exists(f"dist/{PROJECT_NAME}/{PROJECT_NAME}.exe"):
    print("打包成功!")
    print("=" * 60)
    exe_path = os.path.join("dist", PROJECT_NAME, f"{PROJECT_NAME}.exe")
    size = os.path.getsize(exe_path)
    print(f"可执行文件: {os.path.abspath(exe_path)}")
    print(f"文件大小: {size/1024/1024:.2f} MB")
    
    total_size = 0
    for root, dirs, files in os.walk(f"dist/{PROJECT_NAME}"):
        for f in files:
            total_size += os.path.getsize(os.path.join(root, f))
    print(f"总大小: {total_size/1024/1024:.2f} MB")
else:
    print("打包失败!")
    print("=" * 60)
    sys.exit(1)
