"""AutoZS - 标签页实现 - Tkinter版本"""
import os
import json
import copy
import pyautogui
import requests
import base64
import datetime
from typing import Dict, Optional

# 使用Tkinter
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, scrolledtext
from tkinter import font as tkfont


# 辅助函数
def msg_warning(parent, title, text):
    """显示警告消息框"""
    messagebox.showwarning(title, text, parent=parent.root if hasattr(parent, 'root') else parent)


def msg_information(parent, title, text):
    """显示信息消息框"""
    messagebox.showinfo(title, text, parent=parent.root if hasattr(parent, 'root') else parent)


def msg_critical(parent, title, text):
    """显示错误消息框"""
    messagebox.showerror(title, text, parent=parent.root if hasattr(parent, 'root') else parent)


def msg_question(parent, title, text):
    """显示询问消息框"""
    return messagebox.askyesno(title, text, parent=parent.root if hasattr(parent, 'root') else parent)


# 工具标签页
def create_tools_tab(self):
    """创建工具标签页"""
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text='工具')
    
    # 截图工具组
    screenshot_frame = ttk.LabelFrame(tab, text='截图工具')
    screenshot_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 截图按钮
    btn_frame = ttk.Frame(screenshot_frame)
    btn_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Button(btn_frame, text='截图', command=self.take_screenshot).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='多图截图', command=self.start_multi_screenshot).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='手动截图录制', command=self.start_manual_record).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='自动截图录制', command=self.start_auto_record).pack(side=tk.LEFT, padx=5)
    
    self.stop_record_button = ttk.Button(btn_frame, text='停止录制', command=self.on_right_click_in_record, state=tk.DISABLED)
    self.stop_record_button.pack(side=tk.LEFT, padx=5)
    
    ttk.Button(btn_frame, text='保存为工作流', command=self.save_record_as_workflow).pack(side=tk.LEFT, padx=5)
    
    # 多图截图标签
    self.multi_screenshot_label = ttk.Label(screenshot_frame, text='')
    self.multi_screenshot_label.pack(fill=tk.X, padx=5, pady=2)
    
    # 截图显示区 - 固定高度
    screenshot_display_frame = tk.Frame(screenshot_frame, height=200, relief=tk.GROOVE, bd=2)
    screenshot_display_frame.pack(fill=tk.X, padx=5, pady=5)
    screenshot_display_frame.pack_propagate(False)
    
    self.tools_screenshot_label = tk.Label(screenshot_display_frame, text='暂无截图', bg='#2d2d2d')
    self.tools_screenshot_label.pack(fill=tk.BOTH, expand=True)
    
    # 设置组
    settings_frame = ttk.LabelFrame(tab, text='设置')
    settings_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 显示鼠标坐标
    coord_frame = ttk.Frame(settings_frame)
    coord_frame.pack(fill=tk.X, padx=5, pady=2)
    
    self.mouse_coord_var = tk.BooleanVar(value=self.show_mouse_coordinates)
    ttk.Checkbutton(coord_frame, text='显示鼠标坐标', variable=self.mouse_coord_var, 
                   command=self.on_mouse_coord_changed).pack(side=tk.LEFT, padx=5)
    
    # 鼠标坐标显示标签
    self.mouse_coord_label = ttk.Label(coord_frame, text='当前坐标: (0, 0)', foreground='blue')
    self.mouse_coord_label.pack(side=tk.LEFT, padx=20)
    
    # 模型选择
    self.model_var = tk.StringVar(value='local' if getattr(self.config, 'load_multimodal_model', False) else 'api')
    ttk.Radiobutton(coord_frame, text='加载本地多模态大模型', variable=self.model_var, 
                   value='local', command=self.on_model_selection_changed).pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(coord_frame, text='OpenAI调用API', variable=self.model_var, 
                   value='api', command=self.on_model_selection_changed).pack(side=tk.LEFT, padx=5)
    
    self.api_settings_button = ttk.Button(coord_frame, text='API设置', command=self.on_api_settings_clicked)
    if self.model_var.get() == 'api':
        self.api_settings_button.pack(side=tk.LEFT, padx=5)
    
    # 间隔时间和线程数
    interval_frame = ttk.Frame(settings_frame)
    interval_frame.pack(fill=tk.X, padx=5, pady=2)
    
    ttk.Label(interval_frame, text='间隔时间(ms):').pack(side=tk.LEFT, padx=5)
    self.interval_var = tk.IntVar(value=getattr(self.config, 'global_interval', 100))
    self.interval_spin = ttk.Spinbox(interval_frame, from_=0, to=5000, textvariable=self.interval_var, 
                                     width=8, command=self.on_interval_changed)
    self.interval_spin.pack(side=tk.LEFT, padx=5)
    
    ttk.Label(interval_frame, text='多线程:').pack(side=tk.LEFT, padx=5)
    self.thread_var = tk.IntVar(value=getattr(self.config, 'task_thread_count', 3))
    self.thread_spin = ttk.Spinbox(interval_frame, from_=1, to=10, textvariable=self.thread_var,
                                   width=5, command=self.on_thread_count_changed)
    self.thread_spin.pack(side=tk.LEFT, padx=5)
    
    # 相似度
    similarity_frame = ttk.Frame(settings_frame)
    similarity_frame.pack(fill=tk.X, padx=5, pady=2)
    
    ttk.Label(similarity_frame, text='找图相似度:').pack(side=tk.LEFT, padx=5)
    self.similarity_var = tk.IntVar(value=self.config.global_similarity)
    self.similarity_scale = ttk.Scale(similarity_frame, from_=50, to=100, variable=self.similarity_var,
                                      orient=tk.HORIZONTAL, command=self.on_similarity_changed)
    self.similarity_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    self.similarity_label = ttk.Label(similarity_frame, text=f'{self.config.global_similarity}%')
    self.similarity_label.pack(side=tk.LEFT, padx=5)
    
    # 录制组
    record_frame = ttk.LabelFrame(tab, text='录制')
    record_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 点击录制按钮
    click_frame = ttk.Frame(record_frame)
    click_frame.pack(fill=tk.X, padx=5, pady=2)
    
    ttk.Button(click_frame, text='左击', command=self.start_left_click_record).pack(side=tk.LEFT, padx=5)
    ttk.Button(click_frame, text='双击', command=self.start_double_click_record).pack(side=tk.LEFT, padx=5)
    ttk.Button(click_frame, text='右击', command=self.start_right_click_record).pack(side=tk.LEFT, padx=5)
    
    # 长时间录制
    long_frame = ttk.Frame(record_frame)
    long_frame.pack(fill=tk.X, padx=5, pady=2)
    
    self.long_record_button = ttk.Button(long_frame, text='长时间记录操作', command=self.start_long_recording)
    self.long_record_button.pack(side=tk.LEFT, padx=5)
    
    self.stop_long_record_button = ttk.Button(long_frame, text='停止记录', command=self.stop_long_recording, 
                                              state=tk.DISABLED)
    self.stop_long_record_button.pack(side=tk.LEFT, padx=5)
    
    # 测试点击
    ttk.Button(long_frame, text='测试点击功能', command=self.test_mouse_click).pack(side=tk.LEFT, padx=5)
    
    # 录制状态标签
    self.record_status_label = ttk.Label(record_frame, text='录制状态:未录制', foreground='gray')
    self.record_status_label.pack(fill=tk.X, padx=5, pady=2)
    
    # 操作记录组
    record_manage_frame = ttk.LabelFrame(tab, text='操作记录')
    record_manage_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 记录管理按钮
    record_btn_frame = ttk.Frame(record_manage_frame)
    record_btn_frame.pack(fill=tk.X, padx=5, pady=2)
    
    ttk.Button(record_btn_frame, text='编辑记录', command=self.edit_record).pack(side=tk.LEFT, padx=5)
    ttk.Button(record_btn_frame, text='删除记录', command=self.delete_record).pack(side=tk.LEFT, padx=5)
    
    # 记录列表
    self.record_list = tk.Listbox(record_manage_frame)
    self.record_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    self.record_list.bind('<Double-Button-1>', lambda e: self.execute_record())
    self.load_records()


# 关键词标签页
def create_keywords_tab(self):
    """创建关键词标签页"""
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text='关键词')
    
    # 快捷关键词
    quick_frame = ttk.LabelFrame(tab, text='快捷关键词')
    quick_frame.pack(fill=tk.X, padx=5, pady=5)
    
    quick_keywords = ['发现', '查找', '点击', '双击', '拖到', '滑动']
    for i, kw in enumerate(quick_keywords):
        if i % 3 == 0:
            btn_row = ttk.Frame(quick_frame)
            btn_row.pack(fill=tk.X, padx=5, pady=2)
        ttk.Button(btn_row, text=kw, command=lambda k=kw: self.insert_keyword(k)).pack(side=tk.LEFT, padx=5)
    
    # 关键词管理
    manage_frame = ttk.LabelFrame(tab, text='关键词管理')
    manage_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 管理按钮
    btn_frame = ttk.Frame(manage_frame)
    btn_frame.pack(fill=tk.X, padx=5, pady=2)
    
    ttk.Button(btn_frame, text='创建关键词', command=self.create_keyword).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='编辑关键词', command=self.edit_keyword).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='删除关键词', command=self.delete_keyword).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='复制关键词', command=self.copy_keyword).pack(side=tk.LEFT, padx=5)
    
    # 关键词列表
    self.keyword_list = tk.Listbox(manage_frame)
    self.keyword_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    self.keyword_list.bind('<Double-Button-1>', lambda e: self.use_keyword())
    self.load_keywords()


# 工作流标签页
def create_workflows_tab(self):
    """创建工作流标签页"""
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text='工作流')
    
    # 管理按钮
    btn_frame = ttk.Frame(tab)
    btn_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Button(btn_frame, text='创建工作流', command=self.create_workflow).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='编辑工作流', command=self.edit_workflow).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='删除工作流', command=self.delete_workflow).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='复制工作流', command=self.copy_workflow).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='清空全部工作流', command=self.clear_all_workflows).pack(side=tk.LEFT, padx=5)
    
    # 工作流表格
    columns = ('状态', '工作流名称', '步骤数')
    self.workflow_table = ttk.Treeview(tab, columns=columns, show='headings', height=20)
    
    for col in columns:
        self.workflow_table.heading(col, text=col)
        self.workflow_table.column(col, width=100)
    
    self.workflow_table.column('状态', width=200)
    self.workflow_table.column('工作流名称', width=300)
    
    # 添加滚动条
    scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.workflow_table.yview)
    self.workflow_table.configure(yscrollcommand=scrollbar.set)
    
    self.workflow_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
    
    self.workflow_table.bind('<Double-1>', lambda e: self.execute_workflow())
    self.load_workflows()


# 任务标签页
def create_tasks_tab(self):
    """创建任务标签页"""
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text='必用')
    
    # 任务管理
    task_frame = ttk.LabelFrame(tab, text='工作流任务')
    task_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 管理按钮
    btn_frame1 = ttk.Frame(task_frame)
    btn_frame1.pack(fill=tk.X, padx=5, pady=2)
    
    ttk.Button(btn_frame1, text='添加任务', command=self.add_task).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame1, text='编辑任务', command=self.edit_task).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame1, text='删除任务', command=self.delete_task).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame1, text='暂停/继续', command=self.toggle_task_pause).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame1, text='立即执行', command=lambda: self.execute_task_now()).pack(side=tk.LEFT, padx=5)
    
    btn_frame2 = ttk.Frame(task_frame)
    btn_frame2.pack(fill=tk.X, padx=5, pady=2)
    
    ttk.Button(btn_frame2, text='保存任务列表', command=self.save_tasks_to_file).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame2, text='加载任务列表', command=self.load_tasks_from_file).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame2, text='清空全部任务', command=self.clear_all_tasks).pack(side=tk.LEFT, padx=5)
    
    # 任务列表
    self.task_list = tk.Listbox(task_frame)
    self.task_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    self.task_list.bind('<Double-Button-1>', lambda e: self.execute_task_now())
    self.load_tasks_list()


# ==================== 指挥标签页 ====================

