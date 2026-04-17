# -*- coding: utf-8 -*-
"""
自动打包脚本 - 完全自动化
"""
import subprocess
import sys
import os
import shutil
import time

VENV_DIR = "venv_build"
PROJECT_NAME = "ZQ-Automation"

def run_cmd(cmd, cwd=None):
    """运行命令并返回结果"""
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def main():
    print("=" * 60)
    print("ZQ-Automation 自动打包脚本")
    print("=" * 60)

    # 步骤1: 创建虚拟环境
    if not os.path.exists(VENV_DIR):
        print("\n[1/5] 创建虚拟环境...")
        subprocess.run([sys.executable, "-m", "venv", VENV_DIR], check=True)
    else:
        print(f"\n[1/5] 虚拟环境已存在: {VENV_DIR}")

    # 获取虚拟环境的Python路径
    venv_python = os.path.join(VENV_DIR, "Scripts", "python.exe")

    # 步骤2: 安装依赖
    print("\n[2/5] 安装依赖...")
    subprocess.run([venv_python, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([venv_python, "-m", "pip", "install", "-r", "requirements_build.txt"], check=True)

    # 步骤3: 测试导入
    print("\n[3/5] 测试导入...")
    test_code = '''
import sys
modules = ['tkinter', 'pyautogui', 'cv2', 'numpy', 'PIL', 'requests', 'apscheduler']
for m in modules:
    try:
        __import__(m)
        print(f"  {m}: OK")
    except ImportError as e:
        print(f"  {m}: FAILED - {e}")
        sys.exit(1)
print("所有依赖测试通过!")
'''
    result = subprocess.run([venv_python, "-c", test_code])
    if result.returncode != 0:
        print("依赖测试失败")
        sys.exit(1)

    # 步骤4: 清理旧文件
    print("\n[4/5] 清理旧文件...")
    for d in ["build", "dist"]:
        if os.path.exists(d):
            for _ in range(3):
                try:
                    shutil.rmtree(d)
                    print(f"  清理: {d}")
                    break
                except PermissionError:
                    print(f"  等待释放: {d}")
                    time.sleep(2)

    for f in ["main.spec", "ZQ-Automation.spec"]:
        if os.path.exists(f):
            os.remove(f)

    # 步骤5: 打包
    print("\n[5/5] 开始打包...")
    cmd = [
        venv_python, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--console",
        "--name", PROJECT_NAME,
        "--exclude-module", "PyQt5",
        "--exclude-module", "PyQt6",
        "--exclude-module", "PySide2",
        "--exclude-module", "PySide6",
        "--exclude-module", "torch",
        "--exclude-module", "tensorflow",
        "--exclude-module", "matplotlib",
        "--exclude-module", "scipy",
        "--exclude-module", "pandas",
        "--hidden-import", "apscheduler",
        "--hidden-import", "apscheduler.schedulers.background",
        "--add-data", f"data{os.pathsep}data",
        "--add-data", f"SERVER{os.pathsep}SERVER",
        "main.py"
    ]
    
    result = subprocess.run(cmd)
    
    # 检查并手动完成 COLLECT
    if not os.path.exists(f"dist/{PROJECT_NAME}/{PROJECT_NAME}.exe"):
        print("\n手动完成 COLLECT 阶段...")
        os.makedirs(f"dist/{PROJECT_NAME}/_internal", exist_ok=True)
        
        # 复制 EXE
        if os.path.exists(f"build/{PROJECT_NAME}/{PROJECT_NAME}.exe"):
            shutil.copy(f"build/{PROJECT_NAME}/{PROJECT_NAME}.exe", f"dist/{PROJECT_NAME}/")
        
        # 复制 _internal 内容
        for item in os.listdir(f"build/{PROJECT_NAME}"):
            if item != f"{PROJECT_NAME}.exe":
                src = os.path.join(f"build/{PROJECT_NAME}", item)
                dst = os.path.join(f"dist/{PROJECT_NAME}/_internal", item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
        
        # 复制数据目录
        for d in ["data", "SERVER", "3MCWB"]:
            if os.path.exists(d):
                dst = os.path.join(f"dist/{PROJECT_NAME}", d)
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(d, dst)
                print(f"  复制: {d}")

    # 检查结果
    print("\n" + "=" * 60)
    exe_path = f"dist/{PROJECT_NAME}/{PROJECT_NAME}.exe"
    if os.path.exists(exe_path):
        print("打包成功!")
        print("=" * 60)
        size = os.path.getsize(exe_path)
        print(f"可执行文件: {os.path.abspath(exe_path)}")
        print(f"文件大小: {size/1024/1024:.2f} MB")
        
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(f"dist/{PROJECT_NAME}"):
            for f in files:
                total_size += os.path.getsize(os.path.join(root, f))
                file_count += 1
        print(f"总大小: {total_size/1024/1024:.2f} MB ({file_count} 文件)")
        
        # 测试运行
        print("\n测试运行...")
        test_result = subprocess.run([exe_path, "--help"], capture_output=True, text=True, timeout=10)
        if test_result.returncode == 0 or "usage" in test_result.stdout.lower() or test_result.returncode == -1:
            print("程序可以启动!")
        else:
            print(f"警告: 程序可能有问题 - {test_result.stderr[:200]}")
    else:
        print("打包失败!")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()
