# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import time

print("=" * 60)
print("PyInstaller Build Script")
print("=" * 60)
print(f"Python: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 清理旧的构建文件
for d in ["build", "dist"]:
    if os.path.exists(d):
        import shutil
        try:
            shutil.rmtree(d)
            print(f"Cleaned: {d}")
        except Exception as e:
            print(f"Warning: Could not clean {d}: {e}")

print()

cmd = [
    sys.executable,
    "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--console",
    "--name", "ZQ-Automation",
    "run.py"
]

print(f"Command: {' '.join(cmd)}")
print()
print("Starting build...")
print("-" * 60)

# 运行 PyInstaller 并实时输出
process = subprocess.Popen(
    cmd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    cwd=os.getcwd(),
    bufsize=1
)

# 实时读取输出
output_lines = []
for line in iter(process.stdout.readline, ''):
    print(line, end='')
    output_lines.append(line)

process.wait()
return_code = process.returncode

print("-" * 60)
print(f"\nReturn code: {return_code}")
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print()

# 检查输出
print("Checking output directories...")
for d in ["dist", "build"]:
    if os.path.exists(d):
        print(f"\n{d} directory exists:")
        for root, dirs, files in os.walk(d):
            level = root.replace(d, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files[:10]:  # 只显示前10个文件
                print(f'{subindent}{file}')
            if len(files) > 10:
                print(f'{subindent}... and {len(files) - 10} more files')
    else:
        print(f"{d} directory does NOT exist")

# 检查 exe 文件
exe_path = os.path.join("dist", "ZQ-Automation", "ZQ-Automation.exe")
if os.path.exists(exe_path):
    size = os.path.getsize(exe_path)
    print(f"\n✓ Build successful!")
    print(f"Executable: {os.path.abspath(exe_path)}")
    print(f"Size: {size/1024/1024:.2f} MB")
else:
    print(f"\n✗ Build failed - {exe_path} not found")