# 内置命令模板定义
BUILTIN_COMMAND_TEMPLATES = {
    "调动": {
        "type": "python_script",
        "description": "调动：执行调动操作",
        "has_multi_coords": True,
        "has_auto_input": True,
        "is_python_template": True,
        "python_code": """import os
import time
import pyautogui
import numpy as np
import cv2
import sys

# 强制刷新输出
def p(msg):
    print(msg, flush=True)

p("="*50)
p("【打地模块】开始执行")
p("="*50)

workgroup_id = '{{workgroup_id}}'
coord_params = '{{coord_params}}'

# 图片目录：优先工作组同步目录，其次项目默认图片目录
primary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'workgroups', workgroup_id)
secondary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'pic')

p(f"[DEBUG] workgroup_id={workgroup_id}")
p(f"[DEBUG] primary_pic_dir={primary_pic_dir}")
p(f"[DEBUG] secondary_pic_dir={secondary_pic_dir}")
p(f"[DEBUG] coord_params={coord_params}")

# 多次找图函数：返回坐标，不点击
def multi_find_image(image_name):
    \"""
    多次找图：
    - 第1次: 相似度0.9
    - 第2次: 相似度0.8
    - 第3次: 相似度0.7
    返回: (found, x, y) 或 (False, None, None)
    \"""
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    path2 = os.path.join(secondary_pic_dir, image_name)
    
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    
    thresholds = [0.9, 0.8, 0.7]
    template = None
    if image_path:
        template = cv2.imread(image_path)
        if template is None:
            p(f'[图片查找] 无法读取图片文件: {image_path}')
    
    for i, threshold in enumerate(thresholds):
        p(f'[多次找图] 第{i+1}次查找 {image_name}，相似度阈值: {threshold}')
        
        if not image_path:
            p(f'[多次找图] 图片文件不存在')
            p(f'[多次找图] 查找路径1: {path1}')
            p(f'[多次找图] 查找路径2: {path2}')
        elif template is None:
            p(f'[多次找图] 图片文件无法读取')
        else:
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            p(f'[多次找图] 相似度: {max_val:.3f}')
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                p(f'[多次找图] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
                return True, center_x, center_y
            else:
                p(f'[多次找图] 相似度 {max_val:.3f} < 阈值 {threshold}，未找到')
        
        if i < 2:
            p(f'[多次找图] 等待1秒后进行下一次查找...')
            time.sleep(1)
    
    p(f'[多次找图] 3次查找均未找到 {image_name}')
    return False, None, None

# 找图函数（固定相似度0.8）：返回坐标，不点击
def find_image(image_name):
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        path2 = os.path.join(secondary_pic_dir, image_name)
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    if not image_path:
        p(f"[图片查找] 未找到图片文件: {image_name}")
        return False, None, None
    p(f'[图片查找] 查找图片: {image_name}')
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    template = cv2.imread(image_path)
    if template is None:
        p(f'[图片查找] 无法读取图片: {image_name}')
        return False, None, None
    result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        p(f'[图片查找] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
        return True, center_x, center_y
    else:
        p(f'[图片查找] 未找到图片 {image_name}，相似度: {max_val:.3f}')
        return False, None, None

# ==================== 执行流程 ====================

# 2.1 如果找到1-TC2.png，点击，等待2秒
found, x, y = find_image('1-TC2.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.1] 点击1-TC2.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

# 2.2 等待1秒
time.sleep(1)

# 2.3 如果找到1-TC1.png，点击，等待2秒
found, x, y = find_image('1-TC1.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.3] 点击1-TC1.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

# 2.4 等待1秒
time.sleep(1)

# 2.5 如果找到1-CC.png，点击，等待4秒
found, x, y = find_image('1-CC.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.5] 点击1-CC.png坐标: ({x}, {y})，等待4秒')
    time.sleep(4)

# 2.6 等待1秒
time.sleep(1)

# 2.7.1 多次找图1-ST.png
found, st_x, st_y = multi_find_image('1-ST.png')

if found:
    p(f"[2.7.1] 多次找图找到1-ST.png，坐标: ({st_x}, {st_y})")
    
    # 点击该坐标5次，每次等待1秒
    for i in range(5):
        pyautogui.click(st_x, st_y)
        p(f'[2.7.1] 第{i+1}次点击坐标: ({st_x}, {st_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.3 多次找图1-DW.png，点击坐标偏移X+100
    found_dw, dw_x, dw_y = multi_find_image('1-DW.png')
    if found_dw:
        offset_x = dw_x + 100
        offset_y = dw_y
        pyautogui.click(offset_x, offset_y)
        p(f'[2.7.3] 找到1-DW.png，点击偏移坐标: ({offset_x}, {offset_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.4 等待1秒
    p('[2.7.4] 等待1秒')
    time.sleep(1)
    
    # 2.7.5-2.7.9 键盘输入文本参数
    p(f'[2.7.5] 键盘输入文本参数: {coord_params}')
    from pynput.keyboard import Controller
    kb = Controller()
    kb.type(coord_params)
    p('[2.7.8] 输入完成')
    time.sleep(1)
    
    # 2.7.10 多次找图1-QD.png
    found_qd, qd_x, qd_y = multi_find_image('1-QD.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击1-QD.png坐标: ({qd_x}, {qd_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图1-QW.png
    found_qw, qw_x, qw_y = multi_find_image('1-QW.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击1-QW.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.13 等待1秒
    p('[2.7.13] 等待1秒')
    time.sleep(1)
    
    # 2.7.13.1 点击画面中心坐标(1920x1080画面，起始位置0,52，中心960,592)
    pyautogui.click(960, 592)
    p('[2.7.13.1] 点击画面中心坐标: (960, 592)，等待1秒')
    time.sleep(1)
    
    # 2.7.14 多次找图1-DD.png
    found_gz, gz_x, gz_y = multi_find_image('1-DD.png')
    if found_gz:
        pyautogui.click(gz_x, gz_y)
        p(f'[2.7.14] 点击1-DD.png坐标: ({gz_x}, {gz_y})，等待2秒')
        time.sleep(2)
    
    # 2.7.16 等待1秒
    p('[2.7.16] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    p('[打地模块] 条件成立分支执行完成')
else:
    p('[2.7.1] 多次找图未找到1-ST.png，跳过后续操作，模板执行结束')

p("="*50)
p("【打地模块】执行完成!")
p("="*50)""",
        "template": {
            "coords": [
                {"x": 0, "y": 0, "label": "坐标1"}
            ],
            "auto_input": "",
            "params": []
        }
    },
    "走到": {
        "type": "python_script",
        "description": "走到：执行走到操作",
        "has_multi_coords": True,
        "has_auto_input": True,
        "is_python_template": True,
        "python_code": """import os
import time
import pyautogui
import numpy as np
import cv2

print("="*50)
print("【走到模块】开始执行")
print("="*50)

workgroup_id = '{{workgroup_id}}'
coord_params = '{{coord_params}}'

# 图片目录：优先工作组同步目录(3MCWB/workgroups/2)，其次项目默认图片目录(3MCWB/pic)
primary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'workgroups', workgroup_id)
secondary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'pic')

print(f"[DEBUG] workgroup_id={workgroup_id}")
print(f"[DEBUG] primary_pic_dir={primary_pic_dir}")
print(f"[DEBUG] secondary_pic_dir={secondary_pic_dir}")
print(f"[DEBUG] coord_params={coord_params}")

# 多次找图函数：进行3次找图，相似度依次降低
def multi_find_image_click(image_name):
    \"""
    多次找图：
    - 第1次: 相似度0.9
    - 第2次: 相似度0.8
    - 第3次: 相似度0.7
    返回: (found, x, y) 或 (False, None, None)
    \"""
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    if os.path.exists(path1):
        image_path = path1
        print(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        path2 = os.path.join(secondary_pic_dir, image_name)
        if os.path.exists(path2):
            image_path = path2
            print(f"[图片查找] 找到文件(默认): {path2}")
    if not image_path:
        print(f"[图片查找] 未找到图片文件: {image_name}")
        return False, None, None
    
    template = cv2.imread(image_path)
    if template is None:
        print(f'[图片查找] 无法读取图片: {image_name}')
        return False, None, None
    
    thresholds = [0.9, 0.8, 0.7]
    for i, threshold in enumerate(thresholds):
        print(f'[多次找图] 第{i+1}次查找 {image_name}，相似度阈值: {threshold}')
        screenshot = pyautogui.screenshot()
        screen_np = np.array(screenshot)
        screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
        result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        print(f'[多次找图] 相似度: {max_val:.3f}')
        if max_val >= threshold:
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            print(f'[多次找图] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
            return True, center_x, center_y
        if i < 2:  # 不是最后一次，等待1秒再试
            print(f'[多次找图] 未找到，等待1秒后重试...')
            time.sleep(1)
    print(f'[多次找图] 3次查找均未找到 {image_name}')
    return False, None, None

# 找图并点击函数（固定相似度0.8）
def find_image_click(image_name, wait_time=1):
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    if os.path.exists(path1):
        image_path = path1
        print(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        path2 = os.path.join(secondary_pic_dir, image_name)
        if os.path.exists(path2):
            image_path = path2
            print(f"[图片查找] 找到文件(默认): {path2}")
    if not image_path:
        print(f"[图片查找] 未找到图片文件: {image_name}")
        return False, None, None
    print(f'[图片查找] 查找图片: {image_name}')
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    template = cv2.imread(image_path)
    if template is None:
        print(f'[图片查找] 无法读取图片: {image_name}')
        return False, None, None
    result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        print(f'[图片查找] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
        pyautogui.click(center_x, center_y)
        print(f'[图片查找] 点击坐标: ({center_x}, {center_y})')
        if wait_time > 0:
            print(f'[图片查找] 等待 {wait_time} 秒...')
            time.sleep(wait_time)
        return True, center_x, center_y
    else:
        print(f'[图片查找] 未找到图片 {image_name}，相似度: {max_val:.3f}')
        return False, None, None

# ==================== 执行流程 ====================

# 2.1 如果找到1-TC2.png，点击，等待2秒
found, x, y = find_image_click('1-TC2.png', 2)

# 2.2 等待1秒
time.sleep(1)

# 2.3 如果找到1-TC1.png，点击，等待2秒
found, x, y = find_image_click('1-TC1.png', 2)

# 2.4 等待1秒
time.sleep(1)

# 2.5 如果找到1-CC.png，点击，等待4秒
found, x, y = find_image_click('1-CC.png', 4)

# 2.6 等待1秒
time.sleep(1)

# 2.7.1 多次找图1-ST.png
found, st_x, st_y = multi_find_image_click('1-ST.png')

if found:
    print("[2.7.1] 多次找图找到1-ST.png，执行后续操作")
    # 点击找到的坐标，等待2秒
    pyautogui.click(st_x, st_y)
    print(f'[2.7.1] 点击坐标: ({st_x}, {st_y})')
    time.sleep(2)
    
    # 2.7.2 等待1秒
    time.sleep(1)
    
    # 2.7.3 多次找图1-ST.png，点击坐标偏移X+100
    found2, st2_x, st2_y = multi_find_image_click('1-ST.png')
    if found2:
        offset_x = st2_x + 100
        offset_y = st2_y
        pyautogui.click(offset_x, offset_y)
        print(f'[2.7.3] 点击偏移坐标: ({offset_x}, {offset_y})')
        time.sleep(1)
    
    # 2.7.4 等待1秒
    time.sleep(1)
    
    # 2.7.5-2.7.9 键盘输入文本参数
    print(f"[键盘输入] 使用pynput.keyboard输入文本参数: {coord_params}")
    from pynput.keyboard import Controller
    kb = Controller()
    kb.type(coord_params)
    time.sleep(1)
    
    # 2.7.10 多次找图1-QD.png
    found_qd, qd_x, qd_y = multi_find_image_click('1-QD.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        print(f'[2.7.10] 点击1-QD.png坐标: ({qd_x}, {qd_y})')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    time.sleep(1)
    
    # 2.7.12 多次找图1-QW.png
    found_qw, qw_x, qw_y = multi_find_image_click('1-QW.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        print(f'[2.7.12] 点击1-QW.png坐标: ({qw_x}, {qw_y})')
        time.sleep(1)
    
    
    # 2.7.13 等待1秒
    time.sleep(1)
    
    # 2.7.14 多次找图2-XJ.png
    found_gz, gz_x, gz_y = multi_find_image_click('2-XJ.png')
    if found_gz:
        pyautogui.click(gz_x, gz_y)
        print(f'[2.7.14] 点击2-XJ.png坐标: ({gz_x}, {gz_y})')
        time.sleep(1)
    
  
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image_click('1-YJBB.png', 1)
    
    # 2.7.18 等待1秒
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image_click('1-CZ.png', 1)
    
    # 2.7.20 等待1秒
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image_click('9-QD.png', 1)
    
    # 2.7.18 等待1秒
    time.sleep(1)
    
    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image_click('1-CZ.png', 1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image_click('9-QD.png', 1)
    
    # 2.7.18 等待1秒
    time.sleep(1)
    
    print("[走到模块] 条件成立分支执行完成")
else:
    print("[2.7.1] 多次找图未找到1-ST.png，跳过后续操作，模板执行结束")

print("="*50)
print("【走到模块】执行完成!")
print("="*50)""",
        "template": {
            "coords": [
                {"x": 0, "y": 0, "label": "坐标1"}
            ],
            "auto_input": "",
            "params": []
        }
    },
    "预约": {
        "type": "python_script",
        "description": "预约：执行预约操作",
        "has_multi_coords": True,
        "has_auto_input": True,
        "is_python_template": True,
        "python_code": """import os
import time
import pyautogui
import numpy as np
import cv2
import sys

# 强制刷新输出
def p(msg):
    print(msg, flush=True)

p("="*50)
p("【打地模块】开始执行")
p("="*50)

workgroup_id = '{{workgroup_id}}'
coord_params = '{{coord_params}}'

# 图片目录：优先工作组同步目录，其次项目默认图片目录
primary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'workgroups', workgroup_id)
secondary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'pic')

p(f"[DEBUG] workgroup_id={workgroup_id}")
p(f"[DEBUG] primary_pic_dir={primary_pic_dir}")
p(f"[DEBUG] secondary_pic_dir={secondary_pic_dir}")
p(f"[DEBUG] coord_params={coord_params}")

# 多次找图函数：返回坐标，不点击
def multi_find_image(image_name):
    \"""
    多次找图：
    - 第1次: 相似度0.9
    - 第2次: 相似度0.8
    - 第3次: 相似度0.7
    返回: (found, x, y) 或 (False, None, None)
    \"""
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    path2 = os.path.join(secondary_pic_dir, image_name)
    
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    
    thresholds = [0.9, 0.8, 0.7]
    template = None
    if image_path:
        template = cv2.imread(image_path)
        if template is None:
            p(f'[图片查找] 无法读取图片文件: {image_path}')
    
    for i, threshold in enumerate(thresholds):
        p(f'[多次找图] 第{i+1}次查找 {image_name}，相似度阈值: {threshold}')
        
        if not image_path:
            p(f'[多次找图] 图片文件不存在')
            p(f'[多次找图] 查找路径1: {path1}')
            p(f'[多次找图] 查找路径2: {path2}')
        elif template is None:
            p(f'[多次找图] 图片文件无法读取')
        else:
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            p(f'[多次找图] 相似度: {max_val:.3f}')
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                p(f'[多次找图] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
                return True, center_x, center_y
            else:
                p(f'[多次找图] 相似度 {max_val:.3f} < 阈值 {threshold}，未找到')
        
        if i < 2:
            p(f'[多次找图] 等待1秒后进行下一次查找...')
            time.sleep(1)
    
    p(f'[多次找图] 3次查找均未找到 {image_name}')
    return False, None, None

# 找图函数（固定相似度0.8）：返回坐标，不点击
def find_image(image_name):
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        path2 = os.path.join(secondary_pic_dir, image_name)
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    if not image_path:
        p(f"[图片查找] 未找到图片文件: {image_name}")
        return False, None, None
    p(f'[图片查找] 查找图片: {image_name}')
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    template = cv2.imread(image_path)
    if template is None:
        p(f'[图片查找] 无法读取图片: {image_name}')
        return False, None, None
    result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        p(f'[图片查找] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
        return True, center_x, center_y
    else:
        p(f'[图片查找] 未找到图片 {image_name}，相似度: {max_val:.3f}')
        return False, None, None

# ==================== 执行流程 ====================

    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.10 多次找图4-JJ2.png
    found_qd, qd_x, qd_y = multi_find_image('4-JJ2.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击4-JJ2.png坐标: ({qd_x}, {qd_y})，等待3秒')
        time.sleep(3)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图3-YY.png
    found_qw, qw_x, qw_y = multi_find_image('3-YY.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击3-YY.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
 
    # 2.7.12 多次找图3-YY2.png
    found_qw, qw_x, qw_y = multi_find_image('3-YY2.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击3-YY2.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)

    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
 
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.10 多次找图4-JJ2.png
    found_qd, qd_x, qd_y = multi_find_image('4-JJ2.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击4-JJ2.png坐标: ({qd_x}, {qd_y})，等待3秒')
        time.sleep(3)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图3-YY.png
    found_qw, qw_x, qw_y = multi_find_image('3-YY.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击3-YY.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
 
    # 2.7.12 多次找图3-YY2.png
    found_qw, qw_x, qw_y = multi_find_image('3-YY2.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击3-YY2.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)

    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)

    
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.10 多次找图4-JJ2.png
    found_qd, qd_x, qd_y = multi_find_image('4-JJ2.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击4-JJ2.png坐标: ({qd_x}, {qd_y})，等待3秒')
        time.sleep(3)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图3-YY.png
    found_qw, qw_x, qw_y = multi_find_image('3-YY.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击3-YY.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
 
    # 2.7.12 多次找图3-YY2.png
    found_qw, qw_x, qw_y = multi_find_image('3-YY2.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击3-YY2.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)

    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)

    
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.10 多次找图4-JJ2.png
    found_qd, qd_x, qd_y = multi_find_image('4-JJ2.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击4-JJ2.png坐标: ({qd_x}, {qd_y})，等待3秒')
        time.sleep(3)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图3-YY.png
    found_qw, qw_x, qw_y = multi_find_image('3-YY.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击3-YY.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
 
    # 2.7.12 多次找图3-YY2.png
    found_qw, qw_x, qw_y = multi_find_image('3-YY2.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击3-YY2.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)

    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)

    
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.10 多次找图4-JJ2.png
    found_qd, qd_x, qd_y = multi_find_image('4-JJ2.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击4-JJ2.png坐标: ({qd_x}, {qd_y})，等待3秒')
        time.sleep(3)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图3-YY.png
    found_qw, qw_x, qw_y = multi_find_image('3-YY.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击3-YY.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
 
    # 2.7.12 多次找图3-YY2.png
    found_qw, qw_x, qw_y = multi_find_image('3-YY2.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击3-YY2.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)

    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)

    
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.10 多次找图4-JJ2.png
    found_qd, qd_x, qd_y = multi_find_image('4-JJ2.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击4-JJ2.png坐标: ({qd_x}, {qd_y})，等待3秒')
        time.sleep(3)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图3-YY.png
    found_qw, qw_x, qw_y = multi_find_image('3-YY.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击3-YY.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
 
    # 2.7.12 多次找图3-YY2.png
    found_qw, qw_x, qw_y = multi_find_image('3-YY2.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击3-YY2.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)

    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

p("="*50)
p("【模块】执行完成!")
p("="*50)""",
        "template": {
            "coords": [
                {"x": 0, "y": 0, "label": "坐标1"}
            ],
            "auto_input": "",
            "params": []
        }
    },
    "集结": {
        "type": "python_script",
        "description": "集结：执行集结操作",
        "has_multi_coords": True,
        "has_auto_input": True,
        "is_python_template": True,
        "python_code": """import os
import time
import pyautogui
import numpy as np
import cv2
import sys

# 强制刷新输出
def p(msg):
    print(msg, flush=True)

p("="*50)
p("【打地模块】开始执行")
p("="*50)

workgroup_id = '{{workgroup_id}}'
coord_params = '{{coord_params}}'

# 图片目录：优先工作组同步目录，其次项目默认图片目录
primary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'workgroups', workgroup_id)
secondary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'pic')

p(f"[DEBUG] workgroup_id={workgroup_id}")
p(f"[DEBUG] primary_pic_dir={primary_pic_dir}")
p(f"[DEBUG] secondary_pic_dir={secondary_pic_dir}")
p(f"[DEBUG] coord_params={coord_params}")

# 多次找图函数：返回坐标，不点击
def multi_find_image(image_name):
    \"""
    多次找图：
    - 第1次: 相似度0.9
    - 第2次: 相似度0.8
    - 第3次: 相似度0.7
    返回: (found, x, y) 或 (False, None, None)
    \"""
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    path2 = os.path.join(secondary_pic_dir, image_name)
    
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    
    thresholds = [0.9, 0.8, 0.7]
    template = None
    if image_path:
        template = cv2.imread(image_path)
        if template is None:
            p(f'[图片查找] 无法读取图片文件: {image_path}')
    
    for i, threshold in enumerate(thresholds):
        p(f'[多次找图] 第{i+1}次查找 {image_name}，相似度阈值: {threshold}')
        
        if not image_path:
            p(f'[多次找图] 图片文件不存在')
            p(f'[多次找图] 查找路径1: {path1}')
            p(f'[多次找图] 查找路径2: {path2}')
        elif template is None:
            p(f'[多次找图] 图片文件无法读取')
        else:
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            p(f'[多次找图] 相似度: {max_val:.3f}')
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                p(f'[多次找图] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
                return True, center_x, center_y
            else:
                p(f'[多次找图] 相似度 {max_val:.3f} < 阈值 {threshold}，未找到')
        
        if i < 2:
            p(f'[多次找图] 等待1秒后进行下一次查找...')
            time.sleep(1)
    
    p(f'[多次找图] 3次查找均未找到 {image_name}')
    return False, None, None

# 找图函数（固定相似度0.8）：返回坐标，不点击
def find_image(image_name):
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        path2 = os.path.join(secondary_pic_dir, image_name)
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    if not image_path:
        p(f"[图片查找] 未找到图片文件: {image_name}")
        return False, None, None
    p(f'[图片查找] 查找图片: {image_name}')
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    template = cv2.imread(image_path)
    if template is None:
        p(f'[图片查找] 无法读取图片: {image_name}')
        return False, None, None
    result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        p(f'[图片查找] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
        return True, center_x, center_y
    else:
        p(f'[图片查找] 未找到图片 {image_name}，相似度: {max_val:.3f}')
        return False, None, None

# ==================== 执行流程 ====================

    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.10 多次找图4-JJ2.png
    found_qd, qd_x, qd_y = multi_find_image('4-JJ2.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击4-JJ2.png坐标: ({qd_x}, {qd_y})，等待3秒')
        time.sleep(3)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图4-JJ3.png
    found_qw, qw_x, qw_y = multi_find_image('4-JJ3.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击4-JJ3.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
 
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.10 多次找图4-JJ2.png
    found_qd, qd_x, qd_y = multi_find_image('4-JJ2.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击4-JJ2.png坐标: ({qd_x}, {qd_y})，等待3秒')
        time.sleep(3)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图4-JJ3.png
    found_qw, qw_x, qw_y = multi_find_image('4-JJ3.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击4-JJ3.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
 
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.10 多次找图4-JJ2.png
    found_qd, qd_x, qd_y = multi_find_image('4-JJ2.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击4-JJ2.png坐标: ({qd_x}, {qd_y})，等待3秒')
        time.sleep(3)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图4-JJ3.png
    found_qw, qw_x, qw_y = multi_find_image('4-JJ3.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击4-JJ3.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.10 多次找图4-JJ2.png
    found_qd, qd_x, qd_y = multi_find_image('4-JJ2.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击4-JJ2.png坐标: ({qd_x}, {qd_y})，等待3秒')
        time.sleep(3)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图4-JJ3.png
    found_qw, qw_x, qw_y = multi_find_image('4-JJ3.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击4-JJ3.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
 
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.10 多次找图4-JJ2.png
    found_qd, qd_x, qd_y = multi_find_image('4-JJ2.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击4-JJ2.png坐标: ({qd_x}, {qd_y})，等待3秒')
        time.sleep(3)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图4-JJ3.png
    found_qw, qw_x, qw_y = multi_find_image('4-JJ3.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击4-JJ3.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
 
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.10 多次找图4-JJ2.png
    found_qd, qd_x, qd_y = multi_find_image('4-JJ2.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击4-JJ2.png坐标: ({qd_x}, {qd_y})，等待3秒')
        time.sleep(3)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图4-JJ3.png
    found_qw, qw_x, qw_y = multi_find_image('4-JJ3.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击4-JJ3.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
 
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

p("="*50)
p("【模块】执行完成!")
p("="*50)""",
        "template": {
            "coords": [
                {"x": 0, "y": 0, "label": "坐标1"}
            ],
            "auto_input": "",
            "params": []
        }
    },
    "集火": {
        "type": "python_script",
        "description": "集火：执行集火操作",
        "has_multi_coords": True,
        "has_auto_input": True,
        "is_python_template": True,
        "python_code": """import os
import time
import pyautogui
import numpy as np
import cv2
import sys

# 强制刷新输出
def p(msg):
    print(msg, flush=True)

p("="*50)
p("【打地模块】开始执行")
p("="*50)

workgroup_id = '{{workgroup_id}}'
coord_params = '{{coord_params}}'

# 图片目录：优先工作组同步目录，其次项目默认图片目录
primary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'workgroups', workgroup_id)
secondary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'pic')

p(f"[DEBUG] workgroup_id={workgroup_id}")
p(f"[DEBUG] primary_pic_dir={primary_pic_dir}")
p(f"[DEBUG] secondary_pic_dir={secondary_pic_dir}")
p(f"[DEBUG] coord_params={coord_params}")

# 多次找图函数：返回坐标，不点击
def multi_find_image(image_name):
    \"""
    多次找图：
    - 第1次: 相似度0.9
    - 第2次: 相似度0.8
    - 第3次: 相似度0.7
    返回: (found, x, y) 或 (False, None, None)
    \"""
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    path2 = os.path.join(secondary_pic_dir, image_name)
    
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    
    thresholds = [0.9, 0.8, 0.7]
    template = None
    if image_path:
        template = cv2.imread(image_path)
        if template is None:
            p(f'[图片查找] 无法读取图片文件: {image_path}')
    
    for i, threshold in enumerate(thresholds):
        p(f'[多次找图] 第{i+1}次查找 {image_name}，相似度阈值: {threshold}')
        
        if not image_path:
            p(f'[多次找图] 图片文件不存在')
            p(f'[多次找图] 查找路径1: {path1}')
            p(f'[多次找图] 查找路径2: {path2}')
        elif template is None:
            p(f'[多次找图] 图片文件无法读取')
        else:
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            p(f'[多次找图] 相似度: {max_val:.3f}')
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                p(f'[多次找图] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
                return True, center_x, center_y
            else:
                p(f'[多次找图] 相似度 {max_val:.3f} < 阈值 {threshold}，未找到')
        
        if i < 2:
            p(f'[多次找图] 等待1秒后进行下一次查找...')
            time.sleep(1)
    
    p(f'[多次找图] 3次查找均未找到 {image_name}')
    return False, None, None

# 找图函数（固定相似度0.8）：返回坐标，不点击
def find_image(image_name):
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        path2 = os.path.join(secondary_pic_dir, image_name)
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    if not image_path:
        p(f"[图片查找] 未找到图片文件: {image_name}")
        return False, None, None
    p(f'[图片查找] 查找图片: {image_name}')
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    template = cv2.imread(image_path)
    if template is None:
        p(f'[图片查找] 无法读取图片: {image_name}')
        return False, None, None
    result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        p(f'[图片查找] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
        return True, center_x, center_y
    else:
        p(f'[图片查找] 未找到图片 {image_name}，相似度: {max_val:.3f}')
        return False, None, None

# ==================== 执行流程 ====================

# 2.1 如果找到1-TC2.png，点击，等待2秒
found, x, y = find_image('1-TC2.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.1] 点击1-TC2.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

# 2.2 等待1秒
time.sleep(1)

# 2.3 如果找到1-TC1.png，点击，等待2秒
found, x, y = find_image('1-TC1.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.3] 点击1-TC1.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

# 2.4 等待1秒
time.sleep(1)

# 2.5 如果找到1-CC.png，点击，等待4秒
found, x, y = find_image('1-CC.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.5] 点击1-CC.png坐标: ({x}, {y})，等待4秒')
    time.sleep(4)

# 2.6 等待1秒
time.sleep(1)

# 2.7.1 多次找图1-ST.png
found, st_x, st_y = multi_find_image('1-ST.png')

if found:
    p(f"[2.7.1] 多次找图找到1-ST.png，坐标: ({st_x}, {st_y})")
    
    # 点击该坐标5次，每次等待1秒
    for i in range(5):
        pyautogui.click(st_x, st_y)
        p(f'[2.7.1] 第{i+1}次点击坐标: ({st_x}, {st_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.3 多次找图1-DW.png，点击坐标偏移X+100
    found_dw, dw_x, dw_y = multi_find_image('1-DW.png')
    if found_dw:
        offset_x = dw_x + 100
        offset_y = dw_y
        pyautogui.click(offset_x, offset_y)
        p(f'[2.7.3] 找到1-DW.png，点击偏移坐标: ({offset_x}, {offset_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.4 等待1秒
    p('[2.7.4] 等待1秒')
    time.sleep(1)
    
    # 2.7.5-2.7.9 键盘输入文本参数
    p(f'[2.7.5] 键盘输入文本参数: {coord_params}')
    from pynput.keyboard import Controller
    kb = Controller()
    kb.type(coord_params)
    p('[2.7.8] 输入完成')
    time.sleep(1)
    
    # 2.7.10 多次找图1-QD.png
    found_qd, qd_x, qd_y = multi_find_image('1-QD.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击1-QD.png坐标: ({qd_x}, {qd_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图1-QW.png
    found_qw, qw_x, qw_y = multi_find_image('1-QW.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击1-QW.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.13 等待1秒
    p('[2.7.13] 等待1秒')
    time.sleep(1)
    
    # 2.7.13.1 点击画面中心坐标(1920x1080画面，起始位置0,52，中心960,592)
    pyautogui.click(960, 592)
    p('[2.7.13.1] 点击画面中心坐标: (960, 592)，等待1秒')
    time.sleep(1)
    
    # 2.7.14 多次找图1-GZ.png
    found_gz, gz_x, gz_y = multi_find_image('1-GZ.png')
    if found_gz:
        pyautogui.click(gz_x, gz_y)
        p(f'[2.7.14] 点击1-GZ.png坐标: ({gz_x}, {gz_y})，等待2秒')
        time.sleep(2)
    
    # 2.7.14 多次找图6-gc.png
    found_gz, gz_x, gz_y = multi_find_image('6-gc.png')
    if found_gz:
        pyautogui.click(gz_x, gz_y)
        p(f'[2.7.14] 点击6-gc.png坐标: ({gz_x}, {gz_y})，等待2秒')
        time.sleep(2)
 
    # 2.7.16 等待1秒
    p('[2.7.16] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    p('[打地模块] 条件成立分支执行完成')
else:
    p('[2.7.1] 多次找图未找到1-ST.png，跳过后续操作，模板执行结束')

p("="*50)
p("【打地模块】执行完成!")
p("="*50)""",
        "template": {
            "coords": [
                {"x": 0, "y": 0, "label": "坐标1"}
            ],
            "auto_input": "",
            "params": []
        }
    },
    "攻城": {
        "type": "python_script",
        "description": "攻城：执行攻城操作",
        "has_multi_coords": True,
        "has_auto_input": True,
        "is_python_template": True,
        "python_code": """import os
import time
import pyautogui
import numpy as np
import cv2
import sys

# 强制刷新输出
def p(msg):
    print(msg, flush=True)

p("="*50)
p("【打地模块】开始执行")
p("="*50)

workgroup_id = '{{workgroup_id}}'
coord_params = '{{coord_params}}'

# 图片目录：优先工作组同步目录，其次项目默认图片目录
primary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'workgroups', workgroup_id)
secondary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'pic')

p(f"[DEBUG] workgroup_id={workgroup_id}")
p(f"[DEBUG] primary_pic_dir={primary_pic_dir}")
p(f"[DEBUG] secondary_pic_dir={secondary_pic_dir}")
p(f"[DEBUG] coord_params={coord_params}")

# 多次找图函数：返回坐标，不点击
def multi_find_image(image_name):
    \"""
    多次找图：
    - 第1次: 相似度0.9
    - 第2次: 相似度0.8
    - 第3次: 相似度0.7
    返回: (found, x, y) 或 (False, None, None)
    \"""
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    path2 = os.path.join(secondary_pic_dir, image_name)
    
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    
    thresholds = [0.9, 0.8, 0.7]
    template = None
    if image_path:
        template = cv2.imread(image_path)
        if template is None:
            p(f'[图片查找] 无法读取图片文件: {image_path}')
    
    for i, threshold in enumerate(thresholds):
        p(f'[多次找图] 第{i+1}次查找 {image_name}，相似度阈值: {threshold}')
        
        if not image_path:
            p(f'[多次找图] 图片文件不存在')
            p(f'[多次找图] 查找路径1: {path1}')
            p(f'[多次找图] 查找路径2: {path2}')
        elif template is None:
            p(f'[多次找图] 图片文件无法读取')
        else:
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            p(f'[多次找图] 相似度: {max_val:.3f}')
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                p(f'[多次找图] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
                return True, center_x, center_y
            else:
                p(f'[多次找图] 相似度 {max_val:.3f} < 阈值 {threshold}，未找到')
        
        if i < 2:
            p(f'[多次找图] 等待1秒后进行下一次查找...')
            time.sleep(1)
    
    p(f'[多次找图] 3次查找均未找到 {image_name}')
    return False, None, None

# 找图函数（固定相似度0.8）：返回坐标，不点击
def find_image(image_name):
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        path2 = os.path.join(secondary_pic_dir, image_name)
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    if not image_path:
        p(f"[图片查找] 未找到图片文件: {image_name}")
        return False, None, None
    p(f'[图片查找] 查找图片: {image_name}')
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    template = cv2.imread(image_path)
    if template is None:
        p(f'[图片查找] 无法读取图片: {image_name}')
        return False, None, None
    result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        p(f'[图片查找] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
        return True, center_x, center_y
    else:
        p(f'[图片查找] 未找到图片 {image_name}，相似度: {max_val:.3f}')
        return False, None, None

# ==================== 执行流程 ====================

# 2.1 如果找到1-TC2.png，点击，等待2秒
found, x, y = find_image('1-TC2.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.1] 点击1-TC2.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

# 2.2 等待1秒
time.sleep(1)

# 2.3 如果找到1-TC1.png，点击，等待2秒
found, x, y = find_image('1-TC1.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.3] 点击1-TC1.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

# 2.4 等待1秒
time.sleep(1)

# 2.5 如果找到1-CC.png，点击，等待4秒
found, x, y = find_image('1-CC.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.5] 点击1-CC.png坐标: ({x}, {y})，等待4秒')
    time.sleep(4)

# 2.6 等待1秒
time.sleep(1)

# 2.7.1 多次找图1-ST.png
found, st_x, st_y = multi_find_image('1-ST.png')

if found:
    p(f"[2.7.1] 多次找图找到1-ST.png，坐标: ({st_x}, {st_y})")
    
    # 点击该坐标5次，每次等待1秒
    for i in range(5):
        pyautogui.click(st_x, st_y)
        p(f'[2.7.1] 第{i+1}次点击坐标: ({st_x}, {st_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.3 多次找图1-DW.png，点击坐标偏移X+100
    found_dw, dw_x, dw_y = multi_find_image('1-DW.png')
    if found_dw:
        offset_x = dw_x + 100
        offset_y = dw_y
        pyautogui.click(offset_x, offset_y)
        p(f'[2.7.3] 找到1-DW.png，点击偏移坐标: ({offset_x}, {offset_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.4 等待1秒
    p('[2.7.4] 等待1秒')
    time.sleep(1)
    
    # 2.7.5-2.7.9 键盘输入文本参数
    p(f'[2.7.5] 键盘输入文本参数: {coord_params}')
    from pynput.keyboard import Controller
    kb = Controller()
    kb.type(coord_params)
    p('[2.7.8] 输入完成')
    time.sleep(1)
    
    # 2.7.10 多次找图1-QD.png
    found_qd, qd_x, qd_y = multi_find_image('1-QD.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击1-QD.png坐标: ({qd_x}, {qd_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图1-QW.png
    found_qw, qw_x, qw_y = multi_find_image('1-QW.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击1-QW.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.13 等待1秒
    p('[2.7.13] 等待1秒')
    time.sleep(1)
    
    # 2.7.13.1 点击画面中心坐标(1920x1080画面，起始位置0,52，中心960,592)
    pyautogui.click(960, 592)
    p('[2.7.13.1] 点击画面中心坐标: (960, 592)，等待1秒')
    time.sleep(1)
    
    # 2.7.14 多次找图6-gc.png
    found_gz, gz_x, gz_y = multi_find_image('6-gc.png')
    if found_gz:
        pyautogui.click(gz_x, gz_y)
        p(f'[2.7.14] 点击6-gc.png坐标: ({gz_x}, {gz_y})，等待2秒')
        time.sleep(2)
    
    # 2.7.16 等待1秒
    p('[2.7.16] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    p('[打地模块] 条件成立分支执行完成')
else:
    p('[2.7.1] 多次找图未找到1-ST.png，跳过后续操作，模板执行结束')

p("="*50)
p("【打地模块】执行完成!")
p("="*50)""",
        "template": {
            "coords": [
                {"x": 0, "y": 0, "label": "坐标1"}
            ],
            "auto_input": "",
            "params": []
        }
    },
    "打地": {
        "type": "python_script",
        "description": "打地：执行打地操作",
        "has_multi_coords": True,
        "has_auto_input": True,
        "is_python_template": True,
        "python_code": """import os
import time
import pyautogui
import numpy as np
import cv2
import sys

# 强制刷新输出
def p(msg):
    print(msg, flush=True)

p("="*50)
p("【打地模块】开始执行")
p("="*50)

workgroup_id = '{{workgroup_id}}'
coord_params = '{{coord_params}}'

# 图片目录：优先工作组同步目录，其次项目默认图片目录
primary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'workgroups', workgroup_id)
secondary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'pic')

p(f"[DEBUG] workgroup_id={workgroup_id}")
p(f"[DEBUG] primary_pic_dir={primary_pic_dir}")
p(f"[DEBUG] secondary_pic_dir={secondary_pic_dir}")
p(f"[DEBUG] coord_params={coord_params}")

# 多次找图函数：返回坐标，不点击
def multi_find_image(image_name):
    \"""
    多次找图：
    - 第1次: 相似度0.9
    - 第2次: 相似度0.8
    - 第3次: 相似度0.7
    返回: (found, x, y) 或 (False, None, None)
    \"""
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    path2 = os.path.join(secondary_pic_dir, image_name)
    
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    
    thresholds = [0.9, 0.8, 0.7]
    template = None
    if image_path:
        template = cv2.imread(image_path)
        if template is None:
            p(f'[图片查找] 无法读取图片文件: {image_path}')
    
    for i, threshold in enumerate(thresholds):
        p(f'[多次找图] 第{i+1}次查找 {image_name}，相似度阈值: {threshold}')
        
        if not image_path:
            p(f'[多次找图] 图片文件不存在')
            p(f'[多次找图] 查找路径1: {path1}')
            p(f'[多次找图] 查找路径2: {path2}')
        elif template is None:
            p(f'[多次找图] 图片文件无法读取')
        else:
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            p(f'[多次找图] 相似度: {max_val:.3f}')
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                p(f'[多次找图] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
                return True, center_x, center_y
            else:
                p(f'[多次找图] 相似度 {max_val:.3f} < 阈值 {threshold}，未找到')
        
        if i < 2:
            p(f'[多次找图] 等待1秒后进行下一次查找...')
            time.sleep(1)
    
    p(f'[多次找图] 3次查找均未找到 {image_name}')
    return False, None, None

# 找图函数（固定相似度0.8）：返回坐标，不点击
def find_image(image_name):
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        path2 = os.path.join(secondary_pic_dir, image_name)
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    if not image_path:
        p(f"[图片查找] 未找到图片文件: {image_name}")
        return False, None, None
    p(f'[图片查找] 查找图片: {image_name}')
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    template = cv2.imread(image_path)
    if template is None:
        p(f'[图片查找] 无法读取图片: {image_name}')
        return False, None, None
    result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        p(f'[图片查找] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
        return True, center_x, center_y
    else:
        p(f'[图片查找] 未找到图片 {image_name}，相似度: {max_val:.3f}')
        return False, None, None

# ==================== 执行流程 ====================

# 2.1 如果找到1-TC2.png，点击，等待2秒
found, x, y = find_image('1-TC2.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.1] 点击1-TC2.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

# 2.2 等待1秒
time.sleep(1)

# 2.3 如果找到1-TC1.png，点击，等待2秒
found, x, y = find_image('1-TC1.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.3] 点击1-TC1.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

# 2.4 等待1秒
time.sleep(1)

# 2.5 如果找到1-CC.png，点击，等待4秒
found, x, y = find_image('1-CC.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.5] 点击1-CC.png坐标: ({x}, {y})，等待4秒')
    time.sleep(4)

# 2.6 等待1秒
time.sleep(1)

# 2.7.1 多次找图1-ST.png
found, st_x, st_y = multi_find_image('1-ST.png')

if found:
    p(f"[2.7.1] 多次找图找到1-ST.png，坐标: ({st_x}, {st_y})")
    
    # 点击该坐标5次，每次等待1秒
    for i in range(5):
        pyautogui.click(st_x, st_y)
        p(f'[2.7.1] 第{i+1}次点击坐标: ({st_x}, {st_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.3 多次找图1-DW.png，点击坐标偏移X+100
    found_dw, dw_x, dw_y = multi_find_image('1-DW.png')
    if found_dw:
        offset_x = dw_x + 100
        offset_y = dw_y
        pyautogui.click(offset_x, offset_y)
        p(f'[2.7.3] 找到1-DW.png，点击偏移坐标: ({offset_x}, {offset_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.4 等待1秒
    p('[2.7.4] 等待1秒')
    time.sleep(1)
    
    # 2.7.5-2.7.9 键盘输入文本参数
    p(f'[2.7.5] 键盘输入文本参数: {coord_params}')
    from pynput.keyboard import Controller
    kb = Controller()
    kb.type(coord_params)
    p('[2.7.8] 输入完成')
    time.sleep(1)
    
    # 2.7.10 多次找图1-QD.png
    found_qd, qd_x, qd_y = multi_find_image('1-QD.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击1-QD.png坐标: ({qd_x}, {qd_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图1-QW.png
    found_qw, qw_x, qw_y = multi_find_image('1-QW.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击1-QW.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.13 等待1秒
    p('[2.7.13] 等待1秒')
    time.sleep(1)
    
    # 2.7.13.1 点击画面中心坐标(1920x1080画面，起始位置0,52，中心960,592)
    pyautogui.click(960, 592)
    p('[2.7.13.1] 点击画面中心坐标: (960, 592)，等待1秒')
    time.sleep(1)
    
    # 2.7.14 多次找图1-GZ.png
    found_gz, gz_x, gz_y = multi_find_image('1-GZ.png')
    if found_gz:
        pyautogui.click(gz_x, gz_y)
        p(f'[2.7.14] 点击1-GZ.png坐标: ({gz_x}, {gz_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.15 找图1-HC.png
    found_hc, hc_x, hc_y = find_image('1-HC.png')
    if found_hc:
        pyautogui.click(hc_x, hc_y)
        p(f'[2.7.15] 点击1-HC.png坐标: ({hc_x}, {hc_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.16 等待1秒
    p('[2.7.16] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image_click('9-QD.png', 1)
    
    # 2.7.18 等待1秒
    time.sleep(1)
    
    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image_click('9-QD.png', 1)
    
    # 2.7.18 等待1秒
    time.sleep(1)
    
    p('[打地模块] 条件成立分支执行完成')
else:
    p('[2.7.1] 多次找图未找到1-ST.png，跳过后续操作，模板执行结束')

p("="*50)
p("【打地模块】执行完成!")
p("="*50)""",
        "template": {
            "coords": [
                {"x": 0, "y": 0, "label": "坐标1"}
            ],
            "auto_input": "",
            "params": []
        }
    },
    "翻红地": {
        "type": "python_script",
        "description": "翻红地：执行翻红地操作",
        "has_multi_coords": True,
        "has_auto_input": True,
        "is_python_template": True,
        "python_code": """import os
import time
import pyautogui
import numpy as np
import cv2

# 强制刷新输出
def p(msg):
    print(msg, flush=True)

p("="*50)
p("【翻红地模块】开始执行")
p("="*50)

workgroup_id = '{{workgroup_id}}'
coord_params = '{{coord_params}}'

primary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'workgroups', workgroup_id)
secondary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'pic')

p(f"[DEBUG] workgroup_id={workgroup_id}")
p(f"[DEBUG] primary_pic_dir={primary_pic_dir}")
p(f"[DEBUG] secondary_pic_dir={secondary_pic_dir}")

# 要查找的红地图片列表
RED_LAND_IMAGES = [
    '8-HDL.png', '8-HDL2.png', '8-HDL3.png',
    '8-HDM.png', '8-HDM2.png', '8-HDM3.png',
    '8-HDS.png', '8-HDS2.png', '8-HDS3.png',
    '8-HDT.png', '8-HDT2.png', '8-HDT3.png',
    '8HY1.png', '8HY10.png', '8HY2.png', '8HY3.png',
    '8HY4.png', '8HY5.png', '8HY6.png', '8HY7.png',
    '8HY8.png', '8HY9.png', '8HY10.png', '8HY11.png', 
    '8HY12.png', '8HY13.png', '8HY14.png', '8HY15.png',
    '8HY16.png', '8HY17.png', '8HY18.png', '8HY19.png' 
]

# 快速找多图函数：以0.7相似度查找，每个间隔200ms
def find_any_red_land():
    for image_name in RED_LAND_IMAGES:
        image_path = None
        path1 = os.path.join(primary_pic_dir, image_name)
        path2 = os.path.join(secondary_pic_dir, image_name)
        
        if os.path.exists(path1):
            image_path = path1
        elif os.path.exists(path2):
            image_path = path2
        
        if not image_path:
            continue
        
        template = cv2.imread(image_path)
        if template is None:
            continue
        
        screenshot = pyautogui.screenshot()
        screen_np = np.array(screenshot)
        screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
        result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= 0.7:
            h, w = template.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            p(f'[找红地] 找到图片 {image_name}，相似度: {max_val:.3f}，坐标: ({center_x}, {center_y})')
            return True, center_x, center_y, image_name
        
        time.sleep(0.2)
    
    return False, None, None, None

# 多次找图函数（相似度递减）
def multi_find_image(image_name):
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    path2 = os.path.join(secondary_pic_dir, image_name)
    
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    
    thresholds = [0.9, 0.8, 0.7]
    template = None
    if image_path:
        template = cv2.imread(image_path)
        if template is None:
            p(f'[图片查找] 无法读取图片文件: {image_path}')
    
    for i, threshold in enumerate(thresholds):
        p(f'[多次找图] 第{i+1}次查找 {image_name}，相似度阈值: {threshold}')
        
        if not image_path:
            p(f'[多次找图] 图片文件不存在')
        elif template is None:
            p(f'[多次找图] 图片文件无法读取')
        else:
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            p(f'[多次找图] 相似度: {max_val:.3f}')
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                p(f'[多次找图] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
                return True, center_x, center_y
            else:
                p(f'[多次找图] 相似度 {max_val:.3f} < 阈值 {threshold}，未找到')
        
        if i < 2:
            p(f'[多次找图] 等待1秒后进行下一次查找...')
            time.sleep(1)
    
    p(f'[多次找图] 3次查找均未找到 {image_name}')
    return False, None, None

# 找图函数（固定相似度0.8）：返回坐标，不点击
def find_image(image_name):
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        path2 = os.path.join(secondary_pic_dir, image_name)
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    if not image_path:
        p(f"[图片查找] 未找到图片文件: {image_name}")
        return False, None, None
    p(f'[图片查找] 查找图片: {image_name}')
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    template = cv2.imread(image_path)
    if template is None:
        p(f'[图片查找] 无法读取图片: {image_name}')
        return False, None, None
    result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        p(f'[图片查找] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
        return True, center_x, center_y
    else:
        p(f'[图片查找] 未找到图片 {image_name}，相似度: {max_val:.3f}')
        return False, None, None

# ==================== A部分：执行初始操作 ====================
p("[A部分] 开始执行初始操作")

# 2.7.12.1 等待1秒
p('[2.7.12.1] 等待1秒')
time.sleep(1)

# 2.1 如果找到1-TC2.png，点击，等待2秒
found, x, y = find_image('1-TC2.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.1] 点击1-TC2.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

# 2.2 等待1秒
time.sleep(1)

# 2.3 如果找到1-TC1.png，点击，等待2秒
found, x, y = find_image('1-TC1.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.3] 点击1-TC1.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

# 2.4 等待1秒
time.sleep(1)

# 2.5 如果找到1-CC.png，点击，等待4秒
found, x, y = find_image('1-CC.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.5] 点击1-CC.png坐标: ({x}, {y})，等待4秒')
    time.sleep(4)

# 2.6 等待1秒
time.sleep(1)

# 2.7.1 多次找图1-ST.png
found, st_x, st_y = multi_find_image('1-ST.png')

if found:
    p(f"[2.7.1] 多次找图找到1-ST.png，坐标: ({st_x}, {st_y})")
    
    # 点击该坐标5次，每次等待1秒
    for i in range(5):
        pyautogui.click(st_x, st_y)
        p(f'[2.7.1] 第{i+1}次点击坐标: ({st_x}, {st_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.3 多次找图1-DW.png，点击坐标偏移X+100
    found_dw, dw_x, dw_y = multi_find_image('1-DW.png')
    if found_dw:
        offset_x = dw_x + 100
        offset_y = dw_y
        pyautogui.click(offset_x, offset_y)
        p(f'[2.7.3] 找到1-DW.png，点击偏移坐标: ({offset_x}, {offset_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.4 等待1秒
    p('[2.7.4] 等待1秒')
    time.sleep(1)
    
    # 2.7.5-2.7.9 键盘输入文本参数
    p(f'[2.7.5] 键盘输入文本参数: {coord_params}')
    from pynput.keyboard import Controller
    kb = Controller()
    kb.type(coord_params)
    p('[2.7.8] 输入完成')
    time.sleep(1)
    
    # 2.7.10 多次找图1-QD.png
    found_qd, qd_x, qd_y = multi_find_image('1-QD.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击1-QD.png坐标: ({qd_x}, {qd_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图1-QW.png
    found_qw, qw_x, qw_y = multi_find_image('1-QW.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击1-QW.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.13 等待1秒
    p('[2.7.13] 等待1秒')
    time.sleep(1)

# 2.1 如果找到1-ST2.png，点击，等待2秒
found, x, y = find_image('1-ST2.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.1] 点击1-TC2.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)


# 2.1 如果找到1-ST.png，点击，等待2秒
found, x, y = find_image('1-ST.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.1] 点击1-TC.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

    # 2.7.13 等待1秒
    p('[2.7.13] 等待1秒')
    time.sleep(1)
    
# ==================== B-C循环部分 ====================
p("[B-C循环] 开始循环查找红地图片")

for loop_count in range(1, 11):
    p(f"[B部分] 第 {loop_count} 次循环开始")
    
    found, x, y, img_name = find_any_red_land()
    
    if not found:
        p(f'[B部分] 第 {loop_count} 次循环未找到任何红地图片，退出循环')
        p('[翻红地模块] 任务完成，没有更多红地')
        break
    
    pyautogui.click(x, y)
    p(f'[B部分] 点击 {img_name} 坐标: ({x}, {y})，等待1秒')
    time.sleep(1)
    
    p('[C部分] 执行后续操作')
    p('[2.7.22] 等待1秒')
    time.sleep(1)

    # 2.7.14 多次找图1-GZ.png
    found_gz, gz_x, gz_y = multi_find_image('1-GZ.png')
    if found_gz:
        pyautogui.click(gz_x, gz_y)
        p(f'[2.7.14] 点击1-GZ.png坐标: ({gz_x}, {gz_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.14 多次找图6-gc.png
    found_gz, gz_x, gz_y = multi_find_image('6-gc.png')
    if found_gz:
        pyautogui.click(gz_x, gz_y)
        p(f'[2.7.14] 点击6-gc.png坐标: ({gz_x}, {gz_y})，等待1秒')
        time.sleep(1)

    # 2.7.15 找图9-QD.png
    found_hc, hc_x, hc_y = find_image('9-QD.png')
    if found_hc:
        pyautogui.click(hc_x, hc_y)
        p(f'[2.7.15] 点击9-QD.png坐标: ({hc_x}, {hc_y})，等待1秒')
        time.sleep(1)

    # 2.7.15 找图1-HC.png
    found_hc, hc_x, hc_y = find_image('1-HC.png')
    if found_hc:
        pyautogui.click(hc_x, hc_y)
        p(f'[2.7.15] 点击1-HC.png坐标: ({hc_x}, {hc_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.16 等待1秒
    p('[2.7.16] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)

 
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.15 找图9-QD.png
    found_hc, hc_x, hc_y = find_image('9-QD.png')
    if found_hc:
        pyautogui.click(hc_x, hc_y)
        p(f'[2.7.15] 点击9-QD.png坐标: ({hc_x}, {hc_y})，等待1秒')
        time.sleep(1)
  
    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.15 找图9-QD.png
    found_hc, hc_x, hc_y = find_image('9-QD.png')
    if found_hc:
        pyautogui.click(hc_x, hc_y)
        p(f'[2.7.15] 点击9-QD.png坐标: ({hc_x}, {hc_y})，等待1秒')
        time.sleep(1)

    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    p('[翻红地模块] 条件成立分支执行完成')
    
    if loop_count < 10:
        p(f"[等待] 等待3分钟后进行下一次循环...")
        time.sleep(180)

p("")
p("="*50)
p("【翻红地模块】全部执行完成!")
p("="*50)""",
        "template": {
            "coords": [
                {"x": 0, "y": 0, "label": "坐标1"}
            ],
            "auto_input": "",
            "params": []
        }
    },
    "铺路": {
        "type": "python_script",
        "description": "铺路：执行铺路操作",
        "has_multi_coords": True,
        "has_auto_input": True,
        "is_python_template": True,
        "python_code": """import os
import time
import pyautogui
import numpy as np
import cv2
import sys

# 强制刷新输出
def p(msg):
    print(msg, flush=True)

p("="*50)
p("【铺路模块】开始执行")
p("="*50)

workgroup_id = '{{workgroup_id}}'
coord_params = '{{coord_params}}'

# 解析多个参数（用逗号或分号分隔）
params_list = [param.strip() for param in coord_params.replace(';', ',').split(',') if param.strip()]
p(f"[DEBUG] 解析到 {len(params_list)} 个参数: {params_list}")

primary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'workgroups', workgroup_id)
secondary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'pic')

p(f"[DEBUG] workgroup_id={workgroup_id}")
p(f"[DEBUG] primary_pic_dir={primary_pic_dir}")
p(f"[DEBUG] secondary_pic_dir={secondary_pic_dir}")
p(f"[DEBUG] coord_params={coord_params}")

# 多次找图函数：返回坐标，不点击
def multi_find_image(image_name):
    \"""
    多次找图：
    - 第1次: 相似度0.9
    - 第2次: 相似度0.8
    - 第3次: 相似度0.7
    返回: (found, x, y) 或 (False, None, None)
    \"""
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    path2 = os.path.join(secondary_pic_dir, image_name)
    
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    
    thresholds = [0.9, 0.8, 0.7]
    template = None
    if image_path:
        template = cv2.imread(image_path)
        if template is None:
            p(f'[图片查找] 无法读取图片文件: {image_path}')
    
    for i, threshold in enumerate(thresholds):
        p(f'[多次找图] 第{i+1}次查找 {image_name}，相似度阈值: {threshold}')
        
        if not image_path:
            p(f'[多次找图] 图片文件不存在')
            p(f'[多次找图] 查找路径1: {path1}')
            p(f'[多次找图] 查找路径2: {path2}')
        elif template is None:
            p(f'[多次找图] 图片文件无法读取')
        else:
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            p(f'[多次找图] 相似度: {max_val:.3f}')
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                p(f'[多次找图] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
                return True, center_x, center_y
            else:
                p(f'[多次找图] 相似度 {max_val:.3f} < 阈值 {threshold}，未找到')
        
        if i < 2:
            p(f'[多次找图] 等待1秒后进行下一次查找...')
            time.sleep(1)
    
    p(f'[多次找图] 3次查找均未找到 {image_name}')
    return False, None, None

# 找图函数（固定相似度0.8）：返回坐标，不点击
def find_image(image_name):
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        path2 = os.path.join(secondary_pic_dir, image_name)
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    if not image_path:
        p(f"[图片查找] 未找到图片文件: {image_name}")
        return False, None, None
    p(f'[图片查找] 查找图片: {image_name}')
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    template = cv2.imread(image_path)
    if template is None:
        p(f'[图片查找] 无法读取图片: {image_name}')
        return False, None, None
    result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        p(f'[图片查找] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
        return True, center_x, center_y
    else:
        p(f'[图片查找] 未找到图片 {image_name}，相似度: {max_val:.3f}')
        return False, None, None

# ==================== 执行一轮操作的函数 ====================
def execute_round(current_param, round_num, total_rounds):
    p("")
    p("="*50)
    p(f"【第 {round_num}/{total_rounds} 轮】参数: {current_param}")
    p("="*50)
    
    # ==================== 执行流程 A到B ====================
    
    # 2.1 如果找到1-TC2.png，点击，等待2秒
    found, x, y = find_image('1-TC2.png')
    if found:
        pyautogui.click(x, y)
        p(f'[2.1] 点击1-TC2.png坐标: ({x}, {y})，等待2秒')
        time.sleep(2)
    
    # 2.2 等待1秒
    time.sleep(1)
    
    # 2.3 如果找到1-TC1.png，点击，等待2秒
    found, x, y = find_image('1-TC1.png')
    if found:
        pyautogui.click(x, y)
        p(f'[2.3] 点击1-TC1.png坐标: ({x}, {y})，等待2秒')
        time.sleep(2)
    
    # 2.4 等待1秒
    time.sleep(1)
    
    # 2.5 如果找到1-CC.png，点击，等待4秒
    found, x, y = find_image('1-CC.png')
    if found:
        pyautogui.click(x, y)
        p(f'[2.5] 点击1-CC.png坐标: ({x}, {y})，等待4秒')
        time.sleep(4)
    
    # 2.6 等待1秒
    time.sleep(1)
    
    # 2.7.1 多次找图1-ST.png
    found, st_x, st_y = multi_find_image('1-ST.png')
    
    if found:
        p(f"[2.7.1] 多次找图找到1-ST.png，坐标: ({st_x}, {st_y})")
        
        # 点击该坐标5次，每次等待1秒
        for i in range(5):
            pyautogui.click(st_x, st_y)
            p(f'[2.7.1] 第{i+1}次点击坐标: ({st_x}, {st_y})，等待1秒')
            time.sleep(1)
        
        # 2.7.2 等待1秒
        p('[2.7.2] 等待1秒')
        time.sleep(1)
        
        # 2.7.3 多次找图1-DW.png，点击坐标偏移X+100
        found_dw, dw_x, dw_y = multi_find_image('1-DW.png')
        if found_dw:
            offset_x = dw_x + 100
            offset_y = dw_y
            pyautogui.click(offset_x, offset_y)
            p(f'[2.7.3] 找到1-DW.png，点击偏移坐标: ({offset_x}, {offset_y})，等待1秒')
            time.sleep(1)
        
        # 2.7.4 等待1秒
        p('[2.7.4] 等待1秒')
        time.sleep(1)
        
        # 2.7.5-2.7.9 键盘输入文本参数（使用当前轮次的参数）
        p(f'[2.7.5] 键盘输入文本参数: {current_param}')
        from pynput.keyboard import Controller
        kb = Controller()
        kb.type(current_param)
        p('[2.7.8] 输入完成')
        time.sleep(1)
        
        # 2.7.10 多次找图1-QD.png
        found_qd, qd_x, qd_y = multi_find_image('1-QD.png')
        if found_qd:
            pyautogui.click(qd_x, qd_y)
            p(f'[2.7.10] 点击1-QD.png坐标: ({qd_x}, {qd_y})，等待1秒')
            time.sleep(1)
        
        # 2.7.11 等待1秒
        p('[2.7.11] 等待1秒')
        time.sleep(1)
        
        # 2.7.12 多次找图1-QW.png
        found_qw, qw_x, qw_y = multi_find_image('1-QW.png')
        if found_qw:
            pyautogui.click(qw_x, qw_y)
            p(f'[2.7.12] 点击1-QW.png坐标: ({qw_x}, {qw_y})，等待1秒')
            time.sleep(1)
        
        # 2.7.13 等待1秒
        p('[2.7.13] 等待1秒')
        time.sleep(1)
        
        # 2.7.13.1 点击画面中心坐标(1920x1080画面，起始位置0,52，中心960,592)
        pyautogui.click(960, 592)
        p('[2.7.13.1] 点击画面中心坐标: (960, 592)，等待1秒')
        time.sleep(1)
        
        # 2.7.14 多次找图1-GZ.png
        found_gz, gz_x, gz_y = multi_find_image('1-GZ.png')
        if found_gz:
            pyautogui.click(gz_x, gz_y)
            p(f'[2.7.14] 点击1-GZ.png坐标: ({gz_x}, {gz_y})，等待1秒')
            time.sleep(1)
        
        # 2.7.15 找图1-HC.png
        found_hc, hc_x, hc_y = find_image('1-HC.png')
        if found_hc:
            pyautogui.click(hc_x, hc_y)
            p(f'[2.7.15] 点击1-HC.png坐标: ({hc_x}, {hc_y})，等待1秒')
            time.sleep(1)
        
        # 2.7.16 等待1秒
        p('[2.7.16] 等待1秒')
        time.sleep(1)
        
        # 2.7.17 找图1-YJBB.png
        found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
        if found_yjbb:
            pyautogui.click(yjbb_x, yjbb_y)
            p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
            time.sleep(1)
        
        # 2.7.18 等待1秒
        p('[2.7.18] 等待1秒')
        time.sleep(1)
        
        # 2.7.19 找图1-CZ.png
        found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
        if found_cz1:
            pyautogui.click(cz1_x, cz1_y)
            p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
            time.sleep(1)
        
        # 2.7.20 等待1秒
        p('[2.7.20] 等待1秒')
        time.sleep(1)

        # 2.7.15 找图9-JXCZ.png
        found_hc, hc_x, hc_y = find_image('9-JXCZ.png')
        if found_hc:
            pyautogui.click(hc_x, hc_y)
            p(f'[2.7.15] 点击1-HC.png坐标: ({hc_x}, {hc_y})，等待1秒')
            time.sleep(1)

        # 2.7.15 找图9-QD.png
        found_hc, hc_x, hc_y = find_image('9-QD.png')
        if found_hc:
            pyautogui.click(hc_x, hc_y)
            p(f'[2.7.15] 点击1-HC.png坐标: ({hc_x}, {hc_y})，等待1秒')
            time.sleep(1)
        
        # 2.7.21 再次找图1-CZ.png
        found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
        if found_cz2:
            pyautogui.click(cz2_x, cz2_y)
            p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
            time.sleep(1)
        
        # 2.7.22 等待1秒
        p('[2.7.22] 等待1秒')
        time.sleep(1)

        # 2.7.15 找图9-JXCZ.png
        found_hc, hc_x, hc_y = find_image('9-JXCZ.png')
        if found_hc:
            pyautogui.click(hc_x, hc_y)
            p(f'[2.7.15] 点击1-HC.png坐标: ({hc_x}, {hc_y})，等待1秒')
            time.sleep(1)

        # 2.7.15 找图9-QD.png
        found_hc, hc_x, hc_y = find_image('9-QD.png')
        if found_hc:
            pyautogui.click(hc_x, hc_y)
            p(f'[2.7.15] 点击1-HC.png坐标: ({hc_x}, {hc_y})，等待1秒')
            time.sleep(1)
         
        p('[铺路模块] 条件成立分支执行完成')
    else:
        p('[2.7.1] 多次找图未找到1-ST.png，跳过后续操作，模板执行结束')
    
    # ==================== 执行流程结束 ====================

# ==================== 主循环：对每个参数执行一轮 ====================
total_params = len(params_list)
for i, param in enumerate(params_list):
    round_num = i + 1
    
    # 执行当前轮次
    execute_round(param, round_num, total_params)
    
    # 如果不是最后一个参数，等待3分钟
    if round_num < total_params:
        p("")
        p(f"[等待] 等待30分钟后执行下一轮...")
        time.sleep(1800)  # 30分钟 = 1800秒

p("")
p("="*50)
p("【铺路模块】全部执行完成!")
p(f"共执行 {total_params} 轮")
p("="*50)""",
        "template": {
            "coords": [
                {"x": 0, "y": 0, "label": "坐标1"}
            ],
            "auto_input": "",
            "params": []
        }
    },
    "驻守": {
        "type": "python_script",
        "description": "驻守：执行驻守操作",
        "has_multi_coords": True,
        "has_auto_input": True,
        "is_python_template": True,
        "python_code": """import os
import time
import pyautogui
import numpy as np
import cv2
import sys

# 强制刷新输出
def p(msg):
    print(msg, flush=True)

p("="*50)
p("【打地模块】开始执行")
p("="*50)

workgroup_id = '{{workgroup_id}}'
coord_params = '{{coord_params}}'

# 图片目录：优先工作组同步目录，其次项目默认图片目录
primary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'workgroups', workgroup_id)
secondary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'pic')

p(f"[DEBUG] workgroup_id={workgroup_id}")
p(f"[DEBUG] primary_pic_dir={primary_pic_dir}")
p(f"[DEBUG] secondary_pic_dir={secondary_pic_dir}")
p(f"[DEBUG] coord_params={coord_params}")

# 多次找图函数：返回坐标，不点击
def multi_find_image(image_name):
    \"""
    多次找图：
    - 第1次: 相似度0.9
    - 第2次: 相似度0.8
    - 第3次: 相似度0.7
    返回: (found, x, y) 或 (False, None, None)
    \"""
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    path2 = os.path.join(secondary_pic_dir, image_name)
    
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    
    thresholds = [0.9, 0.8, 0.7]
    template = None
    if image_path:
        template = cv2.imread(image_path)
        if template is None:
            p(f'[图片查找] 无法读取图片文件: {image_path}')
    
    for i, threshold in enumerate(thresholds):
        p(f'[多次找图] 第{i+1}次查找 {image_name}，相似度阈值: {threshold}')
        
        if not image_path:
            p(f'[多次找图] 图片文件不存在')
            p(f'[多次找图] 查找路径1: {path1}')
            p(f'[多次找图] 查找路径2: {path2}')
        elif template is None:
            p(f'[多次找图] 图片文件无法读取')
        else:
            screenshot = pyautogui.screenshot()
            screen_np = np.array(screenshot)
            screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
            result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            p(f'[多次找图] 相似度: {max_val:.3f}')
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                p(f'[多次找图] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
                return True, center_x, center_y
            else:
                p(f'[多次找图] 相似度 {max_val:.3f} < 阈值 {threshold}，未找到')
        
        if i < 2:
            p(f'[多次找图] 等待1秒后进行下一次查找...')
            time.sleep(1)
    
    p(f'[多次找图] 3次查找均未找到 {image_name}')
    return False, None, None

# 找图函数（固定相似度0.8）：返回坐标，不点击
def find_image(image_name):
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    if os.path.exists(path1):
        image_path = path1
        p(f"[图片查找] 找到文件(工作组): {path1}")
    if not image_path:
        path2 = os.path.join(secondary_pic_dir, image_name)
        if os.path.exists(path2):
            image_path = path2
            p(f"[图片查找] 找到文件(默认): {path2}")
    if not image_path:
        p(f"[图片查找] 未找到图片文件: {image_name}")
        return False, None, None
    p(f'[图片查找] 查找图片: {image_name}')
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    template = cv2.imread(image_path)
    if template is None:
        p(f'[图片查找] 无法读取图片: {image_name}')
        return False, None, None
    result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        p(f'[图片查找] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
        return True, center_x, center_y
    else:
        p(f'[图片查找] 未找到图片 {image_name}，相似度: {max_val:.3f}')
        return False, None, None

# ==================== 执行流程 ====================

# 2.1 如果找到1-TC2.png，点击，等待2秒
found, x, y = find_image('1-TC2.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.1] 点击1-TC2.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

# 2.2 等待1秒
time.sleep(1)

# 2.3 如果找到1-TC1.png，点击，等待2秒
found, x, y = find_image('1-TC1.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.3] 点击1-TC1.png坐标: ({x}, {y})，等待2秒')
    time.sleep(2)

# 2.4 等待1秒
time.sleep(1)

# 2.5 如果找到1-CC.png，点击，等待4秒
found, x, y = find_image('1-CC.png')
if found:
    pyautogui.click(x, y)
    p(f'[2.5] 点击1-CC.png坐标: ({x}, {y})，等待4秒')
    time.sleep(4)

# 2.6 等待1秒
time.sleep(1)

# 2.7.1 多次找图1-ST.png
found, st_x, st_y = multi_find_image('1-ST.png')

if found:
    p(f"[2.7.1] 多次找图找到1-ST.png，坐标: ({st_x}, {st_y})")
    
    # 点击该坐标5次，每次等待1秒
    for i in range(5):
        pyautogui.click(st_x, st_y)
        p(f'[2.7.1] 第{i+1}次点击坐标: ({st_x}, {st_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.2 等待1秒
    p('[2.7.2] 等待1秒')
    time.sleep(1)
    
    # 2.7.3 多次找图1-DW.png，点击坐标偏移X+100
    found_dw, dw_x, dw_y = multi_find_image('1-DW.png')
    if found_dw:
        offset_x = dw_x + 100
        offset_y = dw_y
        pyautogui.click(offset_x, offset_y)
        p(f'[2.7.3] 找到1-DW.png，点击偏移坐标: ({offset_x}, {offset_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.4 等待1秒
    p('[2.7.4] 等待1秒')
    time.sleep(1)
    
    # 2.7.5-2.7.9 键盘输入文本参数
    p(f'[2.7.5] 键盘输入文本参数: {coord_params}')
    from pynput.keyboard import Controller
    kb = Controller()
    kb.type(coord_params)
    p('[2.7.8] 输入完成')
    time.sleep(1)
    
    # 2.7.10 多次找图1-QD.png
    found_qd, qd_x, qd_y = multi_find_image('1-QD.png')
    if found_qd:
        pyautogui.click(qd_x, qd_y)
        p(f'[2.7.10] 点击1-QD.png坐标: ({qd_x}, {qd_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.11 等待1秒
    p('[2.7.11] 等待1秒')
    time.sleep(1)
    
    # 2.7.12 多次找图1-QW.png
    found_qw, qw_x, qw_y = multi_find_image('1-QW.png')
    if found_qw:
        pyautogui.click(qw_x, qw_y)
        p(f'[2.7.12] 点击1-QW.png坐标: ({qw_x}, {qw_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.13 等待1秒
    p('[2.7.13] 等待1秒')
    time.sleep(1)
    
    # 2.7.13.1 点击画面中心坐标(1920x1080画面，起始位置0,52，中心960,592)
    pyautogui.click(960, 592)
    p('[2.7.13.1] 点击画面中心坐标: (960, 592)，等待1秒')
    time.sleep(1)
    
    # 2.7.14 多次找图10-ZS.png
    found_gz, gz_x, gz_y = multi_find_image('10-ZS.png')
    if found_gz:
        pyautogui.click(gz_x, gz_y)
        p(f'[2.7.14] 点击10-ZS.png坐标: ({gz_x}, {gz_y})，等待2秒')
        time.sleep(2)
    
    # 2.7.16 等待1秒
    p('[2.7.16] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图1-YJBB.png
    found_yjbb, yjbb_x, yjbb_y = find_image('1-YJBB.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击1-YJBB.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.18 等待1秒
    p('[2.7.18] 等待1秒')
    time.sleep(1)
    
    # 2.7.19 找图1-CZ.png
    found_cz1, cz1_x, cz1_y = find_image('1-CZ.png')
    if found_cz1:
        pyautogui.click(cz1_x, cz1_y)
        p(f'[2.7.19] 点击1-CZ.png坐标: ({cz1_x}, {cz1_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.20 等待1秒
    p('[2.7.20] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    # 2.7.21 再次找图1-CZ.png
    found_cz2, cz2_x, cz2_y = find_image('1-CZ.png')
    if found_cz2:
        pyautogui.click(cz2_x, cz2_y)
        p(f'[2.7.21] 点击1-CZ.png坐标: ({cz2_x}, {cz2_y})，等待1秒')
        time.sleep(1)
    
    # 2.7.22 等待1秒
    p('[2.7.22] 等待1秒')
    time.sleep(1)
    
    # 2.7.17 找图9-QD.png
    found_yjbb, yjbb_x, yjbb_y = find_image('9-QD.png')
    if found_yjbb:
        pyautogui.click(yjbb_x, yjbb_y)
        p(f'[2.7.17] 点击9-QD.png坐标: ({yjbb_x}, {yjbb_y})，等待1秒')
        time.sleep(1)

    p('[打地模块] 条件成立分支执行完成')
else:
    p('[2.7.1] 多次找图未找到1-ST.png，跳过后续操作，模板执行结束')

p("="*50)
p("【打地模块】执行完成!")
p("="*50)""",
        "template": {
            "coords": [
                {"x": 0, "y": 0, "label": "坐标1"}
            ],
            "auto_input": "",
            "params": []
        }
    }
}


