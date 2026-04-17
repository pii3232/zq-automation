# -*- coding: utf-8 -*-
import subprocess
import sys
import os

print("Starting PyInstaller build...")
print(f"Python: {sys.executable}")
print(f"Working directory: {os.getcwd()}")
print()

cmd = [
    sys.executable,
    "-m", "PyInstaller",
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--name", "ZQ-Automation",
    "run.py"
]

print(f"Command: {' '.join(cmd)}")
print()

try:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
    print("STDOUT:")
    print(result.stdout)
    print("\nSTDERR:")
    print(result.stderr)
    print(f"\nReturn code: {result.returncode}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nChecking output directories...")
for d in ["dist", "build"]:
    if os.path.exists(d):
        print(f"\n{d} directory contents:")
        for root, dirs, files in os.walk(d):
            level = root.replace(d, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f'{subindent}{file}')
    else:
        print(f"{d} directory does NOT exist")
