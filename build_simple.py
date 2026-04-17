# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import shutil

print("=" * 60)
print("ZQ-Automation Build Script (Tkinter Version)")
print("=" * 60)

# 清理
print("Cleaning...")
for d in ["build", "dist"]:
    if os.path.exists(d):
        shutil.rmtree(d)
        print(f"  Removed: {d}")

# 删除spec文件
for f in ["main.spec", "ZQ-Automation.spec"]:
    if os.path.exists(f):
        os.remove(f)
        print(f"  Removed: {f}")

print("\nStarting PyInstaller...")
print("This may take several minutes...\n")

# 打包命令 - 排除不需要的模块
cmd = [
    sys.executable,
    "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--console",
    "--name", "ZQ-Automation",
    # 排除不需要的大型模块
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
    "--exclude-module", "sphinx",
    "--exclude-module", "pytest",
    # 隐藏导入
    "--hidden-import", "apscheduler",
    "--hidden-import", "apscheduler.schedulers.background",
    # 数据文件
    "--add-data", f"data{os.pathsep}data",
    "--add-data", f"SERVER{os.pathsep}SERVER",
    # 主脚本
    "main.py"
]

result = subprocess.run(cmd)

print(f"\nReturn code: {result.returncode}")

# 复制额外的数据目录
if os.path.exists("dist/ZQ-Automation"):
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

if os.path.exists("dist/ZQ-Automation/ZQ-Automation.exe"):
    print("\n" + "=" * 60)
    print("BUILD SUCCESSFUL!")
    print("=" * 60)
    exe_path = os.path.join("dist", "ZQ-Automation", "ZQ-Automation.exe")
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
    print("\n" + "=" * 60)
    print("BUILD FAILED")
    print("=" * 60)
    print("Please check the error messages above.")