# 指挥命令状态
CMD_STATUS_PENDING = "pending"
CMD_STATUS_QUEUED = "queued"
CMD_STATUS_EXECUTING = "executing"
CMD_STATUS_PAUSED = "paused"
CMD_STATUS_STOPPED = "stopped"
CMD_STATUS_COMPLETED = "completed"

CMD_STATUS_TEXT = {
    CMD_STATUS_PENDING: "待执行",
    CMD_STATUS_QUEUED: "排队中",
    CMD_STATUS_EXECUTING: "执行中",
    CMD_STATUS_PAUSED: "已暂停",
    CMD_STATUS_STOPPED: "已停止",
    CMD_STATUS_COMPLETED: "已执行"
}

CMD_STATUS_COLORS = {
    CMD_STATUS_PENDING: "#FFA500",
    CMD_STATUS_QUEUED: "#9932CC",
    CMD_STATUS_EXECUTING: "#00AA00",
    CMD_STATUS_PAUSED: "#FFD700",
    CMD_STATUS_STOPPED: "#FF4444",
    CMD_STATUS_COMPLETED: "#888888"
}


def create_command_tab(self):
    """创建指挥标签页"""
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text='指挥')

    # 初始化指挥相关数据
    self.cmd_templates = {}
    self.cmd_list = []
    self.cmd_running = False
    self.cmd_paused = False
    self.cmd_stop_flag = False
    self._sync_paused = False
    self.cmd_current_executing_index = -1
    self.cmd_current_coord_index = 0
    self.cmd_selected_index = None
    self.cmd_current_template_name = None

    # 加载自定义模板
    _load_command_templates(self)

    # ====== 第一区域：顶部 - 命令模板快捷列表 ======
    top_frame = ttk.LabelFrame(tab, text='命令模板')
    top_frame.pack(fill=tk.X, padx=5, pady=(5, 2))

    # 模板按钮容器(可横向滚动)
    template_canvas_frame = ttk.Frame(top_frame)
    template_canvas_frame.pack(fill=tk.X, padx=5, pady=2)

    self.cmd_template_canvas = tk.Canvas(template_canvas_frame, height=35, highlightthickness=0)
    template_scrollbar = ttk.Scrollbar(template_canvas_frame, orient=tk.HORIZONTAL,
                                        command=self.cmd_template_canvas.xview)
    self.cmd_template_inner = ttk.Frame(self.cmd_template_canvas)

    self.cmd_template_inner.bind('<Configure>',
        lambda e: self.cmd_template_canvas.configure(scrollregion=self.cmd_template_canvas.bbox("all")))
    self.cmd_template_canvas.create_window((0, 0), window=self.cmd_template_inner, anchor="nw")
    self.cmd_template_canvas.configure(xscrollcommand=template_scrollbar.set)

    self.cmd_template_canvas.pack(side=tk.TOP, fill=tk.X, expand=True)
    template_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

    # 模板操作按钮
    tpl_btn_frame = ttk.Frame(top_frame)
    tpl_btn_frame.pack(fill=tk.X, padx=5, pady=(2, 5))

    ttk.Button(tpl_btn_frame, text='+ 新建模板', command=self.cmd_new_template, width=12).pack(side=tk.LEFT, padx=2)
    ttk.Button(tpl_btn_frame, text='复制模板', command=self.cmd_copy_template, width=12).pack(side=tk.LEFT, padx=2)
    ttk.Button(tpl_btn_frame, text='编辑模板', command=self.cmd_edit_selected_template, width=12).pack(side=tk.LEFT, padx=2)
    ttk.Button(tpl_btn_frame, text='删除模板', command=self.cmd_delete_template, width=12).pack(side=tk.LEFT, padx=2)
    ttk.Button(tpl_btn_frame, text='保存全部模板', command=self.cmd_backup_all_templates, width=12).pack(side=tk.LEFT, padx=2)
    ttk.Button(tpl_btn_frame, text='恢复全部模板', command=self.cmd_restore_all_templates, width=12).pack(side=tk.LEFT, padx=2)

    # ====== 第二区域：中间 - 命令编辑区 ======
    mid_frame = ttk.LabelFrame(tab, text='命令编辑')
    mid_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)

    # 编辑内容区(使用PanedWindow上下分割)
    edit_paned = ttk.PanedWindow(mid_frame, orient=tk.VERTICAL)
    edit_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # --- 上半：参数设置 ---
    coord_frame = ttk.Frame(edit_paned)
    edit_paned.add(coord_frame, weight=1)

    ttk.Label(coord_frame, text='参数设置:', font=('', 10, 'bold')).pack(anchor='w', padx=5, pady=2)

    # 参数列表
    coord_list_frame = ttk.Frame(coord_frame)
    coord_list_frame.pack(fill=tk.BOTH, expand=True, padx=5)

    coord_list_scroll = ttk.Scrollbar(coord_list_frame, orient=tk.VERTICAL)
    self.cmd_coord_listbox = tk.Listbox(coord_list_frame, height=4,
        yscrollcommand=coord_list_scroll.set, font=('Consolas', 9))
    coord_list_scroll.config(command=self.cmd_coord_listbox.yview)
    self.cmd_coord_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    coord_list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # 坐标操作按钮
    coord_btn_frame = ttk.Frame(coord_frame)
    coord_btn_frame.pack(fill=tk.X, padx=5, pady=2)

    self.cmd_add_coord_btn = ttk.Button(coord_btn_frame, text='+ 添加参数', command=self.cmd_add_coord, width=12)
    self.cmd_add_coord_btn.pack(side=tk.LEFT, padx=2)
    self.cmd_remove_coord_btn = ttk.Button(coord_btn_frame, text='- 删除参数', command=self.cmd_remove_coord, width=12)
    self.cmd_remove_coord_btn.pack(side=tk.LEFT, padx=2)
    ttk.Button(coord_btn_frame, text='输入参数', command=self.cmd_pick_coord, width=12).pack(side=tk.LEFT, padx=2)

    # 是否自动输入坐标参数
    self.cmd_auto_input_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(coord_btn_frame, text='自动输入坐标参数',
        variable=self.cmd_auto_input_var).pack(side=tk.LEFT, padx=10)

    # --- 下半：工作流和执行模式 ---
    workflow_exec_frame = ttk.Frame(edit_paned)
    edit_paned.add(workflow_exec_frame, weight=1)

    # 工作流设置
    wf_frame = ttk.Frame(workflow_exec_frame)
    wf_frame.pack(fill=tk.X, padx=5, pady=2)

    ttk.Label(wf_frame, text='执行模板:', font=('', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 5))

    # 工作流下拉选择
    self.cmd_workflow_combo = ttk.Combobox(wf_frame, width=20, state='readonly')
    self.cmd_workflow_combo.pack(side=tk.LEFT, padx=2)

    self.cmd_add_wf_btn = ttk.Button(wf_frame, text='添加', command=self.cmd_add_workflow, width=6)
    self.cmd_add_wf_btn.pack(side=tk.LEFT, padx=2)
    self.cmd_remove_wf_btn = ttk.Button(wf_frame, text='移除', command=self.cmd_remove_workflow, width=6)
    self.cmd_remove_wf_btn.pack(side=tk.LEFT, padx=2)

    # 已选工作流列表
    self.cmd_workflow_listbox = tk.Listbox(wf_frame, height=3, font=('Consolas', 9), width=30)
    self.cmd_workflow_listbox.pack(side=tk.LEFT, padx=5, fill=tk.BOTH, expand=True)

    # 执行模式
    exec_mode_frame = ttk.Frame(workflow_exec_frame)
    exec_mode_frame.pack(fill=tk.X, padx=5, pady=2)

    ttk.Label(exec_mode_frame, text='执行模式:', font=('', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 5))

    self.cmd_exec_mode_var = tk.StringVar(value='scheduled')
    ttk.Radiobutton(exec_mode_frame, text='定时执行', variable=self.cmd_exec_mode_var,
        value='scheduled').pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(exec_mode_frame, text='延时执行', variable=self.cmd_exec_mode_var,
        value='delayed').pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(exec_mode_frame, text='立即执行', variable=self.cmd_exec_mode_var,
        value='immediate').pack(side=tk.LEFT, padx=5)

    # 定时/延时时间输入
    self.cmd_time_entry = ttk.Entry(exec_mode_frame, width=12)
    self.cmd_time_entry.pack(side=tk.LEFT, padx=5)
    self.cmd_time_entry.insert(0, "00:05:00")
    self.cmd_time_label = ttk.Label(exec_mode_frame, text='(HH:MM:SS)')
    self.cmd_time_label.pack(side=tk.LEFT, padx=2)

    # 绑定执行模式变化
    self.cmd_exec_mode_var.trace_add('write', self._on_exec_mode_changed)

    # 编辑区操作按钮
    edit_btn_frame = ttk.Frame(mid_frame)
    edit_btn_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

    ttk.Button(edit_btn_frame, text='确认保存', command=self.cmd_confirm_edit, width=12).pack(side=tk.RIGHT, padx=2)
    ttk.Button(edit_btn_frame, text='清空编辑', command=self.cmd_clear_edit, width=12).pack(side=tk.RIGHT, padx=2)

    # ====== 第三区域：底部 - 命令列表 ======
    bottom_frame = ttk.LabelFrame(tab, text='命令列表')
    bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(2, 5))

    list_source_frame = tk.Frame(bottom_frame)
    list_source_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
    self.cmd_list_source_label = tk.Label(list_source_frame, text='[本地模式] 未加入工作组', fg='gray', font=('Arial', 9))
    self.cmd_list_source_label.pack(side=tk.LEFT)

    # 命令列表Treeview
    tree_frame = ttk.Frame(bottom_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    cmd_columns = ('index', 'enabled', 'name', 'coords', 'workflows', 'exec_mode', 'countdown', 'status')
    self.cmd_tree = ttk.Treeview(tree_frame, columns=cmd_columns, show='headings', height=6)
    self.cmd_tree.heading('index', text='#')
    self.cmd_tree.column('index', width=30, anchor='center')
    self.cmd_tree.heading('enabled', text='启用')
    self.cmd_tree.column('enabled', width=50, anchor='center')
    self.cmd_tree.heading('name', text='命令名称')
    self.cmd_tree.column('name', width=100, anchor='center')
    self.cmd_tree.heading('coords', text='坐标')
    self.cmd_tree.column('coords', width=150, anchor='w')
    self.cmd_tree.heading('workflows', text='工作流')
    self.cmd_tree.column('workflows', width=100, anchor='w')
    self.cmd_tree.heading('exec_mode', text='执行模式')
    self.cmd_tree.column('exec_mode', width=70, anchor='center')
    self.cmd_tree.heading('countdown', text='倒计时')
    self.cmd_tree.column('countdown', width=80, anchor='center')
    self.cmd_tree.heading('status', text='状态')
    self.cmd_tree.column('status', width=60, anchor='center')

    tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.cmd_tree.yview)
    self.cmd_tree.configure(yscrollcommand=tree_scroll.set)
    self.cmd_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # 绑定选中事件
    self.cmd_tree.bind('<<TreeviewSelect>>', self._on_cmd_tree_select)

    # 绑定启用/禁用复选框点击事件
    self.cmd_tree.bind('<Button-1>', self._on_cmd_tree_toggle)

    # 绑定双击事件 - 立即执行选中的命令
    self.cmd_tree.bind('<Double-Button-1>', self._on_cmd_tree_double_click)

    # 命令列表操作按钮(分两行)
    list_btn_frame1 = ttk.Frame(bottom_frame)
    list_btn_frame1.pack(fill=tk.X, padx=5, pady=2)

    ttk.Button(list_btn_frame1, text='添加', command=self.cmd_add_command, width=8).pack(side=tk.LEFT, padx=2)
    ttk.Button(list_btn_frame1, text='编辑', command=self.cmd_edit_command, width=8).pack(side=tk.LEFT, padx=2)
    ttk.Button(list_btn_frame1, text='删除', command=self.cmd_delete_command, width=8).pack(side=tk.LEFT, padx=2)

    ttk.Separator(list_btn_frame1, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

    ttk.Button(list_btn_frame1, text='全部执行', command=self.cmd_execute_all,
        width=10).pack(side=tk.LEFT, padx=2)
    ttk.Button(list_btn_frame1, text='全部暂停', command=self.cmd_pause_all,
        width=10).pack(side=tk.LEFT, padx=2)
    ttk.Button(list_btn_frame1, text='全部继续', command=self.cmd_resume_all,
        width=10).pack(side=tk.LEFT, padx=2)

    list_btn_frame2 = ttk.Frame(bottom_frame)
    list_btn_frame2.pack(fill=tk.X, padx=5, pady=(2, 5))

    # 全部停止按钮 - 红色样式
    self.cmd_stop_all_btn = tk.Button(list_btn_frame2, text='全部停止', command=self.cmd_stop_all,
        width=10, bg='#FF4444', fg='white', activebackground='#CC0000', activeforeground='white')
    self.cmd_stop_all_btn.pack(side=tk.LEFT, padx=2)

    ttk.Button(list_btn_frame2, text='保存列表', command=self.cmd_save_list,
        width=10).pack(side=tk.LEFT, padx=2)
    ttk.Button(list_btn_frame2, text='加载任务', command=self.cmd_load_list,
        width=10).pack(side=tk.LEFT, padx=2)

    ttk.Separator(list_btn_frame2, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

    self.cmd_clear_all_btn = tk.Button(list_btn_frame2, text='全部清空', command=self.cmd_clear_all,
        width=10, bg='#FF4444', fg='white', activebackground='#CC0000', activeforeground='white')
    self.cmd_clear_all_btn.pack(side=tk.LEFT, padx=2)

    ttk.Separator(list_btn_frame2, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8)

    ttk.Button(list_btn_frame2, text='同步刷新', command=self._sync_workgroup_files,
        width=10).pack(side=tk.LEFT, padx=2)

    # 工作组状态显示
    self.wg_status_label = ttk.Label(list_btn_frame2, text='未加入工作组', foreground='gray')
    self.wg_status_label.pack(side=tk.LEFT, padx=5)

    # 工作组按钮行3
    list_btn_frame3 = ttk.Frame(bottom_frame)
    list_btn_frame3.pack(fill=tk.X, padx=5, pady=(2, 5))

    ttk.Button(list_btn_frame3, text='创建工作组', command=self.wg_create_dialog,
        width=12).pack(side=tk.LEFT, padx=2)
    ttk.Button(list_btn_frame3, text='管理工作组', command=self.wg_manage_dialog,
        width=12).pack(side=tk.LEFT, padx=2)
    ttk.Button(list_btn_frame3, text='加入工作组', command=self.wg_join_dialog,
        width=12).pack(side=tk.LEFT, padx=2)
    self.wg_disable_btn = tk.Button(list_btn_frame3, text='暂断3小时', command=self.wg_pause_control,
        width=12, bg='#44CC44', fg='white', activebackground='#33AA33', activeforeground='white')
    self.wg_disable_btn.pack(side=tk.LEFT, padx=2)
    ttk.Button(list_btn_frame3, text='退出工作组', command=self.wg_leave,
        width=12).pack(side=tk.LEFT, padx=2)

    # 工作组内部状态
    self.wg_info = {}  # 当前工作组信息 {id, name, role, sync_dir, last_sync, disabled}
    self._wg_sync_timer = None  # 同步定时器ID

    # 刷新模板按钮和工作流下拉
    self.cmd_refresh_template_buttons()
    self.cmd_refresh_workflow_combo()

    # 启动倒计时刷新定时器
    self._start_countdown_timer()


def _on_exec_mode_changed(self, *args):
    """执行模式变化时更新提示"""
    import datetime
    mode = self.cmd_exec_mode_var.get()
    if mode == 'immediate':
        self.cmd_time_entry.config(state='disabled')
        self.cmd_time_label.config(text='(等待3秒后执行)')
    elif mode == 'scheduled':
        self.cmd_time_entry.config(state='normal')
        self.cmd_time_entry.delete(0, tk.END)
        scheduled_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
        self.cmd_time_entry.insert(0, scheduled_time.strftime('%H:%M:%S'))
        self.cmd_time_label.config(text='(定时执行)')
    elif mode == 'delayed':
        self.cmd_time_entry.config(state='normal')
        self.cmd_time_entry.delete(0, tk.END)
        self.cmd_time_entry.insert(0, '00:00:10')
        self.cmd_time_label.config(text='(延时执行)')


# ==================== 模板管理 ====================

def _load_command_templates(self):
    """从文件加载自定义模板,与内置模板合并"""
    self.cmd_templates = copy.deepcopy(BUILTIN_COMMAND_TEMPLATES)
    template_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'command_templates.json')
    if os.path.exists(template_file):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                custom_templates = json.load(f)
            for name, tpl in custom_templates.items():
                self.cmd_templates[name] = tpl
        except Exception as e:
            print(f"加载自定义命令模板失败: {e}")


def _save_command_templates(self):
    """保存自定义模板到文件"""
    template_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'command_templates.json')
    custom = {}
    for name, tpl in self.cmd_templates.items():
        if name not in BUILTIN_COMMAND_TEMPLATES:
            custom[name] = tpl
    try:
        if not custom:
            print(f"[DEBUG] 没有自定义模板需要保存，跳过")
            return
        import shutil
        if os.path.exists(template_file):
            shutil.copy2(template_file, template_file + '.bak')
        os.makedirs(os.path.dirname(template_file), exist_ok=True)
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(custom, f, ensure_ascii=False, indent=2)
        self.cmd_refresh_workflow_combo()
    except Exception as e:
        print(f"保存自定义命令模板失败: {e}")


