# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import shutil

print("=" * 60)
print("ZQ-Automation Build Script (Tkinter Version)")
print("=" * 60)
print(f"Python: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print()

# 清理旧构建文件
print("Cleaning old build files...")
for d in ["dist/ZQ-Automation", "build/ZQ-Automation"]:
    if os.path.exists(d):
        try:
            shutil.rmtree(d)
            print(f"  Removed: {d}")
        except Exception as e:
            print(f"  Warning: Could not remove {d}: {e}")

# 删除旧的 spec 文件
spec_file = "ZQ-Automation.spec"
if os.path.exists(spec_file):
    os.remove(spec_file)
    print(f"  Removed: {spec_file}")

print()

cmd = [
    sys.executable,
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onedir",
    "--console",
    "--name", "ZQ-Automation",
    # 核心模块
    "--hidden-import", "pyautogui",
    "--hidden-import", "PIL",
    "--hidden-import", "PIL.Image",
    "--hidden-import", "requests",
    # 项目模块
    "--hidden-import", "config",
    "--hidden-import", "engines",
    "--hidden-import", "database",
    "--hidden-import", "managers",
    "--hidden-import", "tabs",
    "--hidden-import", "handlers",
    "--hidden-import", "discovery_handlers",
    "--hidden-import", "main",
    # 额外依赖
    "--hidden-import", "cv2",
    "--hidden-import", "numpy",
    "--hidden-import", "apscheduler",
    "--hidden-import", "apscheduler.schedulers.background",
    # 数据文件
    "--add-data", f"data{os.pathsep}data",
    "--add-data", f"SERVER{os.pathsep}SERVER",
    "main.py"
]

print(f"Command: {' '.join(cmd)}")
print()
print("Starting build...")
print("-" * 60)

result = subprocess.run(cmd, cwd=os.getcwd())

print("-" * 60)
print(f"\nReturn code: {result.returncode}")

# 复制额外的数据目录
print("\nCopying additional data directories...")
extra_dirs = ["3MCWB"]
for dir_name in extra_dirs:
    src_dir = os.path.join(os.getcwd(), dir_name)
    dst_dir = os.path.join("dist", "ZQ-Automation", dir_name)
    if os.path.exists(src_dir):
        try:
            if os.path.exists(dst_dir):
                shutil.rmtree(dst_dir)
            shutil.copytree(src_dir, dst_dir)
            print(f"  Copied: {dir_name}")
        except Exception as e:
            print(f"  Warning: Could not copy {dir_name}: {e}")

# 检查结果
print()
if os.path.exists("dist/ZQ-Automation"):
    print("=" * 60)
    print("BUILD SUCCESSFUL!")
    print("=" * 60)
    exe_path = os.path.join("dist", "ZQ-Automation", "ZQ-Automation.exe")
    if os.path.exists(exe_path):
        size = os.path.getsize(exe_path)
        print(f"Executable: {os.path.abspath(exe_path)}")
        print(f"Size: {size/1024/1024:.2f} MB")
    
    # 计算总大小
    total_size = 0
    for root, dirs, files in os.walk("dist/ZQ-Automation"):
        for f in files:
            total_size += os.path.getsize(os.path.join(root, f))
    print(f"Total size: {total_size/1024/1024:.2f} MB")
else:
    print("=" * 60)
    print("BUILD FAILED - dist/ZQ-Automation not found")
    print("=" * 60)
