#!/bin/bash

# ZQ Automation APK编译脚本
# 在WSL中执行: bash build_apk.sh

set -e

echo "========================================="
echo "ZQ Automation APK 编译脚本"
echo "========================================="

# 设置环境变量
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
export GRADLE_OPTS="-Xmx4096m"
export JAVA_OPTS="-Xmx4096m"

# 进入项目目录
cd ~/android

# 删除旧的虚拟环境
rm -rf buildozer-venv

# 创建虚拟环境
echo "[1/5] 创建Python虚拟环境..."
python3 -m venv buildozer-venv

# 激活虚拟环境
echo "[2/5] 激活虚拟环境..."
source buildozer-venv/bin/activate

# 升级pip
echo "[3/5] 升级pip..."
pip install --upgrade pip setuptools wheel

# 安装Python依赖
echo "[4/5] 安装Python依赖（可能需要几分钟）..."
pip install buildozer kivy opencv-python-headless numpy pyjnius requests pillow

# 编译APK
echo "[5/5] 开始编译APK（首次编译需要30-60分钟）..."
echo "请耐心等待..."
buildozer android debug

# 检查编译结果
if [ -f bin/*.apk ]; then
    echo ""
    echo "========================================="
    echo "编译成功！"
    echo "========================================="
    ls -lh bin/*.apk
    
    # 复制APK到Windows目录
    echo ""
    echo "复制APK到Windows目录..."
    mkdir -p /mnt/e/5-ZDZS-TXA5/android/bin
    cp bin/*.apk /mnt/e/5-ZDZS-TXA5/android/bin/
    echo "完成！APK文件已保存到: E:\\5-ZDZS-TXA5\\android\\bin\\"
else
    echo ""
    echo "========================================="
    echo "编译失败，请检查错误信息"
    echo "========================================="
fi