def cmd_backup_all_templates(self):
    """保存全部模板到备份文件"""
    import shutil
    from datetime import datetime
    
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'template_backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'templates_backup_{timestamp}.json')
    
    try:
        all_templates = copy.deepcopy(self.cmd_templates)
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(all_templates, f, ensure_ascii=False, indent=2)
        messagebox.showinfo('成功', f'全部模板已备份到:\n{backup_file}', parent=self.root)
        if hasattr(self, 'add_status_message'):
            self.add_status_message(f'模板备份成功: {backup_file}')
    except Exception as e:
        messagebox.showerror('错误', f'备份模板失败: {e}', parent=self.root)


def cmd_restore_all_templates(self):
    """从备份文件恢复全部模板"""
    from tkinter import filedialog
    
    backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'template_backups')
    if not os.path.exists(backup_dir):
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    backup_file = filedialog.askopenfilename(
        title='选择模板备份文件',
        defaultextension='.json',
        filetypes=[('JSON文件', '*.json'), ('所有文件', '*.*')],
        initialdir=backup_dir
    )
    
    if not backup_file:
        return
    
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            restored_templates = json.load(f)
        
        if not restored_templates:
            messagebox.showwarning('警告', '备份文件中没有模板数据', parent=self.root)
            return
        
        self.cmd_templates = restored_templates
        
        self._save_command_templates()
        self.cmd_refresh_template_buttons()
        self.cmd_refresh_workflow_combo()
        
        messagebox.showinfo('成功', f'已恢复 {len(restored_templates)} 个模板', parent=self.root)
        if hasattr(self, 'add_status_message'):
            self.add_status_message(f'模板恢复成功: {len(restored_templates)} 个模板')
    except Exception as e:
        messagebox.showerror('错误', f'恢复模板失败: {e}', parent=self.root)


def cmd_refresh_template_buttons(self):
    """刷新顶部模板按钮"""
    for widget in self.cmd_template_inner.winfo_children():
        widget.destroy()

    self.cmd_template_buttons = {}
    for name, tpl in self.cmd_templates.items():
        btn = tk.Button(self.cmd_template_inner, text=name,
            command=lambda n=name: self.cmd_use_template(n), width=8,
            relief=tk.RAISED, bd=2)
        btn.pack(side=tk.LEFT, padx=2, pady=2)
        btn.bind('<Double-Button-1>', lambda e, n=name: self.cmd_edit_template_code(n))
        self.cmd_template_buttons[name] = btn

    self.cmd_refresh_workflow_combo()


def cmd_refresh_workflow_combo(self):
    """刷新模板下拉列表"""
    all_items = []

    if hasattr(self, 'cmd_templates'):
        all_items = list(self.cmd_templates.keys())

    unique_items = []
    seen = set()
    for item in all_items:
        if item not in seen:
            unique_items.append(item)
            seen.add(item)

    self.cmd_workflow_combo['values'] = unique_items


def cmd_use_template(self, template_name):
    """使用模板填充编辑区"""
    if template_name not in self.cmd_templates:
        return

    tpl = self.cmd_templates[template_name]
    template_data = tpl.get('template', copy.deepcopy(BUILTIN_COMMAND_TEMPLATES.get(template_name, {}).get('template', {})))

    self.cmd_clear_edit()

    if hasattr(self, 'cmd_template_buttons'):
        for n, btn in self.cmd_template_buttons.items():
            btn.configure(relief=tk.RAISED, bg=self.root.cget('bg'))
        if template_name in self.cmd_template_buttons:
            self.cmd_template_buttons[template_name].configure(relief=tk.SUNKEN, bg='#87CEEB')

    self.cmd_current_template_name = template_name

    coords = template_data.get('coords', [])
    for coord in coords:
        label = coord.get('label', f'坐标{len(self.cmd_coord_listbox.get(0, tk.END)) + 1}')
        x = coord.get('x', 0)
        y = coord.get('y', 0)
        raw = coord.get('raw', f'{x:.0f}.{y:.0f}')
        # 如果标签包含"文本参数"，显示原始文本而非坐标
        if '文本参数' in label:
            self.cmd_coord_listbox.insert(tk.END, f'{label}: {raw}')
        else:
            self.cmd_coord_listbox.insert(tk.END, f'{label}: {x:.0f}.{y:.0f}')

    self.cmd_auto_input_var.set(tpl.get('has_auto_input', False))

    self.cmd_exec_mode_var.set(template_data.get('exec_mode', 'immediate'))

    for wf in template_data.get('workflows', []):
        self.cmd_workflow_listbox.insert(tk.END, wf)

    if hasattr(self, 'add_status_message'):
        self.add_status_message(f"已加载模板: {template_name}")


def cmd_edit_template_code(self, template_name):
    """编辑模板的Python代码"""
    if template_name not in self.cmd_templates:
        return
    
    tpl = self.cmd_templates[template_name]
    
    dialog = tk.Toplevel(self.root)
    dialog.title(f'编辑模板代码 - {template_name}')
    dialog.geometry('900x700')
    dialog.transient(self.root)
    dialog.grab_set()
    
    ttk.Label(dialog, text=f'模板名称: {template_name}', font=('', 11, 'bold')).pack(pady=5)
    
    hint_frame = ttk.Frame(dialog)
    hint_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
    ttk.Label(hint_frame, text='提示: coords变量包含坐标[x1,y1,x2,y2...]，可用dir()查看', 
              foreground='blue').pack(side=tk.LEFT)
    
    code_frame = ttk.Frame(dialog)
    code_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    code_text = scrolledtext.ScrolledText(code_frame, font=('Consolas', 10), wrap=tk.NONE)
    code_text.pack(fill=tk.BOTH, expand=True)
    
    python_code = tpl.get('python_code', '')
    if python_code:
        code_text.insert(tk.END, python_code)
    
    def on_save():
        new_code = code_text.get('1.0', tk.END).strip()
        self.cmd_templates[template_name]['python_code'] = new_code
        self.cmd_templates[template_name]['is_python_template'] = True
        self.cmd_templates[template_name]['type'] = 'python_script'
        self._save_command_templates()
        dialog.destroy()
        messagebox.showinfo('成功', f'模板"{template_name}"代码已保存', parent=self.root)
    
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(fill=tk.X, padx=10, pady=5)
    
    ttk.Button(btn_frame, text='确定保存', command=on_save, width=12).pack(side=tk.RIGHT, padx=5)
    ttk.Button(btn_frame, text='取消', command=dialog.destroy, width=12).pack(side=tk.RIGHT, padx=5)


def cmd_new_template(self):
    """新建命令模板"""
    self.cmd_template_dialog(title='新建命令模板', template=None)


def cmd_copy_template(self):
    """复制命令模板"""
    selected_name = simpledialog.askstring('复制模板', '请输入要复制的模板名称:',
        parent=self.root)
    if not selected_name or selected_name not in self.cmd_templates:
        messagebox.showwarning('提示', '请输入有效的模板名称', parent=self.root)
        return

    original = self.cmd_templates[selected_name]
    new_name = simpledialog.askstring('复制模板', '请输入新模板名称:', parent=self.root)
    if not new_name:
        return
    if new_name in self.cmd_templates:
        messagebox.showwarning('提示', f'模板"{new_name}"已存在', parent=self.root)
        return

    self.cmd_templates[new_name] = copy.deepcopy(original)
    self._save_command_templates()
    self.cmd_refresh_template_buttons()
    messagebox.showinfo('成功', f'已复制模板"{selected_name}"为"{new_name}"', parent=self.root)


def cmd_delete_template(self):
    """删除命令模板"""
    selected_name = simpledialog.askstring('删除模板', '请输入要删除的模板名称:',
        parent=self.root)
    if not selected_name or selected_name not in self.cmd_templates:
        messagebox.showwarning('提示', '请输入有效的模板名称', parent=self.root)
        return

    if selected_name in BUILTIN_COMMAND_TEMPLATES:
        messagebox.showwarning('提示', '内置模板不能删除', parent=self.root)
        return

    if messagebox.askyesno('确认删除', f'确定要删除模板"{selected_name}"吗？', parent=self.root):
        del self.cmd_templates[selected_name]
        self._save_command_templates()
        self.cmd_refresh_template_buttons()
        messagebox.showinfo('成功', f'已删除模板"{selected_name}"', parent=self.root)


def cmd_template_dialog(self, title='编辑命令模板', template=None):
    """模板编辑弹窗"""
    dialog = tk.Toplevel(self.root)
    dialog.title(title)
    dialog.geometry('500x450')
    dialog.transient(self.root)
    dialog.grab_set()

    # 模板名称
    name_frame = ttk.Frame(dialog)
    name_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Label(name_frame, text='模板名称:').pack(side=tk.LEFT)
    name_var = tk.StringVar(value=template.get('name', '') if template else '')
    name_entry = ttk.Entry(name_frame, textvariable=name_var, width=30)
    name_entry.pack(side=tk.LEFT, padx=5)

    # 模板描述
    desc_frame = ttk.Frame(dialog)
    desc_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Label(desc_frame, text='描述:').pack(side=tk.LEFT)
    desc_var = tk.StringVar(value=template.get('description', '') if template else '')
    desc_entry = ttk.Entry(desc_frame, textvariable=desc_var, width=40)
    desc_entry.pack(side=tk.LEFT, padx=5)

    # 是否多参数
    multi_var = tk.BooleanVar(value=template.get('has_multi_coords', True) if template else True)
    ttk.Checkbutton(desc_frame, text='支持多参数', variable=multi_var).pack(side=tk.LEFT, padx=10)

    # 是否自动输入参数
    auto_var = tk.BooleanVar(value=template.get('has_auto_input', False) if template else False)
    ttk.Checkbutton(desc_frame, text='自动输入参数', variable=auto_var).pack(side=tk.LEFT, padx=5)

    # 默认参数数量
    default_template = template.get('template', {
        'coords': [{'x': 0, 'y': 0, 'label': '参数1'}],
        'workflows': [],
        'exec_mode': 'immediate'
    }) if template else {
        'coords': [{'x': 0, 'y': 0, 'label': '参数1'}],
        'workflows': [],
        'exec_mode': 'immediate'
    }

    # 参数数量设置
    coord_count_frame = ttk.Frame(dialog)
    coord_count_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Label(coord_count_frame, text='默认参数数量:').pack(side=tk.LEFT)
    coord_count_var = tk.StringVar(value=str(len(default_template.get('coords', []))))
    ttk.Entry(coord_count_frame, textvariable=coord_count_var, width=5).pack(side=tk.LEFT, padx=5)

    def on_save():
        name = name_var.get().strip()
        if not name:
            messagebox.showwarning('提示', '请输入模板名称', parent=dialog)
            return
        try:
            count = int(coord_count_var.get())
            count = max(1, min(count, 50))
        except ValueError:
            count = 1

        self.cmd_templates[name] = {
            'type': 'custom',
            'description': desc_var.get().strip(),
            'has_multi_coords': multi_var.get(),
            'has_auto_input': auto_var.get(),
            'template': {
                'coords': [{'x': 0, 'y': 0, 'label': f'坐标{i+1}'} for i in range(count)],
                'workflows': [],
                'exec_mode': 'immediate'
            }
        }
        self._save_command_templates()
        self.cmd_refresh_template_buttons()
        dialog.destroy()
        messagebox.showinfo('成功', f'模板"{name}"已保存', parent=self.root)

    ttk.Button(dialog, text='保存', command=on_save, width=10).pack(pady=10)


# ==================== 编辑区操作 ====================

def cmd_add_coord(self):
    """添加参数"""
    idx = len(self.cmd_coord_listbox.get(0, tk.END)) + 1
    coord_str = f'参数{idx}: 0.0'
    self.cmd_coord_listbox.insert(tk.END, coord_str)
    self.cmd_coord_listbox.selection_set(tk.END)


def cmd_remove_coord(self):
    """删除选中的坐标"""
    selection = self.cmd_coord_listbox.curselection()
    if not selection:
        messagebox.showinfo('提示', '请先选择要删除的坐标', parent=self.root)
        return
    self.cmd_coord_listbox.delete(selection[0])
    # 重新编号
    for i in range(self.cmd_coord_listbox.size()):
        text = self.cmd_coord_listbox.get(i)
        parts = text.split(':')
        if len(parts) >= 2:
            coord_info = parts[1].strip()
            self.cmd_coord_listbox.delete(i)
            self.cmd_coord_listbox.insert(i, f'坐标{i+1}: {coord_info}')


def cmd_pick_coord(self):
    """输入参数"""
    selection = self.cmd_coord_listbox.curselection()
    if not selection:
        messagebox.showinfo('提示', '请先选择要拾取的坐标行', parent=self.root)
        return

    idx = selection[0]
    current_text = self.cmd_coord_listbox.get(idx)
    
    # 检查是否是"文本参数"标签
    if '文本参数' in current_text:
        # 文本参数模式：直接输入文本，不解析为坐标
        label_part = current_text.split(':')[0] if ':' in current_text else f'文本参数{idx + 1}'
        text_input = simpledialog.askstring('输入文本参数',
            '请输入文本参数:', parent=self.root)
        if text_input:
            self.cmd_coord_listbox.delete(idx)
            self.cmd_coord_listbox.insert(idx, f'{label_part}: {text_input}')
            self.cmd_coord_listbox.selection_set(idx)
        return
    
    # 文本模式：直接保存文本，不转换格式
    text_input = simpledialog.askstring('输入文本参数',
        '请输入文本参数 (样式: 0.0):\n例: 500.300', parent=self.root)
    if text_input:
        label = f'文本参数{idx + 1}'
        self.cmd_coord_listbox.delete(idx)
        self.cmd_coord_listbox.insert(idx, f'{label}: {text_input.strip()}')
        self.cmd_coord_listbox.selection_set(idx)


def cmd_add_workflow(self):
    """添加工作流到已选列表"""
    wf_name = self.cmd_workflow_combo.get()
    if not wf_name:
        messagebox.showinfo('提示', '请先选择一个工作流', parent=self.root)
        return
    self.cmd_workflow_listbox.insert(tk.END, wf_name)


def cmd_remove_workflow(self):
    """从已选列表移除工作流"""
    selection = self.cmd_workflow_listbox.curselection()
    if not selection:
        messagebox.showinfo('提示', '请先选择要移除的工作流', parent=self.root)
        return
    self.cmd_workflow_listbox.delete(selection[0])


def cmd_confirm_edit(self):
    """确认保存编辑内容到命令列表"""
    cmd_data = self._collect_edit_data()
    if not cmd_data:
        return

    is_new_cmd = self.cmd_selected_index is None or self.cmd_selected_index >= len(self.cmd_list)

    if is_new_cmd:
        self.cmd_selected_index = None
        self.cmd_list.append(cmd_data)
        if hasattr(self, 'add_status_message'):
            self.add_status_message(f"已添加命令: {cmd_data['name']}")
    else:
        idx = self.cmd_selected_index
        old_cmd = self.cmd_list[idx]
        
        cmd_data['name'] = old_cmd.get('name', cmd_data['name'])
        cmd_data['status'] = CMD_STATUS_PENDING
        cmd_data['enabled'] = True
        cmd_data['local_modified_time'] = datetime.datetime.now().isoformat()
        cmd_data['countdown_start_time'] = datetime.datetime.now()
        
        self.cmd_list[idx] = cmd_data
        if hasattr(self, 'add_status_message'):
            self.add_status_message(f"已更新命令: {cmd_data['name']}，状态已重置为待执行")

    self.cmd_refresh_tree()
    self._update_cmd_list_source()
    self.cmd_selected_index = None

    if self.wg_info.get('id') and self.wg_info.get('role') in ('owner', 'admin'):
        self._save_shared_commands()

    self._start_countdown_timer()


def _execute_cmd_by_name(self, cmd_name):
    """根据命令名称执行命令"""
    for i, cmd in enumerate(self.cmd_list):
        if cmd.get('name') == cmd_name:
            self._execute_cmd_by_index(i)
            break


def _execute_cmd_by_index(self, idx):
    """根据索引执行命令"""
    if idx < 0 or idx >= len(self.cmd_list):
        return
    cmd = self.cmd_list[idx]
    if not cmd.get('enabled', True):
        return
    import threading
    thread = threading.Thread(target=self._execute_single_command, args=(cmd,), daemon=True)
    thread.start()


def cmd_edit_selected_template(self):
    """编辑当前选中的模板代码"""
    template_name = getattr(self, 'cmd_current_template_name', None)
    if not template_name:
        messagebox.showinfo('提示', '请先选择一个模板（点击模板按钮）', parent=self.root)
        return

    if template_name not in self.cmd_templates:
        messagebox.showwarning('提示', f'未找到模板"{template_name}"', parent=self.root)
        return

    tpl = self.cmd_templates[template_name]

    python_code = tpl.get('python_code', '')
    
    dialog = tk.Toplevel(self.root)
    dialog.title(f'编辑模板代码 - {template_name}')
    dialog.geometry('900x700')
    dialog.transient(self.root)
    dialog.grab_set()

    info_frame = ttk.Frame(dialog)
    info_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Label(info_frame, text=f'模板名称: {template_name}', font=('', 11, 'bold')).pack(side=tk.LEFT)
    ttk.Label(info_frame, text=f'  |  类型: {tpl.get("type", "未知")}', font=('', 10)).pack(side=tk.LEFT)
    ttk.Label(info_frame, text=f'  |  代码长度: {len(python_code)} 字符', font=('', 10)).pack(side=tk.LEFT)

    hint_frame = ttk.Frame(dialog)
    hint_frame.pack(fill=tk.X, padx=10, pady=(0, 5))
    ttk.Label(hint_frame, text='提示: 修改代码后点击"确定保存"更新模板。coords变量包含坐标列表[x1,y1,x2,y2...]，可用dir()查看', 
              foreground='blue').pack(side=tk.LEFT)

    code_frame = ttk.Frame(dialog)
    code_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    code_text = scrolledtext.ScrolledText(code_frame, font=('Consolas', 10), wrap=tk.NONE)
    code_text.pack(fill=tk.BOTH, expand=True)

    if python_code:
        code_text.insert(tk.END, python_code)
    else:
        default_template_code = '''import os
import time
import pyautogui
import numpy as np
import cv2

print("="*50)
print("【调动模块】开始执行")
print("="*50)

workgroup_id = '{{workgroup_id}}'
coord_params = '{{coord_params}}'

primary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'workgroups', workgroup_id)
secondary_pic_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '3MCWB', 'pic')

print(f"[DEBUG] workgroup_id={workgroup_id}")
print(f"[DEBUG] primary_pic_dir={primary_pic_dir}")
print(f"[DEBUG] secondary_pic_dir={secondary_pic_dir}")

def find_image_click(image_name, wait_time=1):
    image_path = None
    path1 = os.path.join(primary_pic_dir, image_name)
    print(f"[DEBUG] path1={path1}, exists={os.path.exists(path1)}")
    if os.path.exists(path1):
        image_path = path1
        print(f"[图片查找] 找到文件: {path1}")
    if not image_path:
        path2 = os.path.join(secondary_pic_dir, image_name)
        print(f"[DEBUG] path2={path2}, exists={os.path.exists(path2)}")
        if os.path.exists(path2):
            image_path = path2
            print(f"[图片查找] 找到文件(备用路径): {path2}")
    if not image_path:
        print(f"[图片查找] 未找到图片: {image_name}")
        return False
    print(f'[图片查找] 查找图片: {image_name}')
    screenshot = pyautogui.screenshot()
    screen_np = np.array(screenshot)
    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
    template = cv2.imread(image_path)
    if template is None:
        print(f'[图片查找] 无法读取图片: {image_name}')
        return False
    result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    if max_val >= 0.8:
        h, w = template.shape[:2]
        center_x = max_loc[0] + w // 2
        center_y = max_loc[1] + h // 2
        print(f'[图片查找] 找到图片 {image_name}，坐标: ({center_x}, {center_y})')
        pyautogui.click(center_x, center_y)
        print(f'[图片查找] 点击坐标: ({center_x}, {center_y})')
        if wait_time > 0:
            print(f'[图片查找] 等待 {wait_time} 秒...')
            time.sleep(wait_time)
        return True
    else:
        print(f'[图片查找] 未找到图片 {image_name}，相似度: {max_val:.3f}')
        return False

found_any = find_image_click('1-ST.png', 0) or find_image_click('1-FD.png', 0) or find_image_click('1-HC.png', 0)

if found_any:
    print("[条件成立] 找到1-ST/1-FD/1-HC图片，执行2.1-2.36操作")
    print("[2.1] 点击坐标36,522")
    pyautogui.click(36, 522)
    time.sleep(1)
    print("[2.2] 等待1秒")
    print("[2.3] 点击坐标36,522")
    pyautogui.click(36, 522)
    time.sleep(1)
    print("[2.4] 等待1秒")
    print("[2.5] 点击坐标36,522")
    pyautogui.click(36, 522)
    time.sleep(1)
    print("[2.6] 等待1秒")
    print("[2.7] 点击坐标36,522")
    pyautogui.click(36, 522)
    time.sleep(1)
    print("[2.8] 等待1秒")
    print("[2.9] 点击坐标36,522")
    pyautogui.click(36, 522)
    time.sleep(1)
    print("[2.10] 等待1秒")
    print("[2.11] 点击坐标36,522")
    pyautogui.click(36, 522)
    time.sleep(1)
    print("[2.12] 等待1秒")
    print("[2.13] 点击坐标955,715")
    pyautogui.click(955, 715)
    time.sleep(1)
    print("[2.14] 等待1秒")
    print(f"[键盘输入] 使用pynput.keyboard输入参数: {coord_params}")
    from pynput.keyboard import Controller
    kb = Controller()
    kb.type(coord_params)
    time.sleep(1)
    print("[2.21] 点击坐标1240,708")
    pyautogui.click(1240, 708)
    time.sleep(1)
    print("[2.22] 等待1秒")
    print("[2.23] 点击坐标1158,718")
    pyautogui.click(1158, 718)
    time.sleep(2)
    print("[2.24] 等待2秒")
    print("[2.25] 点击坐标666,386")
    pyautogui.click(666, 386)
    time.sleep(1)
    print("[2.26] 等待1秒")
    find_image_click('1-DD.png', 1)
    time.sleep(1)
    print("[2.32] 等待1秒")
    if find_image_click('1-CZ.png', 1):
        print("[标记] 已找到1-CZ.png并点击，命令执行成功，退出脚本")
        print("="*50)
        print("【调动模块】执行完成!")
        print("="*50)
        exit(0)
    time.sleep(1)
    print("[2.34] 等待1秒")
    find_image_click('1-CZ.png', 2)
    print("[2.36] 等待2秒")
else:
    print("[条件不成立] 未找到1-ST/1-FD/1-HC图片，执行2.37-2.43操作")
    print("[2.37] 点击坐标67,700")
    pyautogui.click(67, 700)
    time.sleep(2)
    print("[2.38] 等待2秒")
    find_image_click('1-TC.png', 4)
    time.sleep(1)
    print("[2.40] 等待1秒")
    find_image_click('1-TC.png', 1)
    time.sleep(1)
    print("[2.42] 等待1秒")
    find_image_click('1-CC.png', 4)

print("="*50)
print("【调动模块】执行完成!")
print("="*50)
'''
        code_text.insert(tk.END, default_template_code)
        tpl['python_code'] = default_template_code

    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(fill=tk.X, padx=10, pady=5)

    def on_save():
        new_code = code_text.get('1.0', tk.END).strip()
        self.cmd_templates[template_name]['python_code'] = new_code
        self.cmd_templates[template_name]['is_python_template'] = True
        self.cmd_templates[template_name]['type'] = 'python_script'
        self._save_command_templates()
        dialog.destroy()
        messagebox.showinfo('成功', f'模板"{template_name}"代码已更新', parent=self.root)
        if hasattr(self, 'add_status_message'):
            self.add_status_message(f'已更新模板"{template_name}"的代码')

    ttk.Button(btn_frame, text='确定保存', command=on_save, width=12).pack(side=tk.RIGHT, padx=5)
    ttk.Button(btn_frame, text='取消', command=dialog.destroy, width=12).pack(side=tk.RIGHT, padx=5)


def cmd_clear_edit(self):
    """清空编辑区"""
    self.cmd_coord_listbox.delete(0, tk.END)
    self.cmd_workflow_listbox.delete(0, tk.END)
    self.cmd_auto_input_var.set(False)
    self.cmd_exec_mode_var.set('scheduled')
    self.cmd_time_entry.delete(0, tk.END)
    self.cmd_time_entry.insert(0, "00:05:00")
    self.cmd_selected_index = None
    self.cmd_current_template_name = None


def _collect_edit_data(self):
    """从编辑区收集命令数据"""
    coords = []
    for i in range(self.cmd_coord_listbox.size()):
        text = self.cmd_coord_listbox.get(i)
        try:
            if ':' in text:
                label_part = text.split(':', 1)[0].strip()
                coord_part = text.split(':', 1)[1].strip()
            else:
                label_part = f'坐标{i + 1}'
                coord_part = text
            
            # 如果标签包含"文本参数"，只保留原始文本，不解析为坐标
            if '文本参数' in label_part:
                coords.append({'raw': coord_part})
                continue
            
            coord_part = coord_part.replace('，', '.').replace(',', '.').replace(' ', '.')
            parts = coord_part.split('.')
            x = float(parts[0].strip())
            y = float(parts[1].strip()) if len(parts) > 1 else 0.0
            
            label = f'坐标{i + 1}'
            raw_value = parts[0].strip() + '.' + parts[1].strip()
            coords.append({'x': x, 'y': y, 'label': label, 'raw': raw_value})
        except (ValueError, IndexError):
            messagebox.showerror('错误', f'坐标格式不正确: {text}', parent=self.root)
            return None

    if not coords:
        messagebox.showwarning('提示', '请至少添加一个坐标', parent=self.root)
        return None

    workflows = []
    for i in range(self.cmd_workflow_listbox.size()):
        workflows.append(self.cmd_workflow_listbox.get(i))

    exec_mode = self.cmd_exec_mode_var.get()
    exec_time = ''
    if exec_mode in ('scheduled', 'delayed'):
        exec_time = self.cmd_time_entry.get().strip()

    if self.cmd_selected_index is not None and self.cmd_selected_index < len(self.cmd_list):
        name = self.cmd_list[self.cmd_selected_index].get('name', f'命令{len(self.cmd_list) + 1}')
    else:
        name = f'命令{len(self.cmd_list) + 1}'

    result = {
        'name': name,
        'coords': coords,
        'workflows': workflows,
        'auto_input': self.cmd_auto_input_var.get(),
        'exec_mode': exec_mode,
        'exec_time': exec_time,
        'status': CMD_STATUS_PENDING,
        'enabled': True,
        'countdown_start_time': datetime.datetime.now()
    }
    
    if self.cmd_current_template_name:
        result['template_name'] = self.cmd_current_template_name
        tpl = self.cmd_templates.get(self.cmd_current_template_name, {})
        if tpl.get('is_python_template') and tpl.get('python_code'):
            result['python_code'] = tpl.get('python_code')
        else:
            result['python_code'] = None
    
    return result


def _format_coords_text(self, coords):
    """格式化参数显示文本"""
    if not coords:
        return ''
    parts = []
    for c in coords:
        # 文本参数格式：只有 raw 字段
        if 'raw' in c and 'x' not in c:
            parts.append(c['raw'])
        # 坐标格式：有 x, y 字段
        elif 'x' in c and 'y' in c:
            parts.append(f"{c['x']:.0f}.{c['y']:.0f}")
        else:
            parts.append(c.get('raw', '0.0'))
    return ' '.join(parts)


def _format_exec_mode_text(self, cmd):
    """格式化执行模式显示文本（含倒计时）"""
    mode = cmd.get('exec_mode', 'immediate')
    if mode == 'immediate':
        remaining = self._get_remaining_seconds(cmd)
        if remaining > 0 and remaining < 999999:
            return f"立即 {remaining}秒"
        return '立即'
    elif mode == 'scheduled':
        exec_time = cmd.get('exec_time', '')
        countdown = self._get_countdown_text(exec_time, mode)
        return f"定时 {countdown}"
    elif mode == 'delayed':
        exec_time = cmd.get('exec_time', '')
        countdown = self._get_countdown_text(exec_time, mode)
        return f"延时 {countdown}"
    return mode


