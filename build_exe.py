# -*- coding: utf-8 -*-
"""
ZQ-全能自动化任务系统 - PyInstaller 打包脚本 (Tkinter版本)
使用方法: python build_exe.py
"""
import os
import sys
import shutil
import subprocess

# 项目配置
PROJECT_NAME = "ZQ-全能自动化任务系统"
PROJECT_VERSION = "2.0.0"
MAIN_SCRIPT = "main.py"
ICON_FILE = "ZQ.bmp"

# 需要包含的数据文件和目录
DATA_FILES = [
    ("data", "data"),
    ("SERVER", "SERVER"),
    ("3MCWB", "3MCWB"),
]

# 需要包含的隐藏导入 (Tkinter版本)
HIDDEN_IMPORTS = [
    "pyautogui",
    "PIL",
    "PIL.Image",
    "requests",
    "json",
    "sqlite3",
    "datetime",
    "pathlib",
    "config",
    "database",
    "engines",
    "handlers",
    "discovery_handlers",
    "managers",
    "tabs",
    "main",
    "cv2",
    "numpy",
    "apscheduler",
    "apscheduler.schedulers.background",
]


def clean_build():
    """清理之前的构建文件"""
    print("=" * 60)
    print("步骤 1: 清理之前的构建文件")
    print("=" * 60)
    
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"  已删除目录: {dir_name}")
            except:
                print(f"  警告: 无法删除 {dir_name}")
    
    # 删除 spec 文件
    for spec_file in [f"{MAIN_SCRIPT.replace('.py', '')}.spec", "ZQ-全能自动化任务系统.spec", "ZQ-Automation.spec"]:
        if os.path.exists(spec_file):
            try:
                os.remove(spec_file)
                print(f"  已删除文件: {spec_file}")
            except:
                pass
    
    print("清理完成\n")


def build_exe():
    """使用 PyInstaller 打包"""
    print("=" * 60)
    print("步骤 2: 执行 PyInstaller 打包")
    print("=" * 60)
    
    # 构建 PyInstaller 命令
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name", PROJECT_NAME,
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
    ]
    
    # 添加图标（如果存在）
    if os.path.exists(ICON_FILE):
        cmd.extend(["--icon", ICON_FILE])
    
    # 添加数据文件
    for src, dst in DATA_FILES:
        if os.path.exists(src):
            cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])
    
    # 添加隐藏导入
    for hidden_import in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", hidden_import])
    
    # 主脚本
    cmd.append(MAIN_SCRIPT)
    
    print(f"执行命令: {' '.join(cmd)}\n")
    
    # 执行打包
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print("\n打包完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n打包失败: {e}")
        return False


def create_portable_version():
    """创建便携版（包含所有依赖的目录）"""
    print("\n" + "=" * 60)
    print("步骤 3: 创建便携版")
    print("=" * 60)
    
    # 构建 PyInstaller 命令（目录模式）
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name", f"{PROJECT_NAME}-便携版",
        "--onedir",
        "--windowed",
        "--clean",
        "--noconfirm",
    ]
    
    # 添加图标
    if os.path.exists(ICON_FILE):
        cmd.extend(["--icon", ICON_FILE])
    
    # 添加数据文件
    for src, dst in DATA_FILES:
        if os.path.exists(src):
            cmd.extend(["--add-data", f"{src}{os.pathsep}{dst}"])
    
    # 添加隐藏导入
    for hidden_import in HIDDEN_IMPORTS:
        cmd.extend(["--hidden-import", hidden_import])
    
    cmd.append(MAIN_SCRIPT)
    
    print(f"执行命令: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print("\n便携版创建完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n便携版创建失败: {e}")
        return False


def show_summary():
    """显示打包摘要"""
    print("\n" + "=" * 60)
    print("打包完成摘要")
    print("=" * 60)
    
    # 单文件版
    single_exe = os.path.join("dist", f"{PROJECT_NAME}.exe")
    if os.path.exists(single_exe):
        size = os.path.getsize(single_exe)
        print(f"\n单文件版:")
        print(f"  路径: {os.path.abspath(single_exe)}")
        print(f"  大小: {size:,} 字节 ({size/1024/1024:.2f} MB)")
    
    # 便携版
    portable_dir = os.path.join("dist", f"{PROJECT_NAME}-便携版")
    if os.path.exists(portable_dir):
        exe_path = os.path.join(portable_dir, f"{PROJECT_NAME}-便携版.exe")
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path)
            print(f"\n便携版:")
            print(f"  路径: {os.path.abspath(portable_dir)}")
            print(f"  主程序: {exe_path}")
            print(f"  大小: {size:,} 字节 ({size/1024/1024:.2f} MB)")
    
    print("\n" + "=" * 60)
    print("使用说明:")
    print(f"  单文件版: 直接运行 dist\\{PROJECT_NAME}.exe")
    print(f"  便携版: 运行 dist\\{PROJECT_NAME}-便携版\\{PROJECT_NAME}-便携版.exe")
    print("=" * 60)


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print(f"  {PROJECT_NAME}")
    print(f"  PyInstaller 打包工具 v{PROJECT_VERSION} (Tkinter)")
    print("=" * 60 + "\n")
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print(f"✓ PyInstaller 已安装 (版本: {PyInstaller.__version__})")
    except ImportError:
        print("✗ 错误: 未安装 PyInstaller")
        print("  请执行: pip install pyinstaller")
        sys.exit(1)
    
    # 清理
    clean_build()
    
    # 打包单文件版
    if build_exe():
        # 创建便携版
        create_portable_version()
        
        # 显示摘要
        show_summary()
        
        print("\n✓ 全部打包完成!")
    else:
        print("\n✗ 打包失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
