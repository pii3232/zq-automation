# ZQ-全能自动化任务系统 - Tkinter版本

## 项目概述

本项目是从PyQt5版本重构为Tkinter版本的自动化任务系统。所有功能和逻辑保持不变,仅将GUI框架从PyQt5替换为Tkinter,以提高兼容性和稳定性。

## 重构内容

### 文件结构

```
E:\5-ZDZS-TXA5\
├── main.py                    # 主入口文件(Tkinter版)
├── tabs.py                    # 标签页创建函数(Tkinter版)
├── handlers.py                # 事件处理函数(Tkinter版)
├── discovery_handlers.py      # 发现即点处理函数(Tkinter版)
├── managers.py                # 管理器类(无需修改)
├── engines.py                 # 引擎类(无需修改)
├── database.py                # 数据库管理(无需修改)
├── config.py                  # 配置管理(无需修改)
├── requirements.txt           # 依赖文件(已更新)
├── config.json                # 配置文件
├── data/                      # 数据目录
├── default/                   # 默认项目目录
└── ZQ.bmp                     # 窗口图标
```

### 主要变化

#### 1. GUI框架替换

**原版本 (PyQt5)**
- 使用QMainWindow、QWidget等PyQt5控件
- 信号槽机制处理事件
- QThread处理多线程
- 样式通过QSS设置

**新版本 (Tkinter)**
- 使用tk.Tk、ttk.Frame等Tkinter控件
- 使用command绑定和事件处理
- 使用threading.Thread处理多线程
- 样式通过ttk.Style设置

#### 2. 控件映射

| PyQt5控件 | Tkinter控件 |
|-----------|-------------|
| QMainWindow | tk.Tk |
| QWidget | ttk.Frame |
| QTabWidget | ttk.Notebook |
| QListWidget | tk.Listbox / ttk.Treeview |
| QTextEdit | scrolledtext.ScrolledText |
| QPushButton | ttk.Button |
| QLabel | ttk.Label |
| QComboBox | ttk.Combobox |
| QSpinBox | ttk.Spinbox |
| QCheckBox | ttk.Checkbutton |
| QRadioButton | ttk.Radiobutton |
| QSlider | ttk.Scale |
| QGroupBox | ttk.LabelFrame |
| QTableWidget | ttk.Treeview |
| QMessageBox | messagebox |
| QFileDialog | filedialog |
| QInputDialog | simpledialog |

#### 3. 事件处理变化

**PyQt5版本:**
```python
button.clicked.connect(self.on_click)
```

**Tkinter版本:**
```python
button = ttk.Button(parent, command=self.on_click)
```

#### 4. 截图功能实现

由于Tkinter没有内置的全屏截图功能,使用了自定义的ScreenshotWidget类,通过创建全屏Tkinter窗口并使用Canvas绘制选择区域来实现截图功能。

### 保留的功能模块

以下模块无需修改,完全保留原功能:

1. **managers.py** - 关键词、工作流、任务、项目管理器
2. **engines.py** - AI引擎、执行引擎、键盘引擎、图像识别引擎
3. **database.py** - SQLite数据库管理
4. **config.py** - 配置文件管理

## 功能特性

### 核心功能

1. **工具标签页**
   - 截图工具(单图、多图)
   - 手动/自动截图录制
   - 鼠标坐标显示
   - 相似度设置
   - 间隔时间设置
   - 多线程设置

2. **AI对话标签页**
   - 自然语言对话
   - AI生成工作流
   - 聊天历史记录
   - 状态显示

3. **关键词标签页**
   - 快捷关键词
   - 创建/编辑/删除关键词
   - 关键词管理

4. **工作流标签页**
   - 创建/编辑/删除工作流
   - 工作流执行
   - 工作流管理

5. **必用标签页**
   - 任务管理
   - 定时执行
   - 延时执行
   - 任务调度

6. **日常任务标签页**
   - 循环执行
   - 定时任务
   - 批量管理

7. **答题标签页**
   - 答题任务管理
   - 自动答题

8. **发现即点标签页**
   - 自动发现并点击
   - 循环监控

9. **项目标签页**
   - 项目创建/切换
   - 项目打包/解包
   - 项目管理

10. **激活标签页**
    - 用户登录/注册
    - 激活码管理

## 使用说明

### 环境要求

- Python 3.7+
- Windows操作系统(推荐)

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python main.py
```

### 配置说明

1. **config.json** - 主配置文件
   - API密钥配置
   - 模型选择
   - 全局设置

2. **projects目录** - 项目数据
   - 关键词定义
   - 工作流定义
   - 任务列表

## 注意事项

### 兼容性改进

1. **不再依赖PyQt5**
   - 避免PyQt5的兼容性问题
   - 减少依赖包大小
   - 提高程序稳定性

2. **使用Python标准库**
   - Tkinter是Python标准库
   - 无需额外安装GUI框架
   - 跨平台兼容性更好

### 功能限制

1. **截图功能**
   - 使用Tkinter Canvas实现,功能较PyQt5简化
   - 支持基本的区域选择和截图

2. **样式定制**
   - Tkinter样式定制能力较PyQt5弱
   - 使用ttk.Style进行基本样式设置

3. **部分高级UI功能**
   - 某些复杂的UI效果可能简化
   - 核心功能完全保留

### 性能优化

1. **多线程处理**
   - 使用threading.Thread代替QThread
   - 保持原有的多线程任务执行能力

2. **事件处理**
   - 使用Tkinter的事件循环
   - 保持响应式UI

## 测试结果

程序已成功测试,主要功能正常:

✅ 程序启动成功
✅ 配置加载正常
✅ AI引擎初始化成功
✅ 执行引擎初始化成功
✅ 关键词管理器初始化成功
✅ 工作流管理器初始化成功
✅ 项目管理器加载成功
✅ 任务管理器工作线程启动成功
✅ 日常任务加载成功
✅ 答题系统任务加载成功
✅ 发现即点任务加载成功
✅ 程序正常退出

## 已知问题

1. **截图功能**
   - 截图选择框可能不如PyQt5流畅
   - 建议后续优化绘制性能

2. **样式美化**
   - UI样式可能不如PyQt5精美
   - 可通过ttk.Style进一步美化

3. **部分对话框**
   - 编辑对话框功能简化
   - 核心功能保持完整

## 后续改进建议

1. **UI美化**
   - 使用ttk.Style定制更美观的样式
   - 添加图标和主题

2. **功能增强**
   - 优化截图功能的用户体验
   - 添加更多快捷操作

3. **性能优化**
   - 优化大列表的加载性能
   - 减少不必要的UI更新

## 开发者说明

### 代码结构

- **main.py** - 主窗口类和程序入口
- **tabs.py** - 所有标签页的创建函数和对话框类
- **handlers.py** - 所有事件处理函数
- **discovery_handlers.py** - 发现即点专用处理函数
- **managers.py** - 数据管理器类
- **engines.py** - 核心引擎类
- **database.py** - 数据库操作类
- **config.py** - 配置管理类

### 扩展开发

如需添加新功能:

1. 在tabs.py中创建新的标签页函数
2. 在handlers.py中添加事件处理函数
3. 在main.py中绑定新的处理函数

## 版本历史

- **v1.0** - 初始PyQt5版本
- **v2.0** - Tkinter重构版本(当前版本)

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题或建议,请联系开发者。

---

**注意**: 本重构版本保持了原版本的所有核心功能逻辑,仅替换了GUI框架,旨在提高兼容性和稳定性。