def _get_countdown_text(self, exec_time, mode):
    """获取倒计时文本"""
    try:
        parts = exec_time.split(':')
        target_h = int(parts[0])
        target_m = int(parts[1])
        target_s = int(parts[2]) if len(parts) > 2 else 0

        if mode == 'delayed':
            total_seconds = target_h * 3600 + target_m * 60 + target_s
            return exec_time
        else:
            now = datetime.datetime.now()
            target = now.replace(hour=target_h, minute=target_m, second=target_s, microsecond=0)

            if now > target:
                target = target.replace(day=now.day + 1)

            diff = target - now
            total_seconds = int(diff.total_seconds())
            if total_seconds < 0:
                return exec_time

            h = total_seconds // 3600
            m = (total_seconds % 3600) // 60
            s = total_seconds % 60
            return f"{h:02d}:{m:02d}:{s:02d}"
    except:
        return exec_time


def _format_exec_mode_short(self, cmd):
    """格式化执行模式简短文本"""
    mode = cmd.get('exec_mode', 'immediate')
    exec_time = cmd.get('exec_time', '')
    if mode == 'immediate':
        return '立即'
    elif mode == 'scheduled':
        return f"定时 {exec_time}"
    elif mode == 'delayed':
        return f"延时 {exec_time}"
    return mode


def _get_countdown_display(self, cmd):
    """获取倒计时显示文本"""
    status = cmd.get('status', CMD_STATUS_PENDING)
    if status == CMD_STATUS_COMPLETED:
        return '已执行'
    elif status == CMD_STATUS_EXECUTING:
        return '正在执行'
    elif status == CMD_STATUS_QUEUED:
        return '排队中'
    
    mode = cmd.get('exec_mode', 'immediate')
    if mode == 'immediate':
        return '-'
    elif mode in ('scheduled', 'delayed'):
        remaining = self._get_remaining_seconds(cmd)
        if remaining < 0:
            remaining = 0
        return f"{remaining}秒"
    return '-'


# ==================== 命令列表操作 ====================

def cmd_refresh_tree(self):
    """刷新命令列表Treeview"""
    for item in self.cmd_tree.get_children():
        self.cmd_tree.delete(item)

    print(f'[DEBUG] cmd_refresh_tree: 共 {len(self.cmd_list)} 条命令')
    for i, cmd in enumerate(self.cmd_list):
        status = cmd.get('status', CMD_STATUS_PENDING)
        status_text = CMD_STATUS_TEXT.get(status, status)
        enabled = '✓' if cmd.get('enabled', True) else '✗'
        countdown_text = self._get_countdown_display(cmd)
        cmd_name = cmd.get('name', f'命令{i+1}')
        print(f'[DEBUG] cmd[{i}] {cmd_name}: status={status_text}, enabled={enabled}')
        self.cmd_tree.insert('', tk.END, iid=str(i), values=(
            i + 1,
            enabled,
            cmd.get('name', f'命令{i+1}'),
            self._format_coords_text(cmd.get('coords', [])),
            ', '.join(cmd.get('workflows', [])) if cmd.get('workflows') else '无',
            self._format_exec_mode_short(cmd),
            countdown_text,
            status_text
        ))
        color = CMD_STATUS_COLORS.get(status, '#000000')
        self.cmd_tree.tag_configure(status, foreground=color)
        self.cmd_tree.item(str(i), tags=(status,))
        if not cmd.get('enabled', True):
            self.cmd_tree.item(str(i), tags=('disabled',))
            self.cmd_tree.tag_configure('disabled', foreground='#CCCCCC')


def _on_cmd_tree_select(self, event):
    """命令列表选中事件 - 将选中命令加载到编辑区"""
    selection = self.cmd_tree.selection()
    if not selection:
        return

    idx = int(selection[0])
    if idx >= len(self.cmd_list):
        return

    cmd = self.cmd_list[idx]
    self.cmd_selected_index = idx


def _on_cmd_tree_toggle(self, event):
    """点击启用/禁用列"""
    region = self.cmd_tree.identify_region(event.x, event.y)
    if region != 'cell':
        return

    column = self.cmd_tree.identify_column(event.x)
    if column != '#2':
        return

    selection = self.cmd_tree.selection()
    if not selection:
        return

    idx = int(selection[0])
    if idx >= len(self.cmd_list):
        return

    cmd = self.cmd_list[idx]
    cmd['enabled'] = not cmd.get('enabled', True)
    self.cmd_refresh_tree()


def _on_cmd_tree_select(self, event):
    """命令列表选中事件 - 将选中命令加载到编辑区"""
    selection = self.cmd_tree.selection()
    if not selection:
        return

    idx = int(selection[0])
    if idx >= len(self.cmd_list):
        return

    cmd = self.cmd_list[idx]
    self.cmd_selected_index = idx

    self.cmd_coord_listbox.delete(0, tk.END)
    self.cmd_workflow_listbox.delete(0, tk.END)

    for coord in cmd.get('coords', []):
        label = coord.get('label', '坐标')
        x = coord.get('x', 0)
        y = coord.get('y', 0)
        raw = coord.get('raw', f'{x:.0f}.{y:.0f}')
        # 如果标签包含"文本参数"，显示原始文本
        if '文本参数' in label:
            self.cmd_coord_listbox.insert(tk.END, f'{label}: {raw}')
        else:
            self.cmd_coord_listbox.insert(tk.END, f'{label}: {x:.0f}.{y:.0f}')

    for wf in cmd.get('workflows', []):
        self.cmd_workflow_listbox.insert(tk.END, wf)

    self.cmd_auto_input_var.set(cmd.get('auto_input', False))
    self.cmd_exec_mode_var.set(cmd.get('exec_mode', 'immediate'))
    if cmd.get('exec_time'):
        self.cmd_time_entry.delete(0, tk.END)
        self.cmd_time_entry.insert(0, cmd['exec_time'])

    template_name = cmd.get('template_name')
    self.cmd_current_template_name = template_name

    if hasattr(self, 'cmd_template_buttons'):
        for n, btn in self.cmd_template_buttons.items():
            btn.configure(relief=tk.RAISED, bg=self.root.cget('bg'))
        if template_name in self.cmd_template_buttons:
            self.cmd_template_buttons[template_name].configure(relief=tk.SUNKEN, bg='#87CEEB')


def _on_cmd_tree_double_click(self, event):
    """双击命令列表 - 立即执行命令"""
    selection = self.cmd_tree.selection()
    if not selection:
        print('[DEBUG 双击] 没有选中项')
        return

    idx = int(selection[0])
    print(f'[DEBUG 双击] 选中索引: {idx}, 命令列表长度: {len(self.cmd_list)}')
    if idx >= len(self.cmd_list):
        print('[DEBUG 双击] 索引超出范围')
        return

    cmd = self.cmd_list[idx]
    print(f'[DEBUG 双击] 命令: {cmd.get("name")}, enabled: {cmd.get("enabled", True)}')

    if not cmd.get('enabled', True):
        if hasattr(self, 'add_status_message'):
            self.add_status_message(f"命令已被禁用: {cmd.get('name', '')}")
        return

    if self.cmd_running:
        messagebox.showinfo('提示', '已有命令在执行中，请等待或停止当前执行', parent=self.root)
        return

    cmd['status'] = CMD_STATUS_EXECUTING
    self.cmd_refresh_tree()
    
    self._pause_sync_temporarily()

    if hasattr(self, 'add_status_message'):
        self.add_status_message(f"立即执行命令: {cmd.get('name', '')}")

    import threading
    def execute_single():
        print(f'[DEBUG 双击] 开始执行线程: {cmd.get("name")}')
        try:
            self._execute_single_command(cmd)
            cmd['status'] = CMD_STATUS_COMPLETED
            cmd['executed_time'] = datetime.datetime.now().isoformat()
            cmd['enabled'] = False
        except SystemExit as e:
            print(f'[DEBUG 双击] SystemExit (code: {e.code}): {cmd.get("name")}')
            cmd['status'] = CMD_STATUS_COMPLETED
            cmd['executed_time'] = datetime.datetime.now().isoformat()
            cmd['enabled'] = False
        except Exception as e:
            print(f'[DEBUG 双击] 异常: {e}')
            cmd['status'] = CMD_STATUS_COMPLETED
            cmd['executed_time'] = datetime.datetime.now().isoformat()
            cmd['enabled'] = False
        self._update_command_to_server(cmd)
        self.root.after(0, self.cmd_refresh_tree)
        self.root.after(0, lambda: self._update_cmd_status_message(f"命令 {cmd.get('name', '')} 执行完成"))
        print(f'[DEBUG 双击] 执行完成: {cmd.get("name")}')

    threading.Thread(target=execute_single, daemon=True).start()


def _open_cmd_code_editor(self, cmd, idx):
    """打开命令代码编辑窗口"""
    dialog = tk.Toplevel(self.root)
    dialog.title(f'编辑命令代码 - {cmd.get("name", "")}')
    dialog.geometry('800x650')
    dialog.transient(self.root)
    dialog.grab_set()
    
    info_frame = ttk.Frame(dialog)
    info_frame.pack(fill=tk.X, padx=10, pady=5)
    ttk.Label(info_frame, text=f'命令名称: {cmd.get("name", "")}', font=('', 11, 'bold')).pack(side=tk.LEFT)
    ttk.Label(info_frame, text=f'  |  模板: {cmd.get("template_name", "无")}', font=('', 10)).pack(side=tk.LEFT)
    
    code_frame = ttk.Frame(dialog)
    code_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    code_text = scrolledtext.ScrolledText(code_frame, font=('Consolas', 10), wrap=tk.NONE)
    code_text.pack(fill=tk.BOTH, expand=True)
    
    python_code = cmd.get('python_code')
    template_name = cmd.get('template_name', '')
    if not python_code and template_name and template_name in self.cmd_templates:
        python_code = self.cmd_templates[template_name].get('python_code', '')
    
    if python_code:
        code_text.insert(tk.END, python_code)
    
    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(fill=tk.X, padx=10, pady=5)
    
    def on_save_and_execute():
        new_code = code_text.get('1.0', tk.END).strip()
        cmd['python_code'] = new_code
        dialog.destroy()
        
        if self.cmd_running:
            messagebox.showinfo('提示', '已有命令在执行中，请等待或停止当前执行', parent=self.root)
            return
        
        cmd['status'] = CMD_STATUS_EXECUTING
        self.cmd_refresh_tree()
        
        self._pause_sync_temporarily()
        
        if hasattr(self, 'add_status_message'):
            self.add_status_message(f"立即执行命令: {cmd.get('name', '')}")
        
        import threading
        def execute_single():
            try:
                self._execute_single_command(cmd)
                cmd['status'] = CMD_STATUS_COMPLETED
                cmd['executed_time'] = datetime.datetime.now().isoformat()
                cmd['enabled'] = False
            except SystemExit as e:
                print(f'[DEBUG 保存执行] SystemExit (code: {e.code}): {cmd.get("name")}')
                cmd['status'] = CMD_STATUS_COMPLETED
                cmd['executed_time'] = datetime.datetime.now().isoformat()
                cmd['enabled'] = False
            except Exception as e:
                print(f'[DEBUG 保存执行] 异常: {e}')
                cmd['status'] = CMD_STATUS_COMPLETED
                cmd['executed_time'] = datetime.datetime.now().isoformat()
                cmd['enabled'] = False
            self._update_command_to_server(cmd)
            self.root.after(0, self.cmd_refresh_tree)
            self.root.after(0, lambda: self._update_cmd_status_message(f"命令 {cmd.get('name', '')} 执行完成"))

        threading.Thread(target=execute_single, daemon=True).start()
    
    def on_save_only():
        new_code = code_text.get('1.0', tk.END).strip()
        cmd['python_code'] = new_code
        dialog.destroy()
        if hasattr(self, 'add_status_message'):
            self.add_status_message(f"已保存命令代码: {cmd.get('name', '')}")
    
    ttk.Button(btn_frame, text='保存并执行', command=on_save_and_execute, width=12).pack(side=tk.RIGHT, padx=5)
    ttk.Button(btn_frame, text='仅保存', command=on_save_only, width=10).pack(side=tk.RIGHT, padx=5)
    ttk.Button(btn_frame, text='取消', command=dialog.destroy, width=10).pack(side=tk.RIGHT, padx=5)


def cmd_add_command(self):
    """添加新命令"""
    self.cmd_selected_index = None
    self.cmd_clear_edit()
    if hasattr(self, 'add_status_message'):
        self.add_status_message('请在编辑区编辑新命令,点击"确认保存"添加到列表')


def cmd_edit_command(self):
    """编辑选中的命令"""
    selection = self.cmd_tree.selection()
    if not selection:
        messagebox.showinfo('提示', '请先选择要编辑的命令', parent=self.root)
        return

    idx = int(selection[0])
    if idx >= len(self.cmd_list):
        return

    cmd = self.cmd_list[idx]

    workflows = self.workflow_manager.get_all_workflows() if hasattr(self, 'workflow_manager') else []
    dialog = self.CommandEditDialog(self, cmd, self.cmd_templates, workflows)
    self.root.wait_window(dialog.dialog)

    if dialog.result:
        self.cmd_list[idx] = dialog.result
        self.cmd_refresh_tree()
        if hasattr(self, '_save_workgroup_state'):
            self._save_workgroup_state()
        if hasattr(self, 'add_status_message'):
            self.add_status_message(f'命令已更新: {dialog.result.get("name", "")}')


def cmd_delete_command(self):
    """删除选中的命令"""
    selection = self.cmd_tree.selection()
    if not selection:
        messagebox.showinfo('提示', '请先选择要删除的命令', parent=self.root)
        return
    idx = int(selection[0])
    if messagebox.askyesno('确认', f'确定要删除命令"{self.cmd_list[idx].get("name", "")}"吗？', parent=self.root):
        del self.cmd_list[idx]
        self.cmd_selected_index = None
        self.cmd_refresh_tree()
        self._update_cmd_list_source()
        if self.wg_info.get('id') and self.wg_info.get('role') in ('owner', 'admin'):
            self._save_shared_commands()


# ==================== 命令执行控制 ====================

def cmd_execute_all(self):
    """执行全部命令"""
    if not self.cmd_list:
        messagebox.showinfo('提示', '命令列表为空', parent=self.root)
        return

    if self.cmd_running:
        messagebox.showinfo('提示', '已有命令在执行中', parent=self.root)
        return

    self.cmd_running = True
    self.cmd_paused = False
    self.cmd_stop_flag = False

    for cmd in self.cmd_list:
        if cmd.get('enabled', True) and cmd.get('status') in (CMD_STATUS_PENDING, CMD_STATUS_STOPPED, CMD_STATUS_COMPLETED):
            cmd['status'] = CMD_STATUS_PENDING

    self.cmd_refresh_tree()

    if hasattr(self, 'add_status_message'):
        self.add_status_message('开始执行全部命令...')

    import threading
    thread = threading.Thread(target=self._cmd_execute_thread, daemon=True)
    thread.start()


def cmd_pause_all(self):
    """暂停全部命令"""
    self.cmd_paused = True
    for cmd in self.cmd_list:
        if cmd.get('status') == CMD_STATUS_EXECUTING:
            cmd['status'] = CMD_STATUS_PAUSED
    self.cmd_refresh_tree()
    if hasattr(self, 'add_status_message'):
        self.add_status_message('已暂停全部命令')


def cmd_resume_all(self):
    """继续执行全部命令"""
    self.cmd_paused = False
    for cmd in self.cmd_list:
        if cmd.get('status') == CMD_STATUS_PAUSED:
            cmd['status'] = CMD_STATUS_PENDING
    self.cmd_refresh_tree()
    if hasattr(self, 'add_status_message'):
        self.add_status_message('继续执行全部命令...')


def cmd_stop_all(self):
    """停止全部命令"""
    self.cmd_stop_flag = True
    self.cmd_paused = False
    self.cmd_running = False
    self._stop_countdown_timer()
    for cmd in self.cmd_list:
        if cmd.get('status') in (CMD_STATUS_EXECUTING, CMD_STATUS_PAUSED, CMD_STATUS_PENDING, CMD_STATUS_QUEUED):
            cmd['status'] = CMD_STATUS_STOPPED
    self.cmd_refresh_tree()
    if hasattr(self, 'add_status_message'):
        self.add_status_message('已停止全部命令')


def cmd_clear_all(self):
    """全部清空"""
    self.cmd_stop_flag = True
    self.cmd_running = False
    self.cmd_paused = False
    self._stop_countdown_timer()
    self.cmd_list.clear()
    self.cmd_selected_index = None
    self.cmd_clear_edit()
    self.cmd_refresh_tree()
    self._update_cmd_list_source()
    
    if self.wg_info.get('id') and self.wg_info.get('role') in ('owner', 'admin'):
        self._save_shared_commands()
    
    if hasattr(self, 'add_status_message'):
        self.add_status_message('已清空全部命令')


def cmd_save_list(self):
    """保存命令列表到文件"""
    if not self.cmd_list:
        messagebox.showinfo('提示', '命令列表为空', parent=self.root)
        return

    filepath = filedialog.asksaveasfilename(
        title='保存命令列表',
        defaultextension='.json',
        filetypes=[('JSON文件', '*.json'), ('所有文件', '*.*')],
        initialdir='data'
    )
    if not filepath:
        return

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.cmd_list, f, ensure_ascii=False, indent=2)
        messagebox.showinfo('成功', f'命令列表已保存到:\n{filepath}', parent=self.root)
        if hasattr(self, 'add_status_message'):
            self.add_status_message(f'命令列表已保存: {os.path.basename(filepath)}')
    except Exception as e:
        messagebox.showerror('错误', f'保存失败: {e}', parent=self.root)


def cmd_load_list(self):
    """从文件加载命令列表(追加,不删除已有命令)"""
    filepath = filedialog.askopenfilename(
        title='加载命令列表',
        filetypes=[('JSON文件', '*.json'), ('所有文件', '*.*')],
        initialdir='data'
    )
    if not filepath:
        return

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            loaded_cmds = json.load(f)

        if not isinstance(loaded_cmds, list):
            messagebox.showerror('错误', '文件格式不正确', parent=self.root)
            return

        for cmd in loaded_cmds:
            cmd['status'] = CMD_STATUS_PENDING
            self.cmd_list.append(cmd)

        self.cmd_refresh_tree()
        messagebox.showinfo('成功',
            f'已加载 {len(loaded_cmds)} 条命令\n当前共 {len(self.cmd_list)} 条命令',
            parent=self.root)
        if hasattr(self, 'add_status_message'):
            self.add_status_message(f'已加载 {len(loaded_cmds)} 条命令')
    except Exception as e:
        messagebox.showerror('错误', f'加载失败: {e}', parent=self.root)


def _load_shared_commands(self):
    """从服务端加载共享命令列表"""
    if not self.wg_info.get('id'):
        return

    username = self._get_username()
    if not username:
        print('[DEBUG] 加载失败: 用户名为空')
        return

    print(f'[DEBUG] 正在从服务端加载命令列表, 用户={username}, 工作组ID={self.wg_info["id"]}')
    result, err = self._wg_request('/api/workgroup/get_shared_commands', {
        'username': username,
        'workgroup_id': self.wg_info['id']
    }, method='GET')

    if err:
        print(f'[DEBUG] 加载失败: {err}')
        self._update_cmd_status_message(f'加载共享命令失败: {err}')
        return

    if result and result.get('success'):
        commands = result.get('data', {}).get('commands', [])
        print(f'[DEBUG] 从服务端加载到 {len(commands)} 条命令')
        if commands:
            old_cmds = {cmd.get('name'): cmd for cmd in self.cmd_list}
            for cmd in commands:
                old_cmd = old_cmds.get(cmd.get('name'))
                if old_cmd:
                    if 'countdown_start_time' in old_cmd:
                        cmd['countdown_start_time'] = old_cmd['countdown_start_time']
                    if old_cmd.get('status') in (CMD_STATUS_EXECUTING, CMD_STATUS_COMPLETED):
                        cmd['status'] = old_cmd['status']
                elif cmd.get('exec_mode') == 'delayed' and cmd.get('exec_time'):
                    if 'countdown_start_time' not in cmd:
                        cmd['countdown_start_time'] = datetime.datetime.now()
            self.cmd_list = commands
            self.cmd_refresh_tree()
            self._update_cmd_list_source()
            self._update_cmd_status_message(f'已加载共享命令 ({len(commands)} 条)')
            if hasattr(self, 'add_status_message'):
                self.add_status_message(f'已加载 {len(commands)} 条共享命令')
        else:
            self.cmd_list = []
            self.cmd_refresh_tree()
            self._update_cmd_list_source()
            self._update_cmd_status_message('共享命令列表为空')
    else:
        print(f'[DEBUG] 加载失败: 服务端返回失败')


def _save_shared_commands(self):
    """保存共享命令列表到服务端（仅owner/admin）"""
    if not self.wg_info.get('id'):
        print('[DEBUG] 保存失败: 无工作组ID')
        return False

    role = self.wg_info.get('role', '')
    print(f'[DEBUG] 保存共享命令: 角色={role}')
    if role not in ('owner', 'admin'):
        print('[DEBUG] 保存失败: 非owner/admin角色')
        return False

    username = self._get_username()
    if not username:
        print('[DEBUG] 保存失败: 用户名为空')
        return False

    commands_to_upload = []
    for cmd in self.cmd_list:
        cmd_copy = cmd.copy()
        cmd_copy.pop('local_modified_time', None)
        cmd_copy.pop('countdown_start_time', None)
        commands_to_upload.append(cmd_copy)

    print(f'[DEBUG] 正在保存 {len(commands_to_upload)} 条命令到服务端...')
    result, err = self._wg_request('/api/workgroup/upload_commands', {
        'username': username,
        'workgroup_id': self.wg_info['id'],
        'commands': commands_to_upload
    })

    if err:
        self._update_cmd_status_message(f'保存共享命令失败: {err}')
        return False

    if result and result.get('success'):
        for cmd in self.cmd_list:
            if 'local_modified_time' in cmd:
                del cmd['local_modified_time']
        self._update_cmd_status_message(f'共享命令已保存 ({len(self.cmd_list)} 条)')
        return True

    print('[DEBUG] 保存失败: 服务端返回失败')
    return False


def _refresh_shared_commands_tick(self):
    """定时刷新共享命令（每3秒）"""
    if not self.wg_info.get('id'):
        return

    if getattr(self, '_sync_paused', False):
        print(f'[DEBUG _refresh] 同步已暂停，跳过刷新')
        return

    username = self._get_username()
    if not username:
        return

    result, err = self._wg_request('/api/workgroup/get_shared_commands', {
        'username': username,
        'workgroup_id': self.wg_info['id']
    }, method='GET')

    if err:
        return

    if result and result.get('success'):
        # 保存 hash 供下次增量检查
        new_hash = result.get('data', {}).get('commands_hash', '')
        if new_hash:
            self._last_commands_hash = new_hash
        
        # 服务端返回 not_modified 表示内容未变化，跳过处理
        if result.get('data', {}).get('not_modified'):
            print(f'[DEBUG _refresh] 命令无更新，跳过同步')
            return
        
        commands = result.get('data', {}).get('commands', [])
        print(f'[DEBUG _refresh] 服务端返回 {len(commands)} 条命令, 本地有 {len(self.cmd_list)} 条')
        if commands:
            old_cmds = {cmd.get('name'): cmd for cmd in self.cmd_list}
            new_cmd_list = []
            has_changes = False
            
            for cmd in commands:
                old_cmd = old_cmds.get(cmd.get('name'))
                if old_cmd:
                    local_modified = old_cmd.get('local_modified_time')
                    if local_modified:
                        try:
                            mod_time = datetime.datetime.fromisoformat(local_modified)
                            elapsed = (datetime.datetime.now() - mod_time).total_seconds()
                            if elapsed < 30:
                                print(f'[DEBUG _refresh] 命令 {cmd.get("name")} 刚被本地修改({elapsed:.1f}秒前)，完全保留本地')
                                new_cmd_list.append(old_cmd)
                                continue
                        except Exception as e:
                            print(f'[DEBUG _refresh] 解析修改时间异常: {e}')
                    
                    local_exec_time = old_cmd.get('exec_time', '')
                    local_exec_mode = old_cmd.get('exec_mode', '')
                    server_exec_time = cmd.get('exec_time', '')
                    server_exec_mode = cmd.get('exec_mode', '')
                    
                    if local_exec_time != server_exec_time or local_exec_mode != server_exec_mode:
                        print(f'[DEBUG _refresh] 本地与服务端不同，保留本地: {cmd.get("name")} local={local_exec_time} server={server_exec_time}')
                        new_cmd_list.append(old_cmd)
                        continue
                    
                    if cmd.get('exec_mode') == 'scheduled' and cmd.get('enabled', True):
                        remaining = self._get_remaining_seconds(cmd)
                        if remaining <= 0:
                            cmd['enabled'] = False
                            cmd['status'] = CMD_STATUS_COMPLETED
                            print(f'[DEBUG _refresh] 定时命令已过期，自动禁用: {cmd.get("name")}')
                            has_changes = True
                    
                    print(f'[DEBUG _refresh] 命令 {cmd.get("name")}: old_status={old_cmd.get("status")}')
                    if 'countdown_start_time' in old_cmd:
                        old_cmd['countdown_start_time'] = old_cmd['countdown_start_time']
                    if old_cmd.get('status') in (CMD_STATUS_EXECUTING, CMD_STATUS_QUEUED, CMD_STATUS_COMPLETED, CMD_STATUS_STOPPED):
                        old_cmd['status'] = old_cmd['status']
                        old_cmd['executed_time'] = old_cmd.get('executed_time')
                        old_cmd['enabled'] = old_cmd.get('enabled', True)
                    else:
                        print(f'[DEBUG _refresh] 服务端状态={cmd.get("status")}, 保留本地状态={old_cmd.get("status")}')
                        old_cmd['status'] = old_cmd.get('status', CMD_STATUS_PENDING)
                    new_cmd_list.append(old_cmd)
                else:
                    has_changes = True
                    cmd['countdown_start_time'] = datetime.datetime.now()
                    new_cmd_list.append(cmd)
                
                template_name = cmd.get('template_name', '')
                tpl = self.cmd_templates.get(template_name, {}) if template_name else {}
                is_python_template = tpl.get('is_python_template', False)
                if not is_python_template and cmd.get('python_code'):
                    cmd['python_code'] = None
                    has_changes = True
                    print(f'[DEBUG _refresh] 清理非Python模板命令的python_code字段: {cmd.get("name")}')
            
            if len(new_cmd_list) != len(self.cmd_list):
                has_changes = True
            print(f'[DEBUG _refresh] has_changes={has_changes}')
            self.cmd_list = new_cmd_list
            if has_changes:
                self.cmd_refresh_tree()
                self._update_cmd_list_source()
                self._update_cmd_status_message(f'共享命令已更新 ({len(new_cmd_list)} 条)')
            self._start_countdown_timer()


def _sync_workgroup_files(self):
    """同步工作组文件：上传本地文件到服务端，再从服务端下载新文件到本地"""
    if not self.wg_info.get('id'):
        messagebox.showwarning('提示', '请先加入工作组', parent=self.root)
        return

    username = self._get_username()
    if not username:
        messagebox.showwarning('提示', '请先登录', parent=self.root)
        return

    role = self.wg_info.get('role', '')

    local_base = self._get_workgroup_local_dir()
    local_dir = os.path.join(local_base, str(self.wg_info['id']))

    if role in ('owner', 'admin'):
        self._upload_local_files(username, local_dir)

    self._download_server_files(username, local_dir)

    self._load_shared_commands()
    self._update_cmd_status_message('同步完成，已进入服务端控制状态')


def _upload_local_files(self, username, local_dir):
    """上传本地工作组目录的文件到服务端"""
    if not os.path.exists(local_dir):
        return

    try:
        files_to_upload = []
        for root, dirs, files in os.walk(local_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, local_dir)
                with open(fpath, 'rb') as f:
                    content = base64.b64encode(f.read()).decode('utf-8')
                files_to_upload.append({
                    'path': rel_path,
                    'content': content,
                    'name': fname
                })

        if not files_to_upload:
            return

        result, err = self._wg_request('/api/workgroup/upload_files', {
            'username': username,
            'workgroup_id': self.wg_info['id'],
            'files': files_to_upload
        })

        if err:
            print(f'[DEBUG] 上传文件失败: {err}')
            return

        if result and result.get('success'):
            print(f'[DEBUG] 已上传 {len(files_to_upload)} 个文件到服务端')
    except Exception as e:
        print(f'[DEBUG] 上传文件异常: {e}')


def _download_server_files(self, username, local_dir):
    """从服务端下载工作组文件到本地目录"""
    try:
        result, err = self._wg_request('/api/workgroup/get_files', {
            'username': username,
            'workgroup_id': self.wg_info['id']
        }, method='POST')

        if err:
            print(f'[DEBUG] 获取文件列表失败: {err}')
            return

        if not result or not result.get('success'):
            return

        file_list = result.get('data', {}).get('files', [])
        os.makedirs(local_dir, exist_ok=True)

        for file_info in file_list:
            rel_path = file_info.get('path', '')
            content = file_info.get('content', '')
            if not rel_path or not content:
                continue

            local_path = os.path.join(local_dir, rel_path)
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            need_download = False
            if os.path.exists(local_path):
                with open(local_path, 'rb') as f:
                    local_content = base64.b64encode(f.read()).decode('utf-8')
                if local_content != content:
                    need_download = True
            else:
                need_download = True

            if need_download:
                with open(local_path, 'wb') as f:
                    f.write(base64.b64decode(content))
                print(f'[DEBUG] 下载文件: {rel_path}')

    except Exception as e:
        print(f'[DEBUG] 下载文件异常: {e}')


def _is_paused(self):
    """检查是否处于暂停状态"""
    paused_until = self.wg_info.get('paused_until')
    if not paused_until:
        return False
    remaining = self._check_pause_remaining(paused_until)
    return remaining > 0


def _start_countdown_timer(self):
    """启动倒计时刷新定时器（每秒刷新一次）"""
    self._stop_countdown_timer()
    self._countdown_running = True
    self._countdown_timer = self.root.after(5000, self._update_countdown_display)


def _stop_countdown_timer(self):
    """停止倒计时刷新定时器"""
    self._countdown_running = False
    if hasattr(self, '_countdown_timer') and self._countdown_timer:
        self.root.after_cancel(self._countdown_timer)
        self._countdown_timer = None


def _process_next_queued_command(self):
    """处理下一个排队的命令"""
    queued_cmds = [cmd for cmd in self.cmd_list if cmd.get('status') == CMD_STATUS_QUEUED and cmd.get('enabled', True)]
    if queued_cmds:
        next_cmd = queued_cmds[0]
        print(f'[DEBUG] _process_next_queued_command: 发现排队命令 {next_cmd.get("name")}')
        next_cmd['status'] = CMD_STATUS_EXECUTING
        self.root.after(0, self.cmd_refresh_tree)
        
        self._pause_sync_temporarily()
        
        import threading
        def execute_and_update(c=next_cmd):
            print(f'[DEBUG] 线程开始执行: {c.get("name")}')
            try:
                self._execute_single_command(c)
                print(f'[DEBUG] _execute_single_command 正常返回，检查状态')
                if not self.cmd_stop_flag:
                    c['status'] = CMD_STATUS_COMPLETED
                    c['executed_time'] = datetime.datetime.now().isoformat()
                    c['enabled'] = False
                    print(f'[DEBUG] 已标记命令为已完成: {c.get("name")}')
                else:
                    c['status'] = CMD_STATUS_STOPPED
                    c['enabled'] = False
                    print(f'[DEBUG] 命令被停止: {c.get("name")}')
                self._update_command_to_server(c)
                print(f'[DEBUG] 命令执行完成: {c.get("name")}')
            except SystemExit as e:
                print(f'[DEBUG] 命令执行引发 SystemExit (code: {e.code}): {c.get("name")}')
                c['status'] = CMD_STATUS_COMPLETED
                c['executed_time'] = datetime.datetime.now().isoformat()
                c['enabled'] = False
                self._update_command_to_server(c)
            except Exception as e:
                print(f'[DEBUG] 命令执行异常: {e}')
                c['status'] = CMD_STATUS_COMPLETED
                c['executed_time'] = datetime.datetime.now().isoformat()
                c['enabled'] = False
                self._update_command_to_server(c)
            print(f'[DEBUG] execute_and_update 即将刷新树')
            self.root.after(0, self.cmd_refresh_tree)
            print(f'[DEBUG] execute_and_update 刷新树调度完成')
            print(f'[DEBUG] execute_and_update 完成')
            self.root.after(0, self._process_next_queued_command)
        thread = threading.Thread(target=execute_and_update, daemon=True)
        thread.start()
        print(f'[DEBUG] 启动执行线程')


