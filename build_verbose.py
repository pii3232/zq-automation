# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import time

print("Starting PyInstaller build...")
print(f"Python: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print()

start_time = time.time()

cmd = [
    sys.executable,
    "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--console",
    "--name", "ZQ-Automation",
    "--hidden-import", "PyQt5",
    "--hidden-import", "PyQt5.QtCore",
    "--hidden-import", "PyQt5.QtGui",
    "--hidden-import", "PyQt5.QtWidgets",
    "--hidden-import", "pyautogui",
    "--hidden-import", "PIL",
    "--hidden-import", "requests",
    "--hidden-import", "config",
    "--hidden-import", "engines",
    "--hidden-import", "database",
    "--hidden-import", "managers",
    "--hidden-import", "tabs",
    "--hidden-import", "handlers",
    "--hidden-import", "discovery_handlers",
    "--hidden-import", "main",
    "run.py"
]

print(f"Command: {' '.join(cmd)}")
print()

# 将输出保存到文件
with open("build_output.txt", "w", encoding="utf-8") as log_file:
    log_file.write(f"Starting build at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    log_file.write(f"Command: {' '.join(cmd)}\n\n")
    log_file.flush()
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=os.getcwd()
    )
    
    # 实时读取输出
    for line in process.stdout:
        print(line, end='')
        log_file.write(line)
        log_file.flush()
    
    process.wait()
    return_code = process.returncode
    
    log_file.write(f"\n\nReturn code: {return_code}\n")
    log_file.write(f"Build finished at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    log_file.write(f"Total time: {time.time() - start_time:.2f} seconds\n")

print(f"\nReturn code: {return_code}")
print(f"Total time: {time.time() - start_time:.2f} seconds")
print(f"Output saved to: build_output.txt")

# 检查输出
if os.path.exists("dist/ZQ-Automation"):
    print("\nBuild successful!")
    print("Output directory: dist/ZQ-Automation")
    exe_path = os.path.join("dist", "ZQ-Automation", "ZQ-Automation.exe")
    if os.path.exists(exe_path):
        size = os.path.getsize(exe_path)
        print(f"Executable: {exe_path}")
        print(f"Size: {size/1024/1024:.2f} MB")
else:
    print("\nBuild failed - dist/ZQ-Automation not found")
    print("Check build_output.txt for details")
