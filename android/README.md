# ZQ Automation Android客户端

基于Kivy + Buildozer + Pyjnius框架开发的Android自动化客户端。

## 功能特性

### 1. 指挥标签
- 10个命令模板：调动、走到、预约、集结、集火、攻城、打地、翻红地、铺路、驻守
- 工作组管理：加入/退出工作组、暂断3小时、同步工作组
- 命令执行：自动执行图片识别和点击操作

### 2. 激活功能
- 用户注册和登录
- 激活码激活
- 每日试用（1小时）
- 激活倒计时显示
- 叠加激活支持

### 3. 界面特性
- 单界面设计
- 横竖屏自适应
- 悬窗模式（25DPI圆形按钮）
- 执行日志和状态显示

### 4. 网络连接
- 连接优先级：花生壳直连 > 局域网直连 > 花生壳域名
- 自动重连机制

## 技术架构

- **UI框架**: Kivy (跨平台Python UI)
- **打包工具**: Buildozer
- **Android桥接**: Pyjnius
- **图像识别**: OpenCV
- **截图/点击**: Android Accessibility Service

## 项目结构

```
android/
├── main.py                 # 主程序入口
├── buildozer.spec          # Buildozer配置
├── lib/
│   ├── config.py           # 配置管理
│   ├── android_bridge.py   # Android API桥接
│   ├── image_recognition.py # 图像识别
│   ├── network.py          # 网络管理
│   ├── activation.py       # 激活管理
│   ├── workgroup.py        # 工作组管理
│   └── command_executor.py # 命令执行器
├── ui/
│   ├── command_screen.py   # 指挥标签页
│   ├── activation_screen.py # 激活标签页
│   └── settings_screen.py  # 设置标签页
├── src/
│   ├── java/               # Java源代码
│   │   └── com/zqautomation/
│   │       ├── accessibility/  # 无障碍服务
│   │       └── floatwindow/     # 悬浮窗服务
│   ├── AndroidManifest.xml # Android配置
│   └── res/                # 资源文件
└── data/
    └── command_templates.json # 命令模板配置
```

## 开发环境

### 依赖安装

```bash
# 安装Buildozer
pip install buildozer

# 初始化Buildozer
cd android
buildozer init
```

### 编译APK

```bash
# 调试版
buildozer android debug

# 发布版
buildozer android release
```

### 运行测试

```bash
# 在连接的Android设备上运行
buildozer android debug deploy run
```

## 权限说明

应用需要以下权限：

1. **无障碍服务** (Accessibility Service)
   - 用于执行模拟点击、滑动、文本输入
   - 需要用户在系统设置中手动开启

2. **悬浮窗权限** (SYSTEM_ALERT_WINDOW)
   - 用于显示悬浮控制按钮
   - 需要用户授权

3. **存储权限** (READ/WRITE_EXTERNAL_STORAGE)
   - 用于保存截图、日志、配置文件

4. **网络权限** (INTERNET)
   - 用于与服务器通信

5. **相机权限** (CAMERA)
   - 用于截图功能

## 首次运行

首次运行应用时，会显示权限引导页面：

1. 引导开启无障碍服务
2. 引导授权悬浮窗权限
3. 引导授权存储权限
4. 引导授权相机权限

## 使用说明

### 1. 激活
- 首次使用需要注册账号
- 输入激活码激活
- 或使用每日试用功能

### 2. 加入工作组
- 在设置页面输入工作组ID
- 点击"加入工作组"
- 同步工作组数据

### 3. 执行命令
- 在指挥标签页选择命令模板
- 输入坐标参数（如需要）
- 点击执行按钮
- 查看执行日志

### 4. 悬窗模式
- 点击开启悬窗模式
- 屏幕显示悬浮按钮
- 拖动按钮可移动位置
- 点击按钮执行当前命令

## 配置说明

### buildozer.spec 关键配置

```ini
# 应用名称
title = ZQ Automation

# 包名
package.name = zqautomation

# Android权限
android.permissions = INTERNET,CAMERA,SYSTEM_ALERT_WINDOW,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# 最低API版本
android.minapi = 21

# 目标API版本
android.api = 31

# 包含的Python模块
requirements = python3,kivy,opencv,numpy,pyjnius,requests
```

## 注意事项

1. **Android版本**: 需要Android 5.0 (API 21)及以上

2. **无障碍服务**: 必须在系统设置中手动开启，无法通过代码自动开启

3. **截图功能**: 需要Android 5.0以上的MediaProjection API，首次截图会请求用户授权

4. **存储路径**: 数据存储在外部存储的 `Android/data/com.zqautomation/files/` 目录

5. **横竖屏**: 应用支持横竖屏自动切换，界面会自动调整布局

## 常见问题

### Q: 无障碍服务无法开启？
A: 请在系统设置 > 无障碍 > ZQ Automation 中手动开启

### Q: 悬浮窗不显示？
A: 请在系统设置 > 应用 > ZQ Automation > 权限 中授权悬浮窗权限

### Q: 截图失败？
A: 首次截图会弹出授权请求，请点击"允许"

### Q: 无法连接服务器？
A: 检查网络连接，确认服务器地址配置正确

## 更新日志

### v1.0.0 (2026-04-16)
- 初始版本
- 实现10个命令模板
- 实现工作组功能
- 实现激活功能
- 实现悬窗模式