def _update_countdown_display(self):
    """更新倒计时显示"""
    if not hasattr(self, 'cmd_tree') or not self.cmd_tree:
        return
    
    if getattr(self, 'cmd_paused', False):
        self._countdown_timer = self.root.after(5000, self._update_countdown_display)
        return

    has_timed_cmds = False
    expired_cmds = []
    for cmd in self.cmd_list:
        if not cmd.get('enabled', True):
            continue
        mode = cmd.get('exec_mode', '')
        status = cmd.get('status', '')
        if status in (CMD_STATUS_STOPPED, CMD_STATUS_COMPLETED):
            continue
        if mode == 'immediate' and status == CMD_STATUS_PENDING:
            has_timed_cmds = True
            remaining = self._get_remaining_seconds(cmd)
            if remaining <= 0:
                expired_cmds.append(cmd)
        elif mode in ('scheduled', 'delayed') and status == CMD_STATUS_PENDING:
            has_timed_cmds = True
            remaining = self._get_remaining_seconds(cmd)
            if remaining <= 0:
                expired_cmds.append(cmd)
        elif mode in ('immediate', 'scheduled', 'delayed') and status in (CMD_STATUS_QUEUED, CMD_STATUS_EXECUTING):
            has_timed_cmds = True
    
    for cmd in expired_cmds:
        if cmd.get('exec_mode') == 'scheduled':
            exec_time = cmd.get('exec_time', '00:00:00')
            parts = exec_time.split(':')
            try:
                target_h = int(parts[0]) if len(parts) > 0 else 0
                target_m = int(parts[1]) if len(parts) > 1 else 0
                target_s = int(parts[2]) if len(parts) > 2 else 0
            except:
                target_h, target_m, target_s = 0, 0, 0
            now = datetime.datetime.now()
            target = now.replace(hour=target_h, minute=target_m, second=target_s, microsecond=0)
            diff_seconds = (now - target).total_seconds()
            if diff_seconds > 60:
                print(f'[DEBUG] 命令 {cmd.get("name")} 已过期超过60秒，停止执行')
                cmd['status'] = CMD_STATUS_STOPPED
                cmd['enabled'] = False
                continue
        
        print(f'[DEBUG] 命令 {cmd.get("name")} 倒计时结束，加入排队')
        cmd['status'] = CMD_STATUS_QUEUED

    executing_cmd = None
    for cmd in self.cmd_list:
        if cmd.get('status') == CMD_STATUS_EXECUTING:
            executing_cmd = cmd
            break

    if not executing_cmd:
        queued_cmds = [cmd for cmd in self.cmd_list if cmd.get('status') == CMD_STATUS_QUEUED and cmd.get('enabled', True)]
        if queued_cmds:
            next_cmd = queued_cmds[0]
            print(f'[DEBUG] 开始执行排队命令: {next_cmd.get("name")}')
            next_cmd['status'] = CMD_STATUS_EXECUTING
            self.root.after(0, self.cmd_refresh_tree)
            
            self._pause_sync_temporarily()
            
            import threading
            def execute_and_update(c=next_cmd):
                print(f'[DEBUG] 线程开始执行: {c.get("name")}')
                try:
                    self._execute_single_command(c)
                    print(f'[DEBUG] _execute_single_command 正常返回，检查状态')
                    if not self.cmd_stop_flag:
                        c['status'] = CMD_STATUS_COMPLETED
                        c['executed_time'] = datetime.datetime.now().isoformat()
                        c['enabled'] = False
                        print(f'[DEBUG] 已标记命令为已完成: {c.get("name")}')
                    else:
                        c['status'] = CMD_STATUS_STOPPED
                        c['enabled'] = False
                        print(f'[DEBUG] 命令被停止: {c.get("name")}')
                    self._update_command_to_server(c)
                    print(f'[DEBUG] 命令执行完成: {c.get("name")}')
                except SystemExit as e:
                    print(f'[DEBUG] 命令执行引发 SystemExit (code: {e.code}): {c.get("name")}')
                    c['status'] = CMD_STATUS_COMPLETED
                    c['executed_time'] = datetime.datetime.now().isoformat()
                    c['enabled'] = False
                    self._update_command_to_server(c)
                except Exception as e:
                    print(f'[DEBUG] 命令执行异常: {e}')
                    c['status'] = CMD_STATUS_COMPLETED
                    c['executed_time'] = datetime.datetime.now().isoformat()
                    c['enabled'] = False
                    self._update_command_to_server(c)
                print(f'[DEBUG] execute_and_update 即将刷新树')
                self.root.after(0, self.cmd_refresh_tree)
                print(f'[DEBUG] execute_and_update 刷新树调度完成')

                print(f'[DEBUG] execute_and_update 完成')
                self.root.after(0, self._process_next_queued_command)
            thread = threading.Thread(target=execute_and_update, daemon=True)
            thread.start()
            print(f'[DEBUG] 启动执行线程')

    for cmd in self.cmd_list:
        if cmd.get('status') == CMD_STATUS_QUEUED and not cmd.get('enabled', True):
            cmd['status'] = CMD_STATUS_COMPLETED
            print(f'[DEBUG] 排队命令 {cmd.get("name")} 已禁用，移出排队')

    if has_timed_cmds or expired_cmds:
        self.cmd_refresh_tree()

    if has_timed_cmds:
        self._countdown_timer = self.root.after(5000, self._update_countdown_display)
    elif self._countdown_timer:
        self._stop_countdown_timer()


def _get_remaining_seconds(self, cmd):
    """获取命令剩余秒数"""
    mode = cmd.get('exec_mode', 'immediate')
    status = cmd.get('status', CMD_STATUS_PENDING)
    
    if status == CMD_STATUS_COMPLETED:
        return 999999
    
    if mode == 'immediate':
        start_time = cmd.get('countdown_start_time')
        if start_time:
            if isinstance(start_time, str):
                try:
                    start_time = datetime.datetime.fromisoformat(start_time)
                except:
                    start_time = datetime.datetime.now()
            elapsed = (datetime.datetime.now() - start_time).total_seconds()
            remaining = 3 - elapsed
            return max(0, int(remaining))
        return 3
    elif mode == 'delayed':
        exec_time = cmd.get('exec_time', '00:00:10')
        delay_seconds = self._parse_time_to_seconds(exec_time)
        start_time = cmd.get('countdown_start_time')
        if start_time:
            if isinstance(start_time, str):
                try:
                    start_time = datetime.datetime.fromisoformat(start_time)
                except:
                    start_time = datetime.datetime.now()
            elapsed = (datetime.datetime.now() - start_time).total_seconds()
            remaining = delay_seconds - elapsed
            return max(0, int(remaining))
        return delay_seconds
    elif mode == 'scheduled':
        exec_time = cmd.get('exec_time', '00:00:00')
        parts = exec_time.split(':')
        try:
            target_h = int(parts[0]) if len(parts) > 0 else 0
            target_m = int(parts[1]) if len(parts) > 1 else 0
            target_s = int(parts[2]) if len(parts) > 2 else 0
            target_h = max(0, min(23, target_h))
            target_m = max(0, min(59, target_m))
            target_s = max(0, min(59, target_s))
        except (ValueError, IndexError):
            target_h, target_m, target_s = 0, 0, 0
        now = datetime.datetime.now()
        target = now.replace(hour=target_h, minute=target_m, second=target_s, microsecond=0)
        diff = target - now
        remaining = int(diff.total_seconds())
        if remaining <= 0:
            return 0
        return remaining
    return 999999


def _start_wg_sync(self):
    """启动工作组同步定时器（15秒间隔，避免高频请求压垮服务端）"""
    self._stop_wg_sync()
    self._wg_syncing = False  # 并发保护标志
    self._wg_sync_timer = self.root.after(15000, self._wg_sync_tick)


def _stop_wg_sync(self):
    """停止工作组同步定时器"""
    if hasattr(self, '_wg_sync_timer') and self._wg_sync_timer:
        self.root.after_cancel(self._wg_sync_timer)
        self._wg_sync_timer = None


def _pause_sync_temporarily(self):
    """暂时停止同步一段时间"""
    try:
        self._stop_wg_sync()
        self._sync_paused = True
        print(f'[DEBUG] 同步已暂停')
        self.root.after(15000, self._resume_sync)
    except Exception as e:
        print(f'[DEBUG] _pause_sync_temporarily 异常: {e}')


def _resume_sync(self):
    """恢复同步"""
    self._sync_paused = False
    print(f'[DEBUG] 同步已恢复')
    if self.wg_info.get('id'):
        self._wg_sync_timer = self.root.after(15000, self._wg_sync_tick)


def _update_command_to_server(self, cmd):
    """立即更新命令状态到服务端"""
    if not self.wg_info.get('id'):
        return
    username = self._get_username()
    if not username:
        return
    import requests
    import copy
    server_url = self._get_server_url()
    try:
        cmd_copy = copy.deepcopy(cmd)
        for key, value in list(cmd_copy.items()):
            if hasattr(value, 'isoformat'):
                cmd_copy[key] = value.isoformat()
        requests.post(f'{server_url}/api/workgroup/update_command', json={
            'username': username,
            'workgroup_id': self.wg_info.get('id'),
            'command': cmd_copy
        }, timeout=5)
        print(f'[DEBUG] 已更新命令状态到服务端: {cmd.get("name")}')
    except Exception as e:
        print(f'[DEBUG] 更新命令状态失败: {e}')


def _wg_sync_tick(self):
    """工作组同步心跳（每15秒）"""
    if not self.wg_info.get('id'):
        return
    # 并发保护：前一次同步请求未完成时跳过
    if getattr(self, '_wg_syncing', False):
        self._wg_sync_timer = self.root.after(15000, self._wg_sync_tick)
        return
    self._wg_syncing = True
    try:
        self._refresh_shared_commands_tick()
    finally:
        self._wg_syncing = False
    self._wg_sync_timer = self.root.after(15000, self._wg_sync_tick)


# ==================== 工作组管理 ====================

def _wg_request(self, url, json_data=None, method='POST'):
    """工作组API请求封装，带错误处理"""
    import requests
    server_url = self._get_server_url()
    full_url = f'{server_url}{url}'
    print(f'[DEBUG] API请求: {method} {full_url}')
    print(f'[DEBUG] 请求数据: {json_data}')
    try:
        if method == 'GET':
            resp = requests.get(full_url, params=json_data, timeout=10)
        else:
            resp = requests.post(full_url, json=json_data, timeout=10)
        print(f'[DEBUG] API响应: HTTP {resp.status_code}')
        # 检查HTTP状态码
        if resp.status_code != 200:
            return None, f'服务器返回错误: HTTP {resp.status_code}\n{resp.text[:200]}'
        # 解析JSON
        try:
            result = resp.json()
            print(f'[DEBUG] API结果: {result}')
            return result, None
        except Exception:
            return None, f'服务器返回非JSON数据: {resp.text[:200]}'
    except requests.exceptions.ConnectionError:
        return None, '无法连接到服务器，请确认服务端已启动'
    except requests.exceptions.Timeout:
        return None, '请求超时，请检查网络'
    except Exception as e:
        return None, f'请求失败: {str(e)}'


def _get_server_url(self):
    """获取服务端地址（优先直连，减少花生壳流量）
    优先级：局域网直连 > 花生壳直连配置 > 花生壳域名
    首次调用时同步检测，确定后缓存，后续直接使用
    """
    # 如果已经缓存了直连地址，直接使用
    cached = getattr(self, '_cached_server_url', None)
    if cached:
        return cached
    
    # 同步检测最优服务器（只执行一次）
    if not getattr(self, '_server_detect_done', False):
        self._server_detect_done = True
        best = self._detect_best_server()
        if best:
            self._cached_server_url = best
            print(f'[服务器] 切换到: {best}')
        else:
            self._cached_server_url = 'https://9793tg1lo456.vicp.fun'
            print('[服务器] 直连不可用，使用花生壳域名')
    
    return getattr(self, '_cached_server_url', 'https://9793tg1lo456.vicp.fun')


def _detect_best_server(self):
    """检测最优服务器地址
    优先级：花生壳直连配置 > 局域网直连 > 花生壳域名
    花生壳直连配置：先通过花生壳域名读取direct_connect.json获取真实外网地址，
    再直接与外网地址通信，不经过花生壳转发（省流量、更快速）
    """
    import socket
    import requests
    
    print('[服务器] ===== 开始检测最优服务器地址 =====')
    
    # === 第1优先级：从花生壳读取直连配置（绕过花生壳转发） ===
    try:
        print('[服务器] 正在从花生壳读取直连配置 (9793tg1lo456.vicp.fun/api/direct_connect) ...')
        resp = requests.get('https://9793tg1lo456.vicp.fun/api/direct_connect', timeout=10)
        print(f'[服务器] 花生壳响应: HTTP {resp.status_code}')
        if resp.status_code == 200:
            result = resp.json()
            print(f'[服务器] 直连配置数据: {result}')
            if result.get('success') and result.get('data', {}).get('direct_url'):
                direct_url = result['data']['direct_url'].rstrip('/')
                print(f'[服务器] ★ 获取到真实外网地址: {direct_url}')
                # 验证直连地址是否可用
                try:
                    print(f'[服务器] 正在验证外网直连地址: {direct_url}/api/health ...')
                    check = requests.head(f'{direct_url}/api/health', timeout=5)
                    print(f'[服务器] 外网直连验证响应: HTTP {check.status_code}')
                    if check.status_code < 500:
                        print(f'[服务器] ★ 外网直连地址可用: {direct_url} (绕过花生壳转发)')
                        return direct_url
                except Exception as e:
                    print(f'[服务器] 外网直连地址不可用: {direct_url} ({e})')
            else:
                print('[服务器] 直连地址未配置或为空')
    except Exception as e:
        print(f'[服务器] 读取直连配置失败: {e}')
    
    # === 第2优先级：局域网直连 ===
    subnet = None
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f'[服务器] 本机IP: {local_ip}')
        if local_ip.startswith(('192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.2', '172.3')):
            subnet = local_ip.rsplit('.', 1)[0]
            print(f'[服务器] 局域网段: {subnet}.x')
    except Exception as e:
        print(f'[服务器] 获取本机IP失败: {e}')
    
    if subnet:
        for suffix in ['.150', '.1', '.100', '.2']:
            for port in ['9000', '5000']:
                candidate = f'http://{subnet}{suffix}:{port}'
                try:
                    resp = requests.head(f'{candidate}/api/health', timeout=3)
                    if resp.status_code < 500:
                        print(f'[服务器] ★ 局域网直连可用: {candidate}')
                        return candidate
                except Exception:
                    pass
        print('[服务器] 局域网直连均不可用')
    else:
        print('[服务器] 非局域网环境，跳过局域网直连')
    
    # === 第3优先级：花生壳域名 ===
    print('[服务器] ★ 所有直连方式均不可用，使用花生壳域名')
    return None  # 返回None表示使用默认花生壳域名


def _get_username(self):
    """获取当前登录用户名"""
    try:
        if hasattr(self, 'activation_manager') and self.activation_manager and hasattr(self.activation_manager, 'username') and self.activation_manager.username:
            username = self.activation_manager.username
            print(f'[DEBUG] _get_username from activation_manager: {username}')
            return username
        projects_dir = getattr(self, 'config', None) and getattr(self.config, 'projects_directory', '')
        if not projects_dir:
            projects_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        cfg_path = os.path.join(projects_dir, 'activation.json')
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                username = json.load(f).get('username', '')
                if username:
                    print(f'[DEBUG] _get_username from activation.json: {username}')
                    return username
        cfg_path2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'activation_config.json')
        if os.path.exists(cfg_path2):
            with open(cfg_path2, 'r', encoding='utf-8') as f:
                username = json.load(f).get('username', '')
                if username:
                    print(f'[DEBUG] _get_username from activation_config.json: {username}')
                    return username
        print('[DEBUG] _get_username: 未找到用户名')
        return ''
    except Exception as e:
        print(f'[DEBUG] _get_username 异常: {e}')
        return ''


def _save_local_cmd_list_backup(self):
    """保存本地命令列表备份"""
    try:
        backup = {
            'cmd_list': self.cmd_list,
            'timestamp': datetime.datetime.now().isoformat()
        }
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, 'local_cmd_backup.json')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup, f, ensure_ascii=False, indent=2)
        print(f'[DEBUG] 本地命令列表已备份, 共 {len(self.cmd_list)} 条')
    except Exception as e:
        print(f'[DEBUG] 备份本地命令列表失败: {e}')


def _load_local_cmd_list_backup(self):
    """加载本地命令列表备份"""
    try:
        backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'local_cmd_backup.json')
        if os.path.exists(backup_path):
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup = json.load(f)
            cmds = backup.get('cmd_list', [])
            print(f'[DEBUG] 已加载本地命令列表备份, 共 {len(cmds)} 条')
            return cmds
        return []
    except Exception as e:
        print(f'[DEBUG] 加载本地命令列表备份失败: {e}')
        return []


def _get_workgroup_local_dir(self):
    """获取工作组在本地项目目录下的同步目录"""
    try:
        project_dir = getattr(self, 'config', None) and getattr(self.config, 'projects_directory', '')
        if not project_dir:
            project_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'default')
        return os.path.join(project_dir, 'workgroups')
    except Exception:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'default', 'workgroups')


def wg_create_dialog(self):
    """创建工作组弹窗"""
    if self.cmd_list:
        save_choice = messagebox.askyesno('创建工作组',
            '创建工作组将清空本地命令列表，是否保存当前命令列表？\n\n选择"是"保存为文件，"否"不保存直接创建。',
            parent=self.root)
        if save_choice:
            self.cmd_save_list()

        self.cmd_list = []
        self.cmd_refresh_tree()

    dialog = tk.Toplevel(self.root)
    dialog.title('创建工作组')
    dialog.geometry('400x300')
    dialog.transient(self.root)
    dialog.grab_set()
    dialog.resizable(False, False)

    ttk.Label(dialog, text='工作组名称:').pack(pady=(15, 2))
    name_entry = ttk.Entry(dialog, width=35)
    name_entry.pack()

    ttk.Label(dialog, text='进入口令:').pack(pady=(10, 2))
    pwd_entry = ttk.Entry(dialog, width=35, show='*')
    pwd_entry.pack()

    ttk.Label(dialog, text='备注:').pack(pady=(10, 2))
    note_entry = ttk.Entry(dialog, width=35)
    note_entry.pack()

    def _confirm():
        name = name_entry.get().strip()
        pwd = pwd_entry.get().strip()
        note = note_entry.get().strip()
        if not name or not pwd:
            messagebox.showwarning('提示', '工作组名称和口令不能为空', parent=dialog)
            return

        username = self._get_username()
        if not username:
            messagebox.showwarning('提示', '请先登录', parent=dialog)
            return

        result, err = self._wg_request('/api/workgroup/create', {
            'name': name, 'password': pwd, 'note': note, 'username': username
        })
        if err:
            messagebox.showerror('创建失败', err, parent=dialog)
            return
        if result.get('success'):
            wg_data = result.get('data', {})
            self.wg_info = {
                'id': wg_data.get('id'),
                'name': wg_data.get('name'),
                'role': 'owner',
                'sync_dir': wg_data.get('sync_dir', ''),
                'last_sync': '',
                'disabled': False
            }
            # 创建本地同步目录
            local_base = self._get_workgroup_local_dir()
            local_dir = os.path.join(local_base, str(self.wg_info['id']))
            os.makedirs(local_dir, exist_ok=True)
            os.makedirs(os.path.join(local_dir, 'commands'), exist_ok=True)
            # 更新UI
            self.wg_status_label.config(text=f'工作组: {self.wg_info["name"]} (创建者)',
                                        foreground='#008800')
            self._update_cmd_list_source()
            self._update_cmd_status_message(f'已创建并加入工作组 [{self.wg_info["name"]}]')
            self._start_wg_sync()
            self._load_shared_commands()
            messagebox.showinfo('成功', f'工作组 [{name}] 创建成功！已自动加入并拥有管理权限。', parent=dialog)
            dialog.destroy()
        else:
            messagebox.showerror('创建失败', result.get('message', '未知错误'), parent=dialog)

    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=20)
    ttk.Button(btn_frame, text='确定', command=_confirm, width=10).pack(side=tk.LEFT, padx=10)
    ttk.Button(btn_frame, text='取消', command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=10)


def wg_manage_dialog(self):
    """管理工作组弹窗 - 仅owner/admin可进入"""
    if not self.wg_info.get('id'):
        messagebox.showwarning('提示', '请先加入工作组', parent=self.root)
        return

    dialog = tk.Toplevel(self.root)
    dialog.title(f'管理工作组 - {self.wg_info.get("name", "")}')
    dialog.geometry('600x900')
    dialog.transient(self.root)
    dialog.grab_set()

    ttk.Label(dialog, text=f'工作组: {self.wg_info.get("name", "")}',
              font=('Arial', 14, 'bold')).pack(pady=10)

    # 成员列表
    columns = ('username', 'game_id', 'role', 'status')
    tree = ttk.Treeview(dialog, columns=columns, show='headings', height=12)
    tree.heading('username', text='用户名')
    tree.heading('game_id', text='游戏ID')
    tree.heading('role', text='角色')
    tree.heading('status', text='状态')
    tree.column('username', width=120)
    tree.column('game_id', width=120)
    tree.column('role', width=100)
    tree.column('status', width=80)
    tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

    role_map = {'owner': '创建者', 'admin': '管理员', 'member': '组员'}

    def load_members():
        result, err = self._wg_request('/api/workgroup/manage', {
            'username': self._get_username(), 'workgroup_id': self.wg_info['id']
        })
        if err:
            messagebox.showerror('错误', err, parent=dialog)
            return
        if result.get('success'):
            for item in tree.get_children():
                tree.delete(item)
            for m in result.get('data', {}).get('members', []):
                status = '禁用' if m.get('is_disabled') else '正常'
                tree.insert('', tk.END, values=(
                    m.get('username', ''), m.get('game_id', ''),
                    role_map.get(m.get('role', ''), m.get('role', '')),
                    status
                ))
            # 更新本地role信息
            username = self._get_username()
            for m in result.get('data', {}).get('members', []):
                if m.get('username') == username:
                    self.wg_info['role'] = m.get('role', 'member')
                    break
        else:
            messagebox.showwarning('提示', result.get('message', '权限不足，仅创建者或管理员可管理'), parent=dialog)

    load_members()

    def set_admin():
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], 'values')
        target = vals[0]
        if target == self._get_username():
            messagebox.showwarning('提示', '不能修改自己的角色', parent=dialog)
            return
        result, err = self._wg_request('/api/workgroup/set_role', {
            'username': self._get_username(), 'workgroup_id': self.wg_info['id'],
            'target_username': target, 'role': 'admin'
        })
        if err:
            messagebox.showerror('错误', err, parent=dialog)
            return
        if result.get('success'):
            messagebox.showinfo('成功', result.get('message'), parent=dialog)
            load_members()
        else:
            messagebox.showerror('失败', result.get('message'), parent=dialog)

    def set_member():
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], 'values')
        target = vals[0]
        if target == self._get_username():
            return
        result, err = self._wg_request('/api/workgroup/set_role', {
            'username': self._get_username(), 'workgroup_id': self.wg_info['id'],
            'target_username': target, 'role': 'member'
        })
        if err:
            messagebox.showerror('错误', err, parent=dialog)
            return
        if result.get('success'):
            load_members()
        else:
            messagebox.showerror('失败', result.get('message'), parent=dialog)

    def toggle_disable():
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], 'values')
        target = vals[0]
        if target == self._get_username():
            messagebox.showwarning('提示', '不能禁用自己', parent=dialog)
            return
        result, err = self._wg_request('/api/workgroup/toggle_disable', {
            'username': self._get_username(), 'workgroup_id': self.wg_info['id'],
            'target_username': target
        })
        if err:
            messagebox.showerror('错误', err, parent=dialog)
            return
        if result.get('success'):
            load_members()
        else:
            messagebox.showerror('失败', result.get('message'), parent=dialog)

    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text='设为管理员', command=set_admin, width=12).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='取消管理员', command=set_member, width=12).pack(side=tk.LEFT, padx=5)
    self._mgmt_disable_btn = tk.Button(btn_frame, text='禁用/启用', command=toggle_disable,
        width=12, bg='#FF8800', fg='white')
    self._mgmt_disable_btn.pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='刷新', command=load_members, width=10).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='关闭', command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)


def wg_join_dialog(self):
    """加入工作组弹窗"""
    if self.cmd_list:
        self._save_local_cmd_list_backup()
        self.cmd_list = []
        self.cmd_refresh_tree()
        self._update_cmd_list_source()

    dialog = tk.Toplevel(self.root)
    dialog.title('加入工作组')
    dialog.geometry('400x250')
    dialog.transient(self.root)
    dialog.grab_set()
    dialog.resizable(False, False)

    ttk.Label(dialog, text='进入口令:').pack(pady=(20, 2))
    pwd_entry = ttk.Entry(dialog, width=35)
    pwd_entry.pack()

    ttk.Label(dialog, text='游戏ID:').pack(pady=(10, 2))
    game_entry = ttk.Entry(dialog, width=35)
    game_entry.pack()

    def _confirm():
        pwd = pwd_entry.get().strip()
        game_id = game_entry.get().strip()
        if not pwd:
            messagebox.showwarning('提示', '请输入进入口令', parent=dialog)
            return

        username = self._get_username()
        if not username and hasattr(self, 'activation_manager') and self.activation_manager:
            username = self.activation_manager.username
        if not username:
            messagebox.showwarning('提示', '请先登录', parent=dialog)
            return

        result, err = self._wg_request('/api/workgroup/join', {
            'password': pwd, 'username': username, 'game_id': game_id
        })
        if err:
            messagebox.showerror('加入失败', err, parent=dialog)
            return
        if result.get('success'):
            wg_data = result.get('data', {}).get('workgroup', {})
            if self.cmd_list:
                self._save_local_cmd_list_backup()
            self.wg_info = {
                'id': wg_data.get('id'),
                'name': wg_data.get('name'),
                'role': result.get('data', {}).get('role', 'member') or 'member',
                'sync_dir': wg_data.get('sync_dir', ''),
                'last_sync': '',
                'disabled': False,
                'paused_until': None
            }
            self.cmd_list = []
            self.cmd_refresh_tree()
            self._update_cmd_list_source()
            local_base = self._get_workgroup_local_dir()
            local_dir = os.path.join(local_base, str(self.wg_info['id']))
            os.makedirs(local_dir, exist_ok=True)
            os.makedirs(os.path.join(local_dir, 'commands'), exist_ok=True)
            _rm = {'owner': '创建者', 'admin': '管理员', 'member': '组员'}
            _rd = _rm.get(self.wg_info.get('role', 'member'), self.wg_info.get('role', ''))
            self.wg_status_label.config(text=f'工作组: {self.wg_info["name"]} ({_rd})',
                                        foreground='#008800')
            self._update_cmd_list_source()
            self._update_cmd_status_message(f'已加入工作组 [{self.wg_info["name"]}]')
            self._start_wg_sync()
            self._load_shared_commands()
            self._save_workgroup_state()
            messagebox.showinfo('成功',
                f'成功加入工作组 [{self.wg_info["name"]}]', parent=dialog)
            dialog.destroy()
        else:
            messagebox.showerror('加入失败', result.get('message', '未知错误'), parent=dialog)

    btn_frame = ttk.Frame(dialog)
    btn_frame.pack(pady=20)
    ttk.Button(btn_frame, text='确定', command=_confirm, width=10).pack(side=tk.LEFT, padx=10)
    ttk.Button(btn_frame, text='取消', command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=10)


def wg_pause_control(self):
    """暂定/恢复工作组控制"""
    if not self.wg_info.get('id'):
        messagebox.showwarning('提示', '请先加入工作组', parent=self.root)
        return

    paused_until = self.wg_info.get('paused_until')
    if paused_until:
        remaining = self._check_pause_remaining(paused_until)
        if remaining > 0:
            if messagebox.askyesno('确认', f'还有 {remaining} 分钟才恢复。\n\n确定要立即恢复接受控制吗？', parent=self.root):
                self.wg_info['paused_until'] = None
                self.wg_disable_btn.config(text='暂断3小时', bg='#44CC44',
                                            activebackground='#33AA33', activeforeground='white')
                self._update_cmd_status_message('已恢复接受工作组控制')
        else:
            self.wg_info['paused_until'] = None
            self.wg_disable_btn.config(text='暂断3小时', bg='#44CC44',
                                        activebackground='#33AA33', activeforeground='white')
            self._update_cmd_status_message('暂停时间已到，已恢复接受控制')
    else:
        pause_minutes = 180
        future_time = datetime.datetime.now() + datetime.timedelta(minutes=pause_minutes)
        self.wg_info['paused_until'] = future_time.isoformat()
        self.wg_disable_btn.config(text='恢复控制', bg='#FF4444',
                                    activebackground='#CC0000', activeforeground='white')
        self._update_cmd_status_message(f'已暂停工作组控制，3小时后自动恢复')
        self._start_pause_timer()


def _check_pause_remaining(self, paused_until_iso):
    """检查暂停剩余时间（分钟）"""
    try:
        paused_until = datetime.datetime.fromisoformat(paused_until_iso)
        remaining = (paused_until - datetime.datetime.now()).total_seconds() / 60
        return max(0, int(remaining))
    except:
        return 0


def _start_pause_timer(self):
    """启动暂停检查定时器（每分钟检查一次）"""
    self._stop_pause_timer()
    self._pause_timer = self.root.after(60000, self._check_pause_expired)


def _stop_pause_timer(self):
    """停止暂停检查定时器"""
    if hasattr(self, '_pause_timer') and self._pause_timer:
        self.root.after_cancel(self._pause_timer)
        self._pause_timer = None


def _check_pause_expired(self):
    """检查暂停是否已过期"""
    if not self.wg_info.get('id'):
        return
    paused_until = self.wg_info.get('paused_until')
    if not paused_until:
        return
    remaining = self._check_pause_remaining(paused_until)
    if remaining > 0:
        self.wg_disable_btn.config(text=f'恢复({remaining}分)', bg='#FF4444',
                                    activebackground='#CC0000', activeforeground='white')
        self._pause_timer = self.root.after(60000, self._check_pause_expired)
    else:
        self.wg_info['paused_until'] = None
        self.wg_disable_btn.config(text='暂断3小时', bg='#44CC44',
                                    activebackground='#33AA33', activeforeground='white')
        self._update_cmd_status_message('暂停时间已到，已恢复接受控制')
        self._stop_pause_timer()


def wg_leave(self):
    """退出工作组"""
    if not self.wg_info.get('id'):
        messagebox.showwarning('提示', '你当前未加入工作组', parent=self.root)
        return

    if not messagebox.askyesno('确认', '确定要退出当前工作组吗？', parent=self.root):
        return

    result, err = self._wg_request('/api/workgroup/leave', {
        'username': self._get_username(), 'workgroup_id': self.wg_info['id']
    })
    if err:
        messagebox.showerror('退出失败', err, parent=self.root)
        return
    if result.get('success'):
        self._stop_wg_sync()
        wg_name = self.wg_info.get('name', '')
        self.wg_info = {'id': None, 'name': None, 'role': None, 'sync_dir': None, 'last_sync': None, 'disabled': False, 'paused_until': None}
        self.cmd_list = []
        self.cmd_refresh_tree()
        local_cmds = self._load_local_cmd_list_backup()
        if local_cmds:
            self.cmd_list = local_cmds
            self.cmd_refresh_tree()
        self.wg_status_label.config(text='未加入工作组', foreground='gray')
        self._update_cmd_list_source()
        self._update_cmd_status_message(f'已退出工作组 [{wg_name}]')
        self._save_workgroup_state()
    else:
        messagebox.showerror('退出失败', result.get('message', '未知错误'), parent=self.root)


# ==================== 命令执行线程 ====================


def _do_sync_now(self):
    """立即同步一次（刷新共享命令）"""
    if not self.wg_info.get('id'):
        return
    self._load_shared_commands()


# ==================== 命令执行线程 ====================

def _cmd_execute_thread(self):
    """命令执行线程"""
    import time
    import threading

    for i, cmd in enumerate(self.cmd_list):
        if self.cmd_stop_flag:
            break

        while self.cmd_paused and not self.cmd_stop_flag:
            time.sleep(0.5)
        if self.cmd_stop_flag:
            break

        exec_mode = cmd.get('exec_mode', 'immediate')
        if exec_mode == 'immediate':
            for countdown in range(3, 0, -1):
                if self.cmd_stop_flag:
                    break
                while self.cmd_paused and not self.cmd_stop_flag:
                    time.sleep(0.5)
                if self.cmd_stop_flag:
                    break
                self.root.after(0, lambda c=countdown, n=cmd.get('name',''): self._update_cmd_status_message(
                    f"{n}: 将在 {c} 秒后执行..."))
                time.sleep(1)

        elif exec_mode == 'scheduled':
            exec_time_str = cmd.get('exec_time', '00:00:00')
            parts = exec_time_str.split(':')
            target_h = int(parts[0]) if len(parts) > 0 else 0
            target_m = int(parts[1]) if len(parts) > 1 else 0
            target_s = int(parts[2]) if len(parts) > 2 else 0
            cmd['status'] = CMD_STATUS_EXECUTING
            self.root.after(0, self.cmd_refresh_tree)

            while True:
                if self.cmd_stop_flag:
                    break
                while self.cmd_paused and not self.cmd_stop_flag:
                    time.sleep(0.5)
                if self.cmd_stop_flag:
                    break

                now = datetime.datetime.now()
                target = now.replace(hour=target_h, minute=target_m, second=target_s, microsecond=0)
                diff = target - now
                total_seconds = int(diff.total_seconds())
                
                if total_seconds <= 0:
                    break

                self.root.after(0, lambda s=total_seconds, n=cmd.get('name',''): self._update_cmd_status_message(
                    f"{n}: 定时倒计时 {s} 秒..."))
                self.root.after(0, self.cmd_refresh_tree)
                time.sleep(1)

            if self.cmd_stop_flag:
                cmd['status'] = CMD_STATUS_STOPPED
                self.root.after(0, self.cmd_refresh_tree)
                continue

        elif exec_mode == 'delayed':
            delay_seconds = self._parse_time_to_seconds(cmd.get('exec_time', '00:00:10'))
            cmd['status'] = CMD_STATUS_EXECUTING
            cmd['countdown_start_time'] = datetime.datetime.now()
            self.root.after(0, self.cmd_refresh_tree)
            for remaining in range(int(delay_seconds), 0, -1):
                if self.cmd_stop_flag:
                    break
                while self.cmd_paused and not self.cmd_stop_flag:
                    time.sleep(0.5)
                if self.cmd_stop_flag:
                    break
                self.root.after(0, lambda r=remaining, n=cmd.get('name',''): self._update_cmd_status_message(
                    f"{n}: 倒计时 {r} 秒..."))
                self.root.after(0, self.cmd_refresh_tree)
                time.sleep(1)

        if self.cmd_stop_flag:
            cmd['status'] = CMD_STATUS_STOPPED
            self.root.after(0, self.cmd_refresh_tree)
            break

        if not cmd.get('enabled', True):
            cmd['status'] = CMD_STATUS_COMPLETED
            self.root.after(0, self.cmd_refresh_tree)
            continue

        cmd['status'] = CMD_STATUS_EXECUTING
        self.root.after(0, self.cmd_refresh_tree)

        try:
            self._execute_single_command(cmd)
            if not self.cmd_stop_flag:
                cmd['status'] = CMD_STATUS_COMPLETED
            else:
                cmd['status'] = CMD_STATUS_STOPPED
        except SystemExit as e:
            print(f'[DEBUG _cmd_execute_thread] SystemExit (code: {e.code}): {cmd.get("name")}')
            cmd['status'] = CMD_STATUS_COMPLETED
        except Exception as e:
            print(f'[DEBUG _cmd_execute_thread] 异常: {e}')
            cmd['status'] = CMD_STATUS_COMPLETED

        self.root.after(0, self.cmd_refresh_tree)

    self.cmd_running = False
    self.root.after(0, lambda: self._update_cmd_status_message('命令列表执行完毕'))


def _execute_single_command(self, cmd):
    """执行单条命令"""
    import time
    import sys
    from io import StringIO

    cmd_name = cmd.get('name', '')
    print(f'[DEBUG _execute_single_command] 开始执行命令: {cmd_name}')

    template_name = cmd.get('template_name', '')
    print(f'[DEBUG _execute_single_command] template_name: {template_name}')

    tpl = self.cmd_templates.get(template_name, {}) if template_name else {}
    is_python_template = tpl.get('is_python_template', False)

    print(f'[DEBUG _execute_single_command] is_python_template: {is_python_template}')

    if template_name and is_python_template and template_name in self.cmd_templates:
        python_code = self.cmd_templates[template_name].get('python_code')
        print(f'[DEBUG _execute_single_command] 从模板 [{template_name}] 获取代码, 长度: {len(python_code) if python_code else 0}')
        if python_code:
            first_line = python_code.split('\n')[0] if '\n' in python_code else python_code[:100]
            print(f'[DEBUG _execute_single_command] 代码开头: {first_line}')
    elif cmd.get('python_code') and is_python_template:
        python_code = cmd.get('python_code')
        print(f'[DEBUG _execute_single_command] 从命令获取代码, 长度: {len(python_code) if python_code else 0}')
    else:
        python_code = None
        print(f'[DEBUG _execute_single_command] 非Python模板，执行工作流')

    if python_code:
        print(f'[DEBUG _execute_single_command] 进入 python_code 分支')
        
        old_code = python_code
        python_code = python_code.replace(
            "'workgroups', workgroup_id, 'pic'",
            "'workgroups', workgroup_id"
        )
        python_code = python_code.replace(
            "'workgroups', workgroup_id, \"pic\"",
            "'workgroups', workgroup_id"
        )
        if old_code != python_code:
            print(f'[DEBUG] 已修复图片路径: 移除了多余的pic子目录')
        
        self.root.after(0, lambda n=cmd_name: self._update_cmd_status_message(f"{n} - 执行Python脚本..."))
        
        # 提前初始化old_stdout，确保异常处理时可用
        old_stdout = sys.stdout
        
        try:
            coords = cmd.get('coords', [])
            print(f'[DEBUG _execute_single_command] coords: {coords}')
            coord_vars = {}
            for i, coord in enumerate(coords):
                coord_vars[f'x{i+1}'] = coord.get('x', 0)
                coord_vars[f'y{i+1}'] = coord.get('y', 0)
                coord_vars[f'coord{i+1}'] = (coord.get('x', 0), coord.get('y', 0))

            def should_stop():
                return self.cmd_stop_flag or self.cmd_paused

            class StoppablePyAutoGUI:
                def __init__(self, real_pya, stop_check):
                    self._pya = real_pya
                    self._stop_check = stop_check
                
                def _check_stop(self):
                    if self._stop_check():
                        raise KeyboardInterrupt("命令被停止")
                
                def click(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.click(*args, **kwargs)
                
                def doubleClick(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.doubleClick(*args, **kwargs)
                
                def rightClick(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.rightClick(*args, **kwargs)
                
                def moveTo(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.moveTo(*args, **kwargs)
                
                def moveRel(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.moveRel(*args, **kwargs)
                
                def dragTo(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.dragTo(*args, **kwargs)
                
                def dragRel(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.dragRel(*args, **kwargs)
                
                def scroll(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.scroll(*args, **kwargs)
                
                def typewrite(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.typewrite(*args, **kwargs)
                
                def write(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.write(*args, **kwargs)
                
                def press(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.press(*args, **kwargs)
                
                def hotkey(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.hotkey(*args, **kwargs)
                
                def screenshot(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.screenshot(*args, **kwargs)
                
                def locateOnScreen(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.locateOnScreen(*args, **kwargs)
                
                def locateCenterOnScreen(self, *args, **kwargs):
                    self._check_stop()
                    return self._pya.locateCenterOnScreen(*args, **kwargs)
                
                def __getattr__(self, name):
                    return getattr(self._pya, name)

            stoppable_pya = StoppablePyAutoGUI(pyautogui, should_stop)

            # 安全导入可选模块（可能未安装）
            def _safe_import(module_name):
                try:
                    return __import__(module_name)
                except ImportError:
                    return None

            exec_globals = {
                'pyautogui': stoppable_pya,
                'time': time,
                'pyperclip': _safe_import('pyperclip'),
                'keyboard': _safe_import('keyboard'),
                'random': __import__('random'),
                'pynput': _safe_import('pynput'),
                'numpy': _safe_import('numpy'),
                'cv2': _safe_import('cv2'),
                'os': __import__('os'),
                'coords': coords,
                'cmd': cmd,
                'should_stop': should_stop,
                **coord_vars,
                'coord_params': coords[0].get('raw', '0.0') if coords else '0.0',
                'workgroup_id': str(self.wg_info.get('id', '')),
                '__file__': __file__,
                '__name__': '__main__',
                '__builtins__': __builtins__
            }

            python_code = python_code.replace('{{workgroup_id}}', str(self.wg_info.get('id', '')))
            # 拼接所有坐标参数（用逗号分隔）
            all_params = ','.join([c.get('raw', '0.0') for c in coords]) if coords else '0.0'
            python_code = python_code.replace('{{coord_params}}', all_params)

            print(f"[DEBUG] workgroup_id: {self.wg_info.get('id', '')}")
            print(f"[DEBUG] 开始执行Python脚本, coord_params: {all_params}")

            # 实时输出流类：每收到一行就立即输出
            class RealtimeOutput:
                def __init__(self, original_stdout, update_func, cmd_name):
                    self.original_stdout = original_stdout
                    self.update_func = update_func
                    self.cmd_name = cmd_name
                    self.buffer = ""
                
                def write(self, text):
                    if text:
                        self.original_stdout.write(text)
                        self.original_stdout.flush()
                        # 实时更新UI
                        if text.strip():
                            self.update_func(f"  >> {text.strip()}")
                
                def flush(self):
                    self.original_stdout.flush()
            
            # 提前初始化old_stdout，避免异常时未定义
            old_stdout = sys.stdout
            realtime_output = RealtimeOutput(old_stdout, self._update_cmd_status_message, cmd_name)
            sys.stdout = realtime_output

            exec_completed = False
            exec_exit_code = None

            print(f"[DEBUG] 即将执行 exec(python_code)")
            try:
                exec(python_code, exec_globals)
                print(f"[DEBUG] exec(python_code) 执行完成")
                exec_completed = True
            except KeyboardInterrupt:
                print(f"[DEBUG] exec 被用户停止")
                sys.stdout = old_stdout
                raise KeyboardInterrupt("命令被停止")
            except SystemExit as e:
                print(f"[DEBUG] exec 正常退出 (exit code: {e.code})")
                sys.stdout = old_stdout
                exec_completed = True
                exec_exit_code = e.code
                self.root.after(0, lambda n=cmd_name: self._update_cmd_status_message(f"{n} - 执行完成"))
            except Exception as exec_err:
                print(f"[DEBUG] exec 异常: {exec_err}")
                sys.stdout = old_stdout
                raise

            sys.stdout = old_stdout

            print(f'[DEBUG _execute_single_command] exec_completed={exec_completed}, exec_exit_code={exec_exit_code}')
            if exec_completed and exec_exit_code == 0:
                print(f'[DEBUG _execute_single_command] 正常退出，返回')
                return

            self.root.after(0, lambda n=cmd_name: self._update_cmd_status_message(f"{n} - Python脚本执行完成"))
        except KeyboardInterrupt:
            print(f"[DEBUG] Python脚本被用户停止")
            sys.stdout = old_stdout
            self.root.after(0, lambda n=cmd_name: self._update_cmd_status_message(f"{n} - 已停止"))
            raise KeyboardInterrupt("命令被停止")
        except Exception as e:
            print(f"[DEBUG] Python脚本执行异常: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout = old_stdout
            self.root.after(0, lambda err=str(e), n=cmd_name: self._update_cmd_status_message(f"{n} - Python脚本执行失败: {err}"))
            raise

    coords = cmd.get('coords', [])
    template_names = cmd.get('workflows', [])
    auto_input = cmd.get('auto_input', False)

    print(f'[DEBUG _execute_single_command] coords={coords}, template_names={template_names}, auto_input={auto_input}')

    if not coords and not template_names:
        print(f'[DEBUG _execute_single_command] 警告: 命令没有coords和workflows，直接返回')
        return

    def should_stop():
        return self.cmd_stop_flag or self.cmd_paused

    class StoppablePyAutoGUI:
        def __init__(self, real_pya, stop_check):
            self._pya = real_pya
            self._stop_check = stop_check
        
        def _check_stop(self):
            if self._stop_check():
                raise KeyboardInterrupt("命令被停止")
        
        def click(self, *args, **kwargs):
            self._check_stop()
            return self._pya.click(*args, **kwargs)
        
        def doubleClick(self, *args, **kwargs):
            self._check_stop()
            return self._pya.doubleClick(*args, **kwargs)
        
        def rightClick(self, *args, **kwargs):
            self._check_stop()
            return self._pya.rightClick(*args, **kwargs)
        
        def moveTo(self, *args, **kwargs):
            self._check_stop()
            return self._pya.moveTo(*args, **kwargs)
        
        def screenshot(self, *args, **kwargs):
            self._check_stop()
            return self._pya.screenshot(*args, **kwargs)
        
        def locateOnScreen(self, *args, **kwargs):
            self._check_stop()
            return self._pya.locateOnScreen(*args, **kwargs)
        
        def __getattr__(self, name):
            return getattr(self._pya, name)

    stoppable_pya = StoppablePyAutoGUI(pyautogui, should_stop)

    for j, coord in enumerate(coords):
        if self.cmd_stop_flag:
            break
        while self.cmd_paused and not self.cmd_stop_flag:
            time.sleep(0.5)
        if self.cmd_stop_flag:
            break

        x, y = coord.get('x', 0), coord.get('y', 0)
        coord_label = coord.get('label', '坐标')
        coord_raw = coord.get('raw', f'{x}.{y}')

        self.root.after(0, lambda l=coord_label, cx=x, cy=y, n=cmd_name:
            self._update_cmd_status_message(f"{n} - 执行{l}: ({cx}, {cy})"))

        try:
            stoppable_pya.click(x, y)
            time.sleep(0.5)

            if auto_input and template_names:
                stoppable_pya.typewrite(str(x))
                time.sleep(0.3)
                stoppable_pya.press('tab')
                time.sleep(0.3)
                stoppable_pya.typewrite(str(y))
                time.sleep(0.5)

            for template_name in template_names:
                if self.cmd_stop_flag:
                    break
                while self.cmd_paused and not self.cmd_stop_flag:
                    time.sleep(0.5)
                if self.cmd_stop_flag:
                    break

                self.root.after(0, lambda t=template_name, n=cmd_name:
                    self._update_cmd_status_message(f"{n} - 执行模板: {t}"))

                try:
                    if template_name in self.cmd_templates:
                        tpl = self.cmd_templates[template_name]
                        python_code = tpl.get('python_code')
                        if python_code:
                            # 安全导入可选模块（可能未安装）
                            def _safe_import_tpl(module_name):
                                try:
                                    return __import__(module_name)
                                except ImportError:
                                    return None

                            exec_globals = {
                                'pyautogui': stoppable_pya,
                                'time': time,
                                'pyperclip': _safe_import_tpl('pyperclip'),
                                'keyboard': _safe_import_tpl('keyboard'),
                                'random': __import__('random'),
                                'pynput': _safe_import_tpl('pynput'),
                                'numpy': _safe_import_tpl('numpy'),
                                'cv2': _safe_import_tpl('cv2'),
                                'os': __import__('os'),
                                'coords': coords,
                                'cmd': cmd,
                                'x1': x, 'y1': y,
                                'coord1': (x, y),
                                'coord_params': coord_raw,
                                'should_stop': should_stop,
                                '__builtins__': __builtins__
                            }
                            exec(python_code, exec_globals)
                            self.root.after(0, lambda tname=template_name, n=cmd_name:
                                self._update_cmd_status_message(f"{n} - 模板 '{tname}' 执行完成"))
                        else:
                            self.root.after(0, lambda tname=template_name, n=cmd_name:
                                self._update_cmd_status_message(f"{n} - 模板 '{tname}' 无Python代码"))
                    else:
                        self.root.after(0, lambda tname=template_name, n=cmd_name:
                            self._update_cmd_status_message(f"{n} - 模板 '{tname}' 不存在"))
                except KeyboardInterrupt:
                    self.root.after(0, lambda n=cmd_name: self._update_cmd_status_message(f"{n} - 已停止"))
                    return
                except SystemExit as e:
                    print(f"[DEBUG] 模板 exec SystemExit (code: {e.code})")
                    self.root.after(0, lambda n=cmd_name: self._update_cmd_status_message(f"{n} - 执行完成"))
                    return
                except Exception as e:
                    self.root.after(0, lambda err=str(e), tname=template_name, n=cmd_name:
                        self._update_cmd_status_message(f"{n} - 模板 '{tname}' 执行失败: {err}"))

            if j < len(coords) - 1:
                time.sleep(1)

        except KeyboardInterrupt:
            self.root.after(0, lambda n=cmd_name: self._update_cmd_status_message(f"{n} - 已停止"))
            return
        except Exception as e:
            self.root.after(0, lambda err=str(e): self._update_cmd_status_message(f"执行出错: {err}"))


def _wait_until_time(self, time_str):
    """等待直到指定时钟时间（支持跨天）"""
    import time as time_module
    try:
        parts = time_str.split(':')
        target_h = int(parts[0])
        target_m = int(parts[1])
        target_s = int(parts[2]) if len(parts) > 2 else 0

        while True:
            if self.cmd_stop_flag:
                return False
            while self.cmd_paused and not self.cmd_stop_flag:
                time_module.sleep(0.5)
            if self.cmd_stop_flag:
                return False

            now = datetime.datetime.now()
            target = now.replace(hour=target_h, minute=target_m, second=target_s, microsecond=0)

            if now >= target:
                return True

            time_module.sleep(1)
    except Exception as e:
        print(f"解析定时时间失败: {e}")
        return False


def _parse_time_to_seconds(self, time_str):
    """将时间字符串转换为秒数"""
    try:
        parts = time_str.split(':')
        h = int(parts[0]) if len(parts) > 0 else 0
        m = int(parts[1]) if len(parts) > 1 else 0
        s = int(parts[2]) if len(parts) > 2 else 0
        return h * 3600 + m * 60 + s
    except Exception:
        return 10


def _update_cmd_status_message(self, msg):
    """更新指挥标签状态消息"""
    if hasattr(self, 'add_status_message'):
        self.add_status_message(f"[指挥] {msg}")
    else:
        print(f"[指挥] {msg}")


def _update_cmd_list_source(self):
    """更新命令列表来源标签"""
    if not hasattr(self, 'cmd_list_source_label'):
        return
    if self.wg_info.get('id'):
        wg_name = self.wg_info.get('name', '')
        role = self.wg_info.get('role', 'member')
        role_map = {'owner': '创建者', 'admin': '管理员', 'member': '组员'}
        role_display = role_map.get(role, role)
        count = len(self.cmd_list) if hasattr(self, 'cmd_list') and self.cmd_list else 0
        print(f'[DEBUG] _update_cmd_list_source: wg_id={self.wg_info["id"]}, count={count}, cmd_list={getattr(self, "cmd_list", "N/A")}')
        self.cmd_list_source_label.config(text=f'[服务端模式] {wg_name} ({role_display}) - {count}条命令', fg='#008800')
    else:
        print('[DEBUG] _update_cmd_list_source: 本地模式')
        self.cmd_list_source_label.config(text='[本地模式] 未加入工作组', fg='gray')


# 项目标签页
def create_projects_tab(self):
    """创建项目标签页"""
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text='项目')
    
    # 管理按钮
    btn_frame = ttk.Frame(tab)
    btn_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Button(btn_frame, text='创建项目', command=self.create_project).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='切换项目', command=self.switch_project).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='打包项目', command=self.pack_project).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='解包项目', command=self.unpack_project).pack(side=tk.LEFT, padx=5)
    
    # 当前项目信息
    current_frame = ttk.LabelFrame(tab, text='当前项目')
    current_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 项目名称
    name_frame = ttk.Frame(current_frame)
    name_frame.pack(fill=tk.X, padx=5, pady=2)
    ttk.Label(name_frame, text='当前项目:').pack(side=tk.LEFT, padx=5)
    self.current_project_name_label = ttk.Label(name_frame, text=self.project_manager.get_current_project())
    self.current_project_name_label.pack(side=tk.LEFT, padx=5)
    
    # 版本
    version_frame = ttk.Frame(current_frame)
    version_frame.pack(fill=tk.X, padx=5, pady=2)
    ttk.Label(version_frame, text='版本:').pack(side=tk.LEFT, padx=5)
    self.current_project_version_edit = ttk.Entry(version_frame, state='disabled')
    self.current_project_version_edit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # 项目目录
    path_frame = ttk.Frame(current_frame)
    path_frame.pack(fill=tk.X, padx=5, pady=2)
    ttk.Label(path_frame, text='项目指定目录:').pack(side=tk.LEFT, padx=5)
    self.current_project_path_label = ttk.Label(path_frame, text='', wraplength=500)
    self.current_project_path_label.pack(side=tk.LEFT, padx=5)
    
    # 创建日期
    created_frame = ttk.Frame(current_frame)
    created_frame.pack(fill=tk.X, padx=5, pady=2)
    ttk.Label(created_frame, text='创建日期:').pack(side=tk.LEFT, padx=5)
    self.current_project_created_edit = ttk.Entry(created_frame, state='disabled')
    self.current_project_created_edit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # 对应程序
    program_frame = ttk.Frame(current_frame)
    program_frame.pack(fill=tk.X, padx=5, pady=2)
    ttk.Label(program_frame, text='对应程序:').pack(side=tk.LEFT, padx=5)
    self.current_project_program_edit = ttk.Entry(program_frame, state='disabled')
    self.current_project_program_edit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # 屏幕分辨率
    resolution_frame = ttk.Frame(current_frame)
    resolution_frame.pack(fill=tk.X, padx=5, pady=2)
    ttk.Label(resolution_frame, text='屏幕分辨率:').pack(side=tk.LEFT, padx=5)
    self.current_project_resolution_combo = ttk.Combobox(resolution_frame, state='disabled', 
                                                          values=['1920*1080(推荐)', '2560*1440(2K)', 
                                                                 '3840*2160(4K)', '960*540(模拟器)'])
    self.current_project_resolution_combo.pack(side=tk.LEFT, padx=5)
    
    self.current_project_resolution_custom = ttk.Entry(resolution_frame, state='disabled')
    self.current_project_resolution_custom.pack(side=tk.LEFT, padx=5)
    
    # 备注
    notes_frame = ttk.Frame(current_frame)
    notes_frame.pack(fill=tk.X, padx=5, pady=2)
    ttk.Label(notes_frame, text='备注:').pack(side=tk.LEFT, padx=5)
    self.current_project_notes_edit = scrolledtext.ScrolledText(notes_frame, height=3, state='disabled')
    self.current_project_notes_edit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # 编辑和保存按钮
    edit_frame = ttk.Frame(current_frame)
    edit_frame.pack(fill=tk.X, padx=5, pady=2)
    
    self.edit_project_button = ttk.Button(edit_frame, text='编辑', command=self.edit_current_project)
    self.edit_project_button.pack(side=tk.LEFT, padx=5)
    
    self.save_project_button = ttk.Button(edit_frame, text='保存', command=self.save_current_project, state='disabled')
    self.save_project_button.pack(side=tk.LEFT, padx=5)
    
    # 项目列表
    self.project_list = tk.Listbox(tab)
    self.project_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    self.project_list.bind('<<ListboxSelect>>', lambda e: self.on_project_selected())
    self.load_projects()


# 日常任务标签页
def create_daily_tasks_tab(self):
    """创建日常任务标签页"""
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text='日常任务')
    
    # 全局设置
    global_frame = ttk.LabelFrame(tab, text='全局设置')
    global_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 循环执行
    loop_frame = ttk.Frame(global_frame)
    loop_frame.pack(fill=tk.X, padx=5, pady=2)
    
    self.daily_tasks_main_switch_var = tk.BooleanVar(value=getattr(self.config, 'daily_tasks_main_switch_enabled', True))
    ttk.Checkbutton(loop_frame, text='总开关', variable=self.daily_tasks_main_switch_var,
                   command=self.on_daily_tasks_main_switch_changed).pack(side=tk.LEFT, padx=5)
    
    self.daily_loop_all_var = tk.BooleanVar(value=getattr(self.config, 'daily_tasks_loop_enabled', False))
    ttk.Checkbutton(loop_frame, text='循环执行', variable=self.daily_loop_all_var,
                   command=self.on_loop_all_changed).pack(side=tk.LEFT, padx=5)
    
    ttk.Label(loop_frame, text='执行遍数:').pack(side=tk.LEFT, padx=5)
    self.daily_repeat_count_var = tk.IntVar(value=getattr(self.config, 'daily_tasks_repeat_count', 1))
    ttk.Spinbox(loop_frame, from_=1, to=100, textvariable=self.daily_repeat_count_var,
               width=8, command=self.on_global_repeat_count_changed).pack(side=tk.LEFT, padx=5)
    
    # 时间设置
    time_frame = ttk.Frame(global_frame)
    time_frame.pack(fill=tk.X, padx=5, pady=2)
    
    self.daily_time_mode_var = tk.StringVar(value=getattr(self.config, 'daily_tasks_time_mode', 'none'))
    
    ttk.Radiobutton(time_frame, text='立即执行', variable=self.daily_time_mode_var, 
                   value='none', command=self.on_global_time_mode_changed).pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(time_frame, text='定时执行', variable=self.daily_time_mode_var,
                   value='schedule', command=self.on_global_time_mode_changed).pack(side=tk.LEFT, padx=5)
    ttk.Radiobutton(time_frame, text='延时执行', variable=self.daily_time_mode_var,
                   value='delay', command=self.on_global_time_mode_changed).pack(side=tk.LEFT, padx=5)
    
    # 任务管理
    task_frame = ttk.LabelFrame(tab, text='任务管理')
    task_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 管理按钮
    btn_frame = ttk.Frame(task_frame)
    btn_frame.pack(fill=tk.X, padx=5, pady=2)
    
    ttk.Button(btn_frame, text='添加任务', command=self.add_daily_task).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='编辑任务', command=self.edit_daily_task).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='删除任务', command=self.delete_daily_task).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='上移', command=self.move_daily_task_up).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='下移', command=self.move_daily_task_down).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='立即执行', command=self.execute_daily_tasks_now).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='停止执行', command=self.stop_all_daily_tasks).pack(side=tk.LEFT, padx=5)
    
    # 日常任务表格
    columns = ('启用', '工作流名称', '遍数', '状态')
    self.daily_task_table = ttk.Treeview(task_frame, columns=columns, show='headings', height=15)
    
    for col in columns:
        self.daily_task_table.heading(col, text=col)
        self.daily_task_table.column(col, width=100)
    
    # 添加滚动条
    scrollbar = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.daily_task_table.yview)
    self.daily_task_table.configure(yscrollcommand=scrollbar.set)
    
    self.daily_task_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
    
    self.load_daily_tasks_list()


# 答题系统标签页
def create_answer_system_tab(self):
    """创建答题系统标签页"""
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text='答题')
    
    # 全局设置
    global_frame = ttk.LabelFrame(tab, text='全局设置')
    global_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 循环执行
    loop_frame = ttk.Frame(global_frame)
    loop_frame.pack(fill=tk.X, padx=5, pady=2)
    
    self.answer_tasks_main_switch_var = tk.BooleanVar(value=getattr(self.config, 'answer_tasks_main_switch_enabled', True))
    ttk.Checkbutton(loop_frame, text='总开关', variable=self.answer_tasks_main_switch_var,
                   command=self.on_answer_tasks_main_switch_changed).pack(side=tk.LEFT, padx=5)
    
    self.answer_loop_all_var = tk.BooleanVar(value=getattr(self.config, 'answer_tasks_loop_enabled', False))
    ttk.Checkbutton(loop_frame, text='循环执行', variable=self.answer_loop_all_var,
                   command=self.on_answer_loop_all_changed).pack(side=tk.LEFT, padx=5)
    
    ttk.Label(loop_frame, text='执行遍数:').pack(side=tk.LEFT, padx=5)
    self.answer_repeat_count_var = tk.IntVar(value=getattr(self.config, 'answer_tasks_repeat_count', 1))
    ttk.Spinbox(loop_frame, from_=1, to=100, textvariable=self.answer_repeat_count_var,
               width=8, command=self.on_answer_repeat_count_changed).pack(side=tk.LEFT, padx=5)
    
    # 任务管理
    task_frame = ttk.LabelFrame(tab, text='任务管理')
    task_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 管理按钮
    btn_frame = ttk.Frame(task_frame)
    btn_frame.pack(fill=tk.X, padx=5, pady=2)
    
    ttk.Button(btn_frame, text='添加任务', command=self.add_answer_task).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='编辑任务', command=self.edit_answer_task).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='删除任务', command=self.delete_answer_task).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='上移', command=self.move_answer_task_up).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='下移', command=self.move_answer_task_down).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='立即执行', command=self.execute_answer_tasks_now).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='停止执行', command=self.stop_all_answer_tasks).pack(side=tk.LEFT, padx=5)
    
    # 答题任务表格
    columns = ('启用', '工作流名称', '遍数', '状态')
    self.answer_task_table = ttk.Treeview(task_frame, columns=columns, show='headings', height=15)
    
    for col in columns:
        self.answer_task_table.heading(col, text=col)
        self.answer_task_table.column(col, width=100)
    
    # 添加滚动条
    scrollbar = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.answer_task_table.yview)
    self.answer_task_table.configure(yscrollcommand=scrollbar.set)
    
    self.answer_task_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
    
    self.load_answer_tasks_list()


# 发现即点标签页
def create_discovery_click_tab(self):
    """创建发现即点标签页"""
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text='发现即点')
    
    # 全局设置
    global_frame = ttk.LabelFrame(tab, text='全局设置')
    global_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 循环执行
    loop_frame = ttk.Frame(global_frame)
    loop_frame.pack(fill=tk.X, padx=5, pady=2)
    
    self.discovery_tasks_main_switch_var = tk.BooleanVar(value=getattr(self.config, 'discovery_tasks_main_switch_enabled', True))
    ttk.Checkbutton(loop_frame, text='总开关', variable=self.discovery_tasks_main_switch_var,
                   command=self.on_discovery_tasks_main_switch_changed).pack(side=tk.LEFT, padx=5)
    
    self.discovery_loop_all_var = tk.BooleanVar(value=getattr(self.config, 'discovery_tasks_loop_enabled', False))
    ttk.Checkbutton(loop_frame, text='循环执行', variable=self.discovery_loop_all_var,
                   command=self.on_discovery_loop_all_changed).pack(side=tk.LEFT, padx=5)
    
    ttk.Label(loop_frame, text='执行遍数:').pack(side=tk.LEFT, padx=5)
    self.discovery_repeat_count_var = tk.IntVar(value=getattr(self.config, 'discovery_tasks_repeat_count', 1))
    ttk.Spinbox(loop_frame, from_=1, to=100, textvariable=self.discovery_repeat_count_var,
               width=8, command=self.on_discovery_repeat_count_changed).pack(side=tk.LEFT, padx=5)
    
    # 任务管理
    task_frame = ttk.LabelFrame(tab, text='任务管理')
    task_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # 管理按钮
    btn_frame = ttk.Frame(task_frame)
    btn_frame.pack(fill=tk.X, padx=5, pady=2)
    
    ttk.Button(btn_frame, text='添加任务', command=self.add_discovery_task).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='编辑任务', command=self.edit_discovery_task).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='删除任务', command=self.delete_discovery_task).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='上移', command=self.move_discovery_task_up).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='下移', command=self.move_discovery_task_down).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='立即执行', command=self.execute_discovery_tasks_now).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='停止执行', command=self.stop_all_discovery_tasks).pack(side=tk.LEFT, padx=5)
    
    # 发现即点任务表格
    columns = ('启用', '工作流名称', '遍数', '状态')
    self.discovery_task_table = ttk.Treeview(task_frame, columns=columns, show='headings', height=15)
    
    for col in columns:
        self.discovery_task_table.heading(col, text=col)
        self.discovery_task_table.column(col, width=100)
    
    # 添加滚动条
    scrollbar = ttk.Scrollbar(task_frame, orient=tk.VERTICAL, command=self.discovery_task_table.yview)
    self.discovery_task_table.configure(yscrollcommand=scrollbar.set)
    
    self.discovery_task_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
    
    self.load_discovery_tasks_list()


# 激活标签页
def create_activation_tab(self):
    """创建激活系统标签页"""
    tab = ttk.Frame(self.notebook)
    self.notebook.add(tab, text='激活')
    
    # 服务器配置 - 优先从配置文件读取，否则使用默认值
    self.activation_server_url = self._get_activation_server_url()
    
    # 配置文件路径
    self.activation_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    self.activation_config_file = os.path.join(self.activation_data_dir, 'activation_config.json')
    
    # 激活管理器
    self.activation_manager = None
    self.sync_timer = None
    
    # 每日试用相关
    self.daily_trial_timer = None
    self.daily_trial_active = False
    self.tabs_locked = True  # 默认锁定，登录后解锁
    self.program_start_time = datetime.datetime.now()  # 程序启动时间
    self.trial_session_started = False  # 本次会话试用是否已开始
    
    # 确保data目录存在
    if not os.path.exists(self.activation_data_dir):
        os.makedirs(self.activation_data_dir)
    
    # ==================== 登录区域 ====================
    login_frame = ttk.LabelFrame(tab, text='用户登录')
    login_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 用户名
    username_frame = ttk.Frame(login_frame)
    username_frame.pack(fill=tk.X, padx=5, pady=2)
    ttk.Label(username_frame, text='用户名:').pack(side=tk.LEFT, padx=5)
    self.activation_username_edit = ttk.Entry(username_frame, width=30)
    self.activation_username_edit.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    # 密码
    password_frame = ttk.Frame(login_frame)
    password_frame.pack(fill=tk.X, padx=5, pady=2)
    ttk.Label(password_frame, text='密码:').pack(side=tk.LEFT, padx=5)
    self.activation_password_edit = ttk.Entry(password_frame, width=30, show='*')
    self.activation_password_edit.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    # 保存密码选项
    self.save_password_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(login_frame, text='保存密码', variable=self.save_password_var).pack(anchor=tk.W, padx=5, pady=2)
    
    # 登录按钮
    login_btn_frame = ttk.Frame(login_frame)
    login_btn_frame.pack(fill=tk.X, padx=5, pady=5)
    
    login_btn = ttk.Button(login_btn_frame, text='登录', command=self.on_activation_login)
    login_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    logout_btn = ttk.Button(login_btn_frame, text='退出登录', command=self.on_activation_logout)
    logout_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    register_btn = ttk.Button(login_btn_frame, text='注册', command=self.on_activation_register)
    register_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
    
    # ==================== 激活状态区域 ====================
    status_frame = ttk.LabelFrame(tab, text='激活状态')
    status_frame.pack(fill=tk.X, padx=5, pady=5)
    
    self.activation_status_label = ttk.Label(status_frame, text='未登录', foreground='red')
    self.activation_status_label.pack(pady=5)
    
    self.days_remaining_label = ttk.Label(status_frame, text='剩余天数: -')
    self.days_remaining_label.pack(pady=2)
    
    self.activation_expiry_label = ttk.Label(status_frame, text='有效期至: -')
    self.activation_expiry_label.pack(pady=2)
    
    # ==================== 每日免费试用状态区域 ====================
    self.trial_status_frame = ttk.LabelFrame(tab, text='每日免费试用')
    self.trial_status_frame.pack(fill=tk.X, padx=5, pady=5)
    
    self.trial_status_label = ttk.Label(self.trial_status_frame, text='未登录', foreground='gray')
    self.trial_status_label.pack(pady=2)
    
    self.trial_countdown_label = ttk.Label(self.trial_status_frame, text='剩余时间: --:--:--', foreground='#007bff')
    self.trial_countdown_label.pack(pady=2)
    
    self.trial_hint_label = ttk.Label(self.trial_status_frame, text='登录后启动每日1小时免费试用', foreground='gray')
    self.trial_hint_label.pack(pady=2)
    
    # ==================== 功能按钮区域 ====================
    actions_frame = ttk.LabelFrame(tab, text='功能操作')
    actions_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # 购买激活码按钮
    purchase_btn = ttk.Button(actions_frame, text='购买激活码', command=self.on_activation_purchase)
    purchase_btn.pack(fill=tk.X, padx=5, pady=2)
    
    # 激活使用按钮
    activate_btn = ttk.Button(actions_frame, text='激活使用', command=self.on_activation_activate)
    activate_btn.pack(fill=tk.X, padx=5, pady=2)
    
    # 同步状态按钮
    sync_btn = ttk.Button(actions_frame, text='同步状态', command=self.on_activation_sync)
    sync_btn.pack(fill=tk.X, padx=5, pady=2)
    
    # 报障按钮
    ticket_btn = ttk.Button(actions_frame, text='报障', command=self.on_activation_ticket)
    ticket_btn.pack(fill=tk.X, padx=5, pady=2)
    
    # ==================== 底部联系信息 ====================
    contact_frame = ttk.Frame(tab)
    contact_frame.pack(fill=tk.X, padx=5, pady=(10, 5))
    contact_label = ttk.Label(contact_frame, text='如有本软件有问题，或有意合作推广，可以直接联系ZQ工作室：pii3232（微信和Q号相同）', foreground='gray', anchor='center')
    contact_label.pack(fill=tk.X)
    
    # 加载保存的用户名和密码
    self.load_activation_config()
    
    # 自动尝试登录（延迟500ms）
    self.root.after(500, self.auto_activation_login)
    
    # 启动定时同步（每24小时同步一次）
    self.activation_sync_timer_id = self.root.after(86400000, self.on_activation_auto_sync)
    
    # 启动每日试用倒计时定时器（每5秒更新）
    self.daily_trial_timer_id = self.root.after(5000, self.on_daily_trial_tick)


# 编辑对话框类(简化版本)
class CommandEditDialog:
    """命令编辑对话框"""
    def __init__(self, parent, cmd, templates, workflows):
        import datetime
        self.dialog = tk.Toplevel(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.title('编辑命令')
        self.dialog.geometry('600x550')
        self.dialog.transient(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.grab_set()
        self.result = None
        self.cmd = cmd or {}
        self.templates = templates
        self.workflows = workflows

        all_items = []
        seen = set()
        for w in workflows:
            name = w.get('name', '')
            if name and name not in seen:
                all_items.append(name)
                seen.add(name)
        for t in templates.keys():
            if t not in seen:
                all_items.append(t)
                seen.add(t)

        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(main_frame, text='编辑命令', font=('', 12, 'bold')).pack(pady=5)

        form_frame = ttk.Frame(main_frame)
        form_frame.pack(fill=tk.X, pady=5)

        ttk.Label(form_frame, text='名称:').grid(row=0, column=0, sticky=tk.W, pady=3)
        self.name_entry = ttk.Entry(form_frame, width=35)
        self.name_entry.grid(row=0, column=1, pady=3, padx=5)
        self.name_entry.insert(0, cmd.get('name', ''))

        ttk.Label(form_frame, text='模板:').grid(row=1, column=0, sticky=tk.W, pady=3)
        self.template_combo = ttk.Combobox(form_frame, values=list(templates.keys()), width=33, state='readonly')
        self.template_combo.grid(row=1, column=1, pady=3, padx=5)
        self.template_combo.insert(0, cmd.get('template_name', ''))

        ttk.Label(form_frame, text='坐标:').grid(row=2, column=0, sticky=tk.W, pady=3)
        coords_frame = ttk.Frame(form_frame)
        coords_frame.grid(row=2, column=1, pady=3, padx=5)
        self.coords_text = tk.Text(coords_frame, height=3, width=35)
        self.coords_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        coords = cmd.get('coords', [])
        if coords:
            raw_texts = []
            for c in coords:
                raw = c.get('raw', '')
                if raw:
                    raw_texts.append(raw)
                else:
                    raw_texts.append(f"{c.get('x', 0)}.{c.get('y', 0)}")
            self.coords_text.insert('1.0', '\n'.join(raw_texts))

        ttk.Label(form_frame, text='工作流:').grid(row=3, column=0, sticky=tk.W, pady=3)
        wf_frame = ttk.Frame(form_frame)
        wf_frame.grid(row=3, column=1, pady=3, padx=5)
        self.wf_listbox = tk.Listbox(wf_frame, height=3, font=('Consolas', 9))
        self.wf_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        wf_scroll = ttk.Scrollbar(wf_frame, orient=tk.VERTICAL, command=self.wf_listbox.yview)
        wf_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.wf_listbox.config(yscrollcommand=wf_scroll.set)
        for wf in cmd.get('workflows', []):
            self.wf_listbox.insert(tk.END, wf)
        self.wf_add_combo = ttk.Combobox(wf_frame, values=all_items, width=15)
        self.wf_add_combo.pack(side=tk.LEFT, padx=(0, 2), fill=tk.X, expand=True)
        ttk.Button(wf_frame, text='+', width=3, command=self._add_wf).pack(side=tk.LEFT)
        ttk.Button(wf_frame, text='-', width=3, command=self._remove_wf).pack(side=tk.LEFT)

        ttk.Label(form_frame, text='执行模式:').grid(row=4, column=0, sticky=tk.W, pady=3)
        exec_frame = ttk.Frame(form_frame)
        exec_frame.grid(row=4, column=1, pady=3, padx=5, sticky=tk.W)
        self.exec_mode_var = tk.StringVar(value='delayed')
        ttk.Radiobutton(exec_frame, text='立即', variable=self.exec_mode_var, value='immediate').pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(exec_frame, text='定时', variable=self.exec_mode_var, value='scheduled').pack(side=tk.LEFT, padx=2)
        ttk.Radiobutton(exec_frame, text='延时', variable=self.exec_mode_var, value='delayed').pack(side=tk.LEFT, padx=2)
        self.time_entry = ttk.Entry(exec_frame, width=10)
        self.time_entry.pack(side=tk.LEFT, padx=2)

        current_exec_mode = cmd.get('exec_mode', 'delayed')
        self.exec_mode_var.set(current_exec_mode)
        existing_time = cmd.get('exec_time', '')
        if existing_time and existing_time.strip():
            self.time_entry.insert(0, existing_time)
        elif current_exec_mode == 'delayed':
            self.time_entry.insert(0, '00:00:10')
        else:
            now = datetime.datetime.now()
            scheduled_time = now + datetime.timedelta(minutes=5)
            self.time_entry.insert(0, scheduled_time.strftime('%H:%M:%S'))

        self.exec_mode_var.trace('w', self._on_exec_mode_changed)

        ttk.Label(form_frame, text='启用状态:').grid(row=5, column=0, sticky=tk.W, pady=3)
        enabled_frame = ttk.Frame(form_frame)
        enabled_frame.grid(row=5, column=1, pady=3, padx=5, sticky=tk.W)
        self.enabled_var = tk.BooleanVar(value=cmd.get('enabled', True))
        ttk.Checkbutton(enabled_frame, text='启用', variable=self.enabled_var).pack(side=tk.LEFT)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        ttk.Button(btn_frame, text='确定', command=self.ok).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text='取消', command=self.cancel).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def _on_exec_mode_changed(self, *args):
        mode = self.exec_mode_var.get()
        self.time_entry.delete(0, tk.END)
        if mode == 'delayed':
            self.time_entry.insert(0, '00:00:10')
        else:
            now = datetime.datetime.now()
            scheduled_time = now + datetime.timedelta(minutes=5)
            self.time_entry.insert(0, scheduled_time.strftime('%H:%M:%S'))

    def _add_wf(self):
        wf = self.wf_add_combo.get().strip()
        if wf:
            self.wf_listbox.insert(tk.END, wf)

    def _remove_wf(self):
        sel = self.wf_listbox.curselection()
        if sel:
            self.wf_listbox.delete(sel)

    def ok(self):
        workflows = []
        for i in range(self.wf_listbox.size()):
            workflows.append(self.wf_listbox.get(i))

        coords = []
        coords_text = self.coords_text.get('1.0', tk.END).strip()
        if coords_text:
            for line in coords_text.split('\n'):
                line = line.strip()
                if line:
                    parts = line.split('.')
                    if len(parts) >= 2:
                        try:
                            x = float(parts[0])
                            y = float(parts[1])
                            coords.append({'x': x, 'y': y, 'raw': line})
                        except:
                            pass

        self.result = {
            'name': self.name_entry.get().strip(),
            'template_name': self.template_combo.get().strip(),
            'coords': coords,
            'workflows': workflows,
            'exec_mode': self.exec_mode_var.get(),
            'exec_time': self.time_entry.get().strip(),
            'enabled': self.enabled_var.get(),
            'status': self.cmd.get('status', 'pending')
        }
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()


class WorkflowEditDialog:
    """工作流编辑对话框"""
    def __init__(self, parent, workflow=None):
        self.dialog = tk.Toplevel(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.title('编辑工作流')
        self.dialog.geometry('800x600')
        self.result = None
        self.workflow = workflow or {}
        
        # 名称
        name_frame = ttk.Frame(self.dialog)
        name_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(name_frame, text='工作流名称:').pack(side=tk.LEFT, padx=5)
        self.name_entry = ttk.Entry(name_frame, width=40)
        self.name_entry.insert(0, self.workflow.get('name', ''))
        self.name_entry.pack(side=tk.LEFT, padx=5)
        
        # 步骤编辑区域(简化版本)
        steps_frame = ttk.LabelFrame(self.dialog, text='步骤')
        steps_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.steps_text = scrolledtext.ScrolledText(steps_frame, height=20)
        self.steps_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 显示现有步骤
        steps = self.workflow.get('steps', [])
        for step in steps:
            keyword = step.get('keyword', '')
            params = step.get('params', '')
            self.steps_text.insert(tk.END, f'{keyword}|{params}\n')
        
        # 按钮
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text='确定', command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='取消', command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.dialog.transient(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.grab_set()
        
    def ok(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning('警告', '请输入工作流名称')
            return
        
        # 解析步骤
        steps_text = self.steps_text.get('1.0', tk.END).strip()
        steps = []
        for line in steps_text.split('\n'):
            if '|' in line:
                parts = line.split('|', 1)
                keyword = parts[0].strip()
                params = parts[1].strip() if len(parts) > 1 else ''
                steps.append({'keyword': keyword, 'params': params})
        
        self.result = {
            'name': name,
            'steps': steps
        }
        self.dialog.destroy()
        
    def cancel(self):
        self.dialog.destroy()


class DailyTaskEditDialog:
    """日常任务编辑对话框"""
    def __init__(self, parent, task=None, workflows=None):
        self.dialog = tk.Toplevel(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.title('编辑日常任务')
        self.dialog.geometry('600x400')
        self.result = None
        self.task = task or {}
        self.workflows = workflows or []
        
        # 工作流选择
        wf_frame = ttk.Frame(self.dialog)
        wf_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(wf_frame, text='工作流:').pack(side=tk.LEFT, padx=5)
        self.workflow_combo = ttk.Combobox(wf_frame, values=[w['name'] for w in self.workflows], width=40)
        self.workflow_combo.insert(0, self.task.get('workflow', ''))
        self.workflow_combo.pack(side=tk.LEFT, padx=5)
        
        # 执行遍数
        repeat_frame = ttk.Frame(self.dialog)
        repeat_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(repeat_frame, text='执行遍数:').pack(side=tk.LEFT, padx=5)
        self.repeat_spin = ttk.Spinbox(repeat_frame, from_=1, to=100, width=10)
        self.repeat_spin.delete(0, tk.END)
        self.repeat_spin.insert(0, str(self.task.get('repeat_count', 1)))
        self.repeat_spin.pack(side=tk.LEFT, padx=5)
        
        # 按钮
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text='确定', command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='取消', command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.dialog.transient(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.grab_set()
        
    def ok(self):
        workflow = self.workflow_combo.get().strip()
        if not workflow:
            messagebox.showwarning('警告', '请选择工作流')
            return
        
        self.result = {
            'workflow': workflow,
            'repeat_count': int(self.repeat_spin.get()),
            'enabled': True
        }
        self.dialog.destroy()
        
    def cancel(self):
        self.dialog.destroy()


class AnswerTaskEditDialog:
    """答题任务编辑对话框"""
    def __init__(self, parent, task=None, workflows=None):
        self.dialog = tk.Toplevel(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.title('编辑答题任务')
        self.dialog.geometry('600x400')
        self.result = None
        self.task = task or {}
        self.workflows = workflows or []
        
        # 工作流选择
        wf_frame = ttk.Frame(self.dialog)
        wf_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(wf_frame, text='工作流:').pack(side=tk.LEFT, padx=5)
        self.workflow_combo = ttk.Combobox(wf_frame, values=[w['name'] for w in self.workflows], width=40)
        self.workflow_combo.insert(0, self.task.get('workflow', ''))
        self.workflow_combo.pack(side=tk.LEFT, padx=5)
        
        # 执行遍数
        repeat_frame = ttk.Frame(self.dialog)
        repeat_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(repeat_frame, text='执行遍数:').pack(side=tk.LEFT, padx=5)
        self.repeat_spin = ttk.Spinbox(repeat_frame, from_=1, to=100, width=10)
        self.repeat_spin.delete(0, tk.END)
        self.repeat_spin.insert(0, str(self.task.get('repeat_count', 1)))
        self.repeat_spin.pack(side=tk.LEFT, padx=5)
        
        # 按钮
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text='确定', command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='取消', command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.dialog.transient(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.grab_set()
        
    def ok(self):
        workflow = self.workflow_combo.get().strip()
        if not workflow:
            messagebox.showwarning('警告', '请选择工作流')
            return
        
        self.result = {
            'workflow': workflow,
            'repeat_count': int(self.repeat_spin.get()),
            'enabled': True
        }
        self.dialog.destroy()
        
    def cancel(self):
        self.dialog.destroy()


class DiscoveryTaskEditDialog:
    """发现即点任务编辑对话框"""
    def __init__(self, parent, task=None, workflows=None):
        self.dialog = tk.Toplevel(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.title('编辑发现即点任务')
        self.dialog.geometry('600x400')
        self.result = None
        self.task = task or {}
        self.workflows = workflows or []
        
        # 工作流选择
        wf_frame = ttk.Frame(self.dialog)
        wf_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(wf_frame, text='工作流:').pack(side=tk.LEFT, padx=5)
        self.workflow_combo = ttk.Combobox(wf_frame, values=[w['name'] for w in self.workflows], width=40)
        self.workflow_combo.insert(0, self.task.get('workflow', ''))
        self.workflow_combo.pack(side=tk.LEFT, padx=5)
        
        # 执行遍数
        repeat_frame = ttk.Frame(self.dialog)
        repeat_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(repeat_frame, text='执行遍数:').pack(side=tk.LEFT, padx=5)
        self.repeat_spin = ttk.Spinbox(repeat_frame, from_=1, to=100, width=10)
        self.repeat_spin.delete(0, tk.END)
        self.repeat_spin.insert(0, str(self.task.get('repeat_count', 1)))
        self.repeat_spin.pack(side=tk.LEFT, padx=5)
        
        # 按钮
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text='确定', command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text='取消', command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.dialog.transient(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.grab_set()
        
    def ok(self):
        workflow = self.workflow_combo.get().strip()
        if not workflow:
            messagebox.showwarning('警告', '请选择工作流')
            return
        
        self.result = {
            'workflow': workflow,
            'repeat_count': int(self.repeat_spin.get()),
            'enabled': True
        }
        self.dialog.destroy()
        
    def cancel(self):
        self.dialog.destroy()


# ==================== 激活系统 - 激活管理器 ====================
class ActivationManager:
    """激活管理器"""

    def __init__(self, username):
        self.username = username
        self.expires_at = None
        self.days_remaining = 0
        # 每日免费试用相关属性
        self.daily_trial_date = None  # 最后试用日期 (YYYY-MM-DD)
        self.daily_trial_remaining_seconds = 3600  # 剩余试用秒数（默认1小时）
        self.daily_trial_start_time = None  # 本次试用开始时间
        self.daily_trial_flag = None  # 加密标志（用于判断是否第一次进入）
        self.first_run_today = False  # 标记今天是否是第一次运行

    def _get_server_url(self):
        """获取激活服务器地址"""
        return "https://9793tg1lo456.vicp.fun"

    def load_from_local(self):
        """从本地加载激活信息"""
        try:
            activation_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
            config_file = os.path.join(activation_data_dir, 'activation_config.json')

            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    expires_at_str = config.get(f'activation_{self.username}')
                    if expires_at_str:
                        self.expires_at = datetime.datetime.fromisoformat(expires_at_str)
                        self.update_days_remaining()
                    # 加载每日试用数据
                    trial_key = f'daily_trial_{self.username}'
                    trial_data = config.get(trial_key, {})
                    if trial_data:
                        self.daily_trial_date = trial_data.get('date')
                        self.daily_trial_remaining_seconds = trial_data.get('remaining_seconds', 3600)
                        self.daily_trial_flag = trial_data.get('flag')
                        start_time_str = trial_data.get('start_time')
                        if start_time_str:
                            try:
                                self.daily_trial_start_time = datetime.datetime.fromisoformat(start_time_str)
                            except:
                                self.daily_trial_start_time = None
                        self.first_run_today = trial_data.get('first_run_today', False)
        except Exception as e:
            print(f"加载激活信息失败: {e}")

    def save_to_local(self):
        """保存激活信息到本地"""
        try:
            import hashlib
            import uuid
            
            activation_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
            if not os.path.exists(activation_data_dir):
                os.makedirs(activation_data_dir)

            config_file = os.path.join(activation_data_dir, 'activation_config.json')

            # 加载现有配置
            config = {}
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            # 保存激活信息
            if self.expires_at:
                config[f'activation_{self.username}'] = self.expires_at.isoformat()

            # 保存每日试用数据
            trial_key = f'daily_trial_{self.username}'
            config[trial_key] = {
                'date': self.daily_trial_date,
                'remaining_seconds': self.daily_trial_remaining_seconds,
                'flag': self.daily_trial_flag,
                'start_time': self.daily_trial_start_time.isoformat() if self.daily_trial_start_time else None,
                'first_run_today': self.first_run_today
            }

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存激活信息失败: {e}")

    def update_days_remaining(self):
        """更新剩余天数"""
        if self.expires_at:
            remaining = self.expires_at - datetime.datetime.now()
            self.days_remaining = max(0, remaining.days)
        else:
            self.days_remaining = 0

    def is_expired(self):
        """检查是否过期（不含试用）"""
        if not self.expires_at:
            return True
        return datetime.datetime.now() > self.expires_at

    def is_activated(self):
        """检查是否已激活（非过期）"""
        if not self.expires_at:
            return False
        return datetime.datetime.now() <= self.expires_at

    def can_use_daily_trial(self):
        """检查是否可以使用每日免费试用"""
        import hashlib
        import uuid
        
        # 如果已激活，不需要试用
        if self.is_activated():
            return False
        
        # 检查是否是新的一天
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if self.daily_trial_date != today:
            # 新的一天
            if self.daily_trial_flag:
                self.daily_trial_date = today
                self.daily_trial_remaining_seconds = 3600
                self.daily_trial_start_time = None
                self.first_run_today = False
                self.save_to_local()
                print("新的一天，重置试用时间，开始计时")
                return True
            else:
                # 首次使用
                self.daily_trial_date = today
                self.daily_trial_remaining_seconds = 3600
                self.daily_trial_start_time = None
                self.first_run_today = True
                machine_id = str(uuid.getnode())
                flag_data = f"{self.username}_{today}_{machine_id}"
                self.daily_trial_flag = hashlib.md5(flag_data.encode()).hexdigest()
                self.save_to_local()
                print("首次使用，已创建加密标志，今天不计时，明天开始计时")
                return False
        
        if self.first_run_today:
            print("今天首次使用，不计时，明天开始计时")
            return False
        
        return self.daily_trial_remaining_seconds > 0

    def start_daily_trial(self):
        """开始每日试用计时"""
        if self.daily_trial_remaining_seconds <= 0:
            self.daily_trial_remaining_seconds = 0
            print("今日试用时间已用完")
        else:
            print(f"继续计时，剩余 {self.daily_trial_remaining_seconds} 秒")

    def update_daily_trial_time(self, elapsed_seconds):
        """更新试用剩余时间"""
        self.daily_trial_remaining_seconds = max(0, self.daily_trial_remaining_seconds - elapsed_seconds)
        self.save_to_local()

    def get_formatted_trial_time(self):
        """获取格式化的剩余试用时间"""
        seconds = max(0, self.daily_trial_remaining_seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def sync_from_server(self):
        """从服务端同步激活状态"""
        try:
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            activation_server_url = self._get_server_url()
            response = requests.post(
                f"{activation_server_url}/api/activation/sync",
                json={'username': self.username},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'application/json' not in content_type:
                    print("服务器返回非JSON响应")
                    return
                    
                result = response.json()
                if result.get('success'):
                    data = result.get('data', {})
                    expires_at = data.get('expires_at')
                    if expires_at:
                        self.expires_at = datetime.datetime.fromisoformat(expires_at)
                        self.update_days_remaining()
                        self.save_to_local()
                        print(f"同步成功，过期时间: {self.expires_at}")
                else:
                    print(f"同步失败: {result.get('message', '未知错误')}")
        except Exception as e:
            print(f"同步激活状态失败: {e}")


# ==================== 激活系统 - 注册对话框 ====================
class ActivationRegisterDialog:
    """激活系统注册对话框"""

    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.title('用户注册')
        self.dialog.geometry('400x350')
        self.dialog.transient(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.grab_set()
        
        self.result = False
        self.username = ''
        self.password = ''
        
        ttk.Label(self.dialog, text='用户注册', font=('Arial', 16, 'bold')).pack(pady=10)
        
        form_frame = ttk.Frame(self.dialog)
        form_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(form_frame, text='用户名:').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_edit = ttk.Entry(form_frame, width=30)
        self.username_edit.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text='重置密码邮箱:').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_edit = ttk.Entry(form_frame, width=30)
        self.email_edit.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text='密码:').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.password_edit = ttk.Entry(form_frame, width=30, show='*')
        self.password_edit.grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text='重复密码:').grid(row=3, column=0, sticky=tk.W, pady=5)
        self.repeat_password_edit = ttk.Entry(form_frame, width=30, show='*')
        self.repeat_password_edit.grid(row=3, column=1, pady=5, padx=5)
        
        ttk.Label(self.dialog, text='用户名和密码至少6位', foreground='gray').pack(pady=5)
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(btn_frame, text='注册', command=self.register).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text='取消', command=self.cancel).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def _get_activation_server_url(self):
        return "https://9793tg1lo456.vicp.fun"

    def register(self):
        username = self.username_edit.get().strip()
        email = self.email_edit.get().strip()
        password = self.password_edit.get().strip()
        repeat_password = self.repeat_password_edit.get().strip()

        if len(username) < 6:
            messagebox.showwarning('错误', '用户名至少需要6位', parent=self.dialog)
            return

        if not email:
            messagebox.showwarning('错误', '请输入重置密码邮箱', parent=self.dialog)
            return

        if len(password) < 6:
            messagebox.showwarning('错误', '密码至少需要6位', parent=self.dialog)
            return

        if password != repeat_password:
            messagebox.showwarning('错误', '两次输入的密码不一致', parent=self.dialog)
            return

        try:
            server_url = self._get_activation_server_url()
            response = requests.post(f"{server_url}/api/register", json={
                'username': username,
                'email': email,
                'password': password,
                'repeat_password': repeat_password
            }, timeout=10)
            result = response.json()

            if result.get('success'):
                messagebox.showinfo('成功', '注册成功！\n\n请记住您的用户名和密码。\n重置密码邮箱可用于找回密码。', parent=self.dialog)
                self.username = username
                self.password = password
                self.result = True
                self.dialog.destroy()
            else:
                messagebox.showerror('错误', result.get('message', '注册失败'), parent=self.dialog)
        except Exception as e:
            messagebox.showerror('错误', f'网络错误: {str(e)}', parent=self.dialog)

    def cancel(self):
        self.dialog.destroy()


# ==================== 激活系统 - 激活码对话框 ====================
class ActivationCodeDialog:
    """激活码输入对话框"""

    def __init__(self, parent, username):
        self.dialog = tk.Toplevel(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.title('激活使用')
        self.dialog.geometry('500x400')
        self.dialog.transient(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.grab_set()
        
        self.username = username
        self.code = ''
        self.invite_code = ''
        self.result = False
        
        ttk.Label(self.dialog, text='激活使用', font=('Arial', 16, 'bold')).pack(pady=10)
        ttk.Label(self.dialog, text='请输入激活码激活系统', foreground='gray').pack(pady=5)
        
        form_frame = ttk.Frame(self.dialog)
        form_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(form_frame, text='用户名:').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_display = ttk.Entry(form_frame, width=35, state='readonly')
        self.username_display.grid(row=0, column=1, pady=5, padx=5)
        self.username_display.config(state='normal')
        self.username_display.insert(0, username)
        self.username_display.config(state='readonly')
        
        ttk.Label(form_frame, text='激活码:').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.code_edit = ttk.Entry(form_frame, width=35)
        self.code_edit.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text='邀请码:').grid(row=2, column=0, sticky=tk.W, pady=5)
        self.invite_code_edit = ttk.Entry(form_frame, width=35)
        self.invite_code_edit.grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Label(self.dialog, text='邀请码为已注册的用户名，输入正确可获得额外奖励（可选）', 
                 foreground='#007bff').pack(pady=5)
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(btn_frame, text='确认激活', command=self.confirm).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text='取消', command=self.cancel).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def confirm(self):
        code = self.code_edit.get().strip()
        if not code:
            messagebox.showwarning('提示', '请输入激活码', parent=self.dialog)
            return
        self.code = code
        self.invite_code = self.invite_code_edit.get().strip()
        self.result = True
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()


# ==================== 激活系统 - 购买对话框 ====================
class ActivationPurchaseDialog:
    """激活系统购买对话框"""

    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.title('购买激活码')
        self.dialog.geometry('500x400')
        self.dialog.transient(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.grab_set()
        
        ttk.Label(self.dialog, text='购买激活码', font=('Arial', 16, 'bold')).pack(pady=10)
        
        info_text = """购买方式：

1. 联系开发者购买
2. 扫描二维码支付

价格：
- 月卡：30元/月
- 季卡：80元/3个月
- 年卡：280元/年

联系方式：
- 微信：xxx
- QQ：xxx
"""
        ttk.Label(self.dialog, text=info_text, justify=tk.LEFT).pack(pady=10, padx=20)
        ttk.Button(self.dialog, text='关闭', command=self.dialog.destroy).pack(pady=10)


# ==================== 激活系统 - 报障对话框 ====================
class ActivationTicketDialog:
    """激活系统报障对话框"""

    def __init__(self, parent, username):
        self.dialog = tk.Toplevel(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.title('报障')
        self.dialog.geometry('500x450')
        self.dialog.transient(parent.root if hasattr(parent, 'root') else parent)
        self.dialog.grab_set()
        
        self.username = username
        self.result = False
        
        ttk.Label(self.dialog, text='报障工单', font=('Arial', 16, 'bold')).pack(pady=10)
        
        form_frame = ttk.Frame(self.dialog)
        form_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Label(form_frame, text='用户名:').grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_display = ttk.Entry(form_frame, width=35, state='readonly')
        self.username_display.grid(row=0, column=1, pady=5, padx=5)
        self.username_display.config(state='normal')
        self.username_display.insert(0, username)
        self.username_display.config(state='readonly')
        
        ttk.Label(form_frame, text='问题标题:').grid(row=1, column=0, sticky=tk.W, pady=5)
        self.title_edit = ttk.Entry(form_frame, width=35)
        self.title_edit.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text='问题内容:').grid(row=2, column=0, sticky=tk.NW, pady=5)
        self.content_edit = tk.Text(form_frame, width=35, height=6)
        self.content_edit.grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text='联系人:').grid(row=3, column=0, sticky=tk.W, pady=5)
        self.contact_person_edit = ttk.Entry(form_frame, width=35)
        self.contact_person_edit.grid(row=3, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text='联系电话:').grid(row=4, column=0, sticky=tk.W, pady=5)
        self.contact_phone_edit = ttk.Entry(form_frame, width=35)
        self.contact_phone_edit.grid(row=4, column=1, pady=5, padx=5)
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(btn_frame, text='提交', command=self.submit).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        ttk.Button(btn_frame, text='取消', command=self.cancel).pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

    def _get_activation_server_url(self):
        try:
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SERVER', 'server_config.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    server_url = config.get('server_url', '').strip()
                    if server_url:
                        return server_url
        except Exception:
            pass
        return "https://9793tg1lo456.vicp.fun"

    def submit(self):
        title = self.title_edit.get().strip()
        content = self.content_edit.get('1.0', tk.END).strip()
        contact_person = self.contact_person_edit.get().strip()
        contact_phone = self.contact_phone_edit.get().strip()

        if not title:
            messagebox.showwarning('错误', '请输入问题标题', parent=self.dialog)
            return

        if not content:
            messagebox.showwarning('错误', '请输入问题内容', parent=self.dialog)
            return

        try:
            server_url = self._get_activation_server_url()
            response = requests.post(
                f"{server_url}/api/ticket/create",
                json={
                    'username': self.username,
                    'title': title,
                    'content': content,
                    'contact_person': contact_person,
                    'contact_phone': contact_phone
                },
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    messagebox.showinfo('成功', '报障工单已提交，请耐心等待处理。', parent=self.dialog)
                    self.result = True
                    self.dialog.destroy()
                else:
                    messagebox.showerror('错误', result.get('message', '提交失败'), parent=self.dialog)
            else:
                messagebox.showerror('错误', f'服务器错误: HTTP {response.status_code}', parent=self.dialog)

        except Exception as e:
            messagebox.showerror('错误', f'提交报障失败: {str(e)}', parent=self.dialog)

    def cancel(self):
        self.dialog.destroy()
