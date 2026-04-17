"""ZQ-自动化任务系统主程序 - Tkinter版本"""
import sys
import os
import json
import shutil
import zipfile
import requests
from datetime import datetime
from pathlib import Path

# 使用Tkinter
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
from tkinter import font as tkfont

import pyautogui
import threading
import time

from config import Config
from engines import AIEngine, ExecutionEngine, KeyboardEngine, ImageRecognition
from database import DatabaseManager
from managers import KeywordManager, WorkflowManager, TaskManager, ProjectManager

# 导入标签页和处理模块(稍后创建)
import tabs as tabs_module
import handlers as handlers_module
import discovery_handlers as discovery_handlers_module


class StatusOutput:
    """重定向输出到状态显示器"""
    def __init__(self, text_widget, original_output):
        self.text_widget = text_widget
        self.original_output = original_output
        
    def write(self, text):
        if text.strip():
            self.text_widget.insert(tk.END, text.strip() + '\n')
            self.text_widget.see(tk.END)
        self.original_output.write(text)
        
    def flush(self):
        self.original_output.flush()


class ScreenshotWidget:
    """截图选择窗口 - Tkinter版本"""
    def __init__(self, parent=None, recording_mode=None):
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0
        self.drawing = False
        self.cancelled = False
        self.recording_mode = recording_mode
        self.screenshot_callback = None
        self.right_click_callback = None
        self.background_image = None
        self._screen_image = None
        self._finished = False
        self.window = None
        self.canvas = None
        
    def start(self):
        """开始截图"""
        try:
            from PIL import ImageGrab
            
            self.window = tk.Toplevel()
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            
            self._screen_image = ImageGrab.grab(bbox=(0, 0, screen_width, screen_height))
            
            self.window.attributes('-fullscreen', True)
            self.window.attributes('-topmost', True)
            self.window.overrideredirect(True)
            
            self.canvas = tk.Canvas(self.window, cursor='cross', highlightthickness=0, bg='#1e1e1e')
            self.canvas.pack(fill=tk.BOTH, expand=True)
            
            self.window.update()
            self._show_screen_background()
            
            self.canvas.bind('<Button-1>', self.on_left_press)
            self.canvas.bind('<Button-3>', self.on_right_press)
            self.canvas.bind('<B1-Motion>', self.on_drag)
            self.canvas.bind('<ButtonRelease-1>', self.on_release)
            self.window.bind('<Escape>', self.on_escape)
            self.window.protocol("WM_DELETE_WINDOW", self.on_escape)
            
        except Exception as e:
            print(f"截图初始化失败: {e}")
            import traceback
            traceback.print_exc()
        
    def _show_screen_background(self):
        """显示屏幕截图作为背景"""
        try:
            if self._screen_image:
                from PIL import ImageTk
                self.background_image = ImageTk.PhotoImage(self._screen_image)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.background_image, tags='background')
        except Exception as e:
            print(f"显示屏幕背景失败: {e}")
        
    def on_left_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.drawing = True
        
    def on_right_press(self, event):
        if self._finished:
            return
        print(f"[ScreenshotWidget] 右键点击,recording_mode={self.recording_mode}")
        self.cancelled = True
        self._finished = True
        if self.recording_mode in ['manual_record', 'auto_record']:
            if self.right_click_callback:
                self.right_click_callback()
        self.window.destroy()
            
    def on_drag(self, event):
        if self.drawing:
            self.end_x = event.x
            self.end_y = event.y
            self.canvas.delete('rect')
            self.canvas.create_rectangle(
                self.start_x, self.start_y, self.end_x, self.end_y,
                outline='red', width=2, fill='', stipple='gray50', tags='rect'
            )
            
    def on_release(self, event):
        if self.drawing and not self._finished:
            self.end_x = event.x
            self.end_y = event.y
            self.drawing = False
            self._finished = True
            self.capture_selected_region()
            
    def on_escape(self, event=None):
        if self._finished:
            return
        self.cancelled = True
        self._finished = True
        self.window.destroy()
        
    def capture_selected_region(self):
        x1 = min(self.start_x, self.end_x)
        y1 = min(self.start_y, self.end_y)
        x2 = max(self.start_x, self.end_x)
        y2 = max(self.start_y, self.end_y)
        
        width = x2 - x1
        height = y2 - y1
        
        if width > 10 and height > 10:
            try:
                if self._screen_image:
                    screenshot = self._screen_image.crop((x1, y1, x2, y2))
                else:
                    from PIL import ImageGrab
                    screenshot = ImageGrab.grab(bbox=(x1, y1, x2, y2))
                    
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"screenshot_{timestamp}.png"
                pic_dir = getattr(self, 'pic_directory', 'pic')
                os.makedirs(pic_dir, exist_ok=True)
                filepath = os.path.join(pic_dir, filename)
                screenshot.save(filepath)
                
                if self.screenshot_callback:
                    self.screenshot_callback(filepath)
            except Exception as e:
                print(f"截图失败: {e}")
        
        self.window.destroy()


class MainWindow:
    """主窗口类 - Tkinter版本"""
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('ZQ-全能自动化任务系统')
        self.root.geometry('1200x1000')
        
        # 设置窗口图标
        try:
            self.root.iconbitmap('ZQ.bmp')
        except:
            pass
        
        # 初始化配置
        self.config = Config()
        print(f"图片目录: {self.config.pic_directory}")
        print(f"项目目录: {self.config.projects_directory}")
        
        # 初始化各个模块
        self.ai_engine = AIEngine(self.config)
        self.execution_engine = ExecutionEngine(self.config)
        self.keyboard_engine = KeyboardEngine(self.config)
        self.image_recognition = ImageRecognition(self.config)
        self.database_manager = DatabaseManager(self.config)
        self.keyword_manager = KeywordManager(self.config)
        self.workflow_manager = WorkflowManager(self.config)
        self.project_manager = ProjectManager(self.config)
        
        # 多模态大模型相关
        self.multimodal_model = None
        self.multimodal_processor = None
        
        # API调用相关配置
        if not hasattr(self.config, 'use_openai_api'):
            self.config.use_openai_api = False
        if not hasattr(self.config, 'api_provider'):
            self.config.api_provider = "百度API"
        if not hasattr(self.config, 'api_base_url'):
            self.config.api_base_url = ""
        if not hasattr(self.config, 'api_key'):
            self.config.api_key = ""
        if not hasattr(self.config, 'api_model'):
            self.config.api_model = "gpt-3.5-turbo"
        if not hasattr(self.config, 'api_enable_thinking'):
            self.config.api_enable_thinking = False
        
        # 根据配置加载多模态大模型
        print(f"[调试] load_multimodal_model 配置值: {self.config.load_multimodal_model}")
        print(f"[调试] load_multimodal_model 类型: {type(self.config.load_multimodal_model)}")
        if self.config.load_multimodal_model:
            print("启动时加载本地多模态大模型...")
            self.load_multimodal_model()
            print("本地多模态大模型已加载")
        else:
            print("启动时不加载本地多模态大模型(开关关闭)")
            
        self.task_manager = TaskManager(
            self.config,
            self.execution_engine,
            self.keyboard_engine,
            self.image_recognition,
            self.keyword_manager
        )
        
        # UI相关变量
        self.current_screenshot = None
        self.show_mouse_coordinates = self.config.show_mouse_coordinates
        self.global_similarity = self.config.global_similarity / 100.0
        self.mouse_coord_window = None
        
        # 录制相关变量
        self.recording_mode = None
        self.recorded_steps = []
        self.record_prefix = ""
        self.record_count = 0
        self.long_recording_listener = None
        self.long_recording_start_time = None
        self.long_recording_events = []
        
        # 日常任务列表
        self.daily_tasks = []
        
        # 答题系统任务列表
        self.answer_tasks = []
        
        # 发现即点任务列表
        self.discovery_tasks = []
        
        # 初始化全局点击监听器
        self.init_global_click_listener()
        
        # 鼠标坐标更新定时器
        self.mouse_coord_timer = None
        if self.show_mouse_coordinates:
            self.update_mouse_coordinates()
        
        # 初始化UI
        self.init_ui()
        
        # 恢复上次保存的项目状态(不清空任务列表)
        if hasattr(self, 'project_manager'):
            current_project = self.project_manager.current_project
            print(f"正在恢复项目状态: {current_project}")
            print(f"当前 projects_directory: {self.config.projects_directory}")
            if current_project and hasattr(self, 'switch_project_by_name'):
                self.switch_project_by_name(current_project, clear_tasks=False)
        
        self.load_chat_history()
        
        # 初始化默认关键词(包括多图、间隔、快找)
        self._initialize_default_keywords()
        
        # 刷新关键词列表
        if hasattr(self, 'keyword_list'):
            self.load_keywords()
        
        # 加载日常任务列表
        print(f"初始化日常任务列表,当前任务数: {len(self.daily_tasks) if hasattr(self, 'daily_tasks') else 0}")
        self.load_daily_tasks_list()
        print(f"加载完成后任务数: {len(self.daily_tasks) if hasattr(self, 'daily_tasks') else 0}")
        
        # 加载答题系统任务列表
        print(f"初始化答题系统任务列表,当前任务数: {len(self.answer_tasks) if hasattr(self, 'answer_tasks') else 0}")
        self.load_answer_tasks_list()
        print(f"加载完成后任务数: {len(self.answer_tasks) if hasattr(self, 'answer_tasks') else 0}")
        
        # 加载发现即点任务列表
        print(f"初始化发现即点任务列表,当前任务数: {len(self.discovery_tasks) if hasattr(self, 'discovery_tasks') else 0}")
        self.load_discovery_tasks_list()
        print(f"加载完成后任务数: {len(self.discovery_tasks) if hasattr(self, 'discovery_tasks') else 0}")
        
        # 恢复工作组状态和命令列表
        if hasattr(self, 'wg_info'):
            self._restore_workgroup_state()
        
        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.closeEvent)
        
        # 绑定键盘事件
        self.root.bind('<Escape>', self.keyPressEvent)
        
    def keyPressEvent(self, event):
        """处理键盘按键事件"""
        if hasattr(self, 'recording_mode') and self.recording_mode in ['manual_record', 'auto_record']:
            print("[DEBUG] ESC键按下,停止录制")
            if hasattr(self, 'on_right_click_in_record'):
                self.on_right_click_in_record()
                
    def closeEvent(self):
        """窗口关闭事件"""
        try:
            # 保存日常任务全局设置
            if hasattr(self, 'daily_tasks_main_switch'):
                self.save_daily_tasks_global_settings()
            
            # 保存答题系统全局设置
            if hasattr(self, 'answer_tasks_main_switch'):
                self.save_answer_tasks_global_settings()
            
            # 保存当前项目状态
            if hasattr(self, 'project_manager'):
                self.project_manager._save_current_project_config()
                print(f"程序退出时已保存当前项目: {self.project_manager.current_project}")
            
            # 保存配置
            self.config.save()
            print("配置已保存到 config.json")
            
            # 保存日常任务
            if hasattr(self, 'daily_tasks'):
                self.save_daily_tasks()
                print(f"程序退出时已保存 {len(self.daily_tasks)} 个日常任务")
            
            # 保存答题系统任务
            if hasattr(self, 'answer_tasks'):
                self.save_answer_tasks()
                print(f"程序退出时已保存 {len(self.answer_tasks)} 个答题任务")
            
            # 保存发现即点任务
            if hasattr(self, 'discovery_tasks'):
                self.save_discovery_tasks()
                print(f"程序退出时已保存 {len(self.discovery_tasks)} 个发现即点任务")
            
            # 保存工作组状态和命令列表
            if hasattr(self, 'wg_info'):
                self._save_workgroup_state()
            
            # 恢复输出
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
            
            # 停止所有任务
            self.stop_all_tasks()
            
        except Exception as e:
            print(f"关闭窗口时出错: {e}")
        finally:
            self.root.destroy()
            
    def _wg_request(self, url, json_data=None, method='POST'):
        """工作组API请求封装，带错误处理"""
        import requests
        server_url = self._get_server_url()
        full_url = f'{server_url}{url}'
        try:
            if method == 'GET':
                resp = requests.get(full_url, timeout=10)
            else:
                resp = requests.post(full_url, json=json_data, timeout=10)
            if resp.status_code != 200:
                return None, f'服务器返回错误: HTTP {resp.status_code}\n{resp.text[:200]}'
            try:
                return resp.json(), None
            except Exception:
                return None, f'服务器返回非JSON数据: {resp.text[:200]}'
        except requests.exceptions.ConnectionError:
            return None, '无法连接到服务器，请确认服务端已启动'
        except requests.exceptions.Timeout:
            return None, '请求超时，请检查网络'
        except Exception as e:
            return None, f'请求失败: {str(e)}'

    def _get_server_url(self):
        """获取服务端地址"""
        return 'https://9793tg1lo456.vicp.fun'

    def _extract_json_object(self, content, key):
        """从可能损坏的JSON内容中提取指定key的对象"""
        import re
        pattern = rf'"{key}"\s*:\s*\{{'
        match = re.search(pattern, content)
        if not match:
            return None
        start = match.end() - 1
        brace_count = 1
        i = start + 1
        while i < len(content) and brace_count > 0:
            if content[i] == '{':
                brace_count += 1
            elif content[i] == '}':
                brace_count -= 1
            i += 1
        if brace_count == 0:
            return '{' + content[start+1:i-1] + '}'
        return None

    def _get_username(self):
        """获取当前激活系统登录的用户名"""
        try:
            projects_dir = getattr(self, 'config', None) and getattr(self.config, 'projects_directory', '')
            if not projects_dir:
                projects_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
            cfg_path = os.path.join(projects_dir, 'activation.json')
            if os.path.exists(cfg_path):
                with open(cfg_path, 'r') as f:
                    return json.load(f).get('username', '')
            cfg_path2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'activation_config.json')
            if os.path.exists(cfg_path2):
                with open(cfg_path2, 'r') as f:
                    return json.load(f).get('username', '')
            return ''
        except Exception:
            return ''

    def _get_workgroup_local_dir(self):
        """获取工作组本地同步目录"""
        if hasattr(self, 'wg_info') and self.wg_info.get('sync_dir'):
            sync_dir = self.wg_info['sync_dir']
            if not os.path.isabs(sync_dir):
                sync_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), sync_dir)
            os.makedirs(sync_dir, exist_ok=True)
            return sync_dir
        return None

    def _load_shared_commands(self):
        """加载共享命令"""
        pass

    def _save_shared_commands(self):
        """保存共享命令"""
        pass

    def _save_workgroup_state(self):
        """保存工作组状态和命令列表"""
        try:
            def json_serial(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

            state = {
                'wg_info': getattr(self, 'wg_info', {}),
                'cmd_list': getattr(self, 'cmd_list', []),
                'cmd_templates': getattr(self, 'cmd_templates', {})
            }
            os.makedirs('data', exist_ok=True)
            with open('data/workgroup_state.json', 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2, default=json_serial)
            print(f"工作组状态已保存, 命令数: {len(self.cmd_list)}")
        except Exception as e:
            print(f"保存工作组状态失败: {e}")

    def _restore_workgroup_state(self):
        """恢复工作组状态和命令列表"""
        state_file = 'data/workgroup_state.json'
        state = None

        if not os.path.exists(state_file):
            print('[DEBUG] 工作组状态文件不存在')
            return

        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[DEBUG] JSON解析失败: {e}，尝试手动提取工作组信息")
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                wg_info_str = self._extract_json_object(content, 'wg_info')
                if wg_info_str:
                    state = {'wg_info': json.loads(wg_info_str), 'cmd_list': [], 'cmd_templates': {}}
                    print(f"[DEBUG] 手动提取工作组信息成功")
                else:
                    print(f"[DEBUG] 无法从损坏的文件中提取工作组信息")
                    return
            except Exception as extract_err:
                print(f"[DEBUG] 手动提取也失败: {extract_err}")
                return

        try:
            wg = state.get('wg_info', {})
            if not wg or not wg.get('id'):
                print('[DEBUG] 工作组信息为空或无ID')
                return

            cached_role = wg.get('role', '')
            self.wg_info = wg.copy()
            print(f"[DEBUG] 已恢复工作组状态(待验证): {wg.get('name', '')} 缓存角色: {cached_role}")

            templates = state.get('cmd_templates', {})
            if templates:
                for name, tpl in templates.items():
                    self.cmd_templates[name] = tpl

            username = self._get_username()
            print(f"[DEBUG] 当前用户名: {username}, 工作组ID: {self.wg_info.get('id')}")
            if username and self.wg_info.get('id'):
                result, err = self._wg_request('/api/workgroup/get_shared_commands', {
                    'username': username,
                    'workgroup_id': self.wg_info['id']
                }, method='GET')
                print(f"[DEBUG] 角色验证响应: result={result is not None}, err={err}")
                if result and result.get('success'):
                    member_info = result.get('data', {}).get('member')
                    print(f"[DEBUG] 成员信息: {member_info}")
                    if member_info:
                        if member_info.get('is_disabled'):
                            print('[DEBUG] 用户已被禁用，不恢复工作组状态')
                            self.wg_info = {}
                            self.cmd_list = []
                            self.cmd_refresh_tree()
                            self._update_cmd_list_source()
                            self.wg_status_label.config(text='未加入工作组', foreground='gray')
                            return
                        
                        actual_role = member_info.get('role', 'member')
                        if actual_role != cached_role:
                            print(f"[DEBUG] 角色验证: 缓存角色 {cached_role} -> 实际角色 {actual_role}")
                            self.wg_info['role'] = actual_role
                        _role_map = {'owner': '创建者', 'admin': '管理员', 'member': '组员'}
                        _role_display = _role_map.get(actual_role, actual_role)
                        self.wg_status_label.config(
                            text=f'工作组: {self.wg_info.get("name", "")} ({_role_display})',
                            foreground='#008800')
                        self._update_cmd_list_source()
                        commands = result.get('data', {}).get('commands', [])
                        if commands:
                            self.cmd_list = commands
                            self.cmd_refresh_tree()
                            self._update_cmd_list_source()
                            print(f"[DEBUG] 已加载共享命令, 共 {len(commands)} 条命令")
                        else:
                            self.cmd_list = []
                            self.cmd_refresh_tree()
                            self._update_cmd_list_source()
                        
                        self._start_wg_sync()
                        self._start_countdown_timer()
                        print(f"[DEBUG] 工作组状态恢复完成")
                    else:
                        print('[DEBUG] 无法获取成员信息，可能已被移出工作组')
                        self.wg_info = {}
                        self.cmd_list = []
                        self.cmd_refresh_tree()
                        self._update_cmd_list_source()
                        self.wg_status_label.config(text='未加入工作组', foreground='gray')
                else:
                    print(f'[DEBUG] 验证工作组失败: {err}')
            else:
                print('[DEBUG] 无用户名或工作组ID，跳过验证')

        except Exception as e:
            print(f"恢复工作组状态失败: {e}")

    def stop_all_tasks(self):
        """停止所有正在执行的任务"""
        try:
            stopped_any = False
            
            # 停止日常任务
            if hasattr(self, 'daily_tasks_running') and self.daily_tasks_running:
                self.stop_all_daily_tasks()
                print("已停止日常任务")
                stopped_any = True
            
            # 停止答题系统
            if hasattr(self, 'answer_tasks_running') and self.answer_tasks_running:
                self.stop_all_answer_tasks()
                print("已停止答题系统")
                stopped_any = True
            
            # 停止发现即点
            if hasattr(self, 'discovery_tasks_running') and self.discovery_tasks_running:
                self.stop_all_discovery_tasks()
                print("已停止发现即点")
                stopped_any = True
            
            if stopped_any:
                print("所有任务已停止")
            else:
                print("当前没有正在执行的任务")
                
        except Exception as e:
            print(f"停止所有任务时出错: {e}")
            
    def init_ui(self):
        """初始化UI"""
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 创建标签页控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建各个标签页
        self.create_command_tab()
        self.create_tools_tab()
        self.create_ai_chat_tab()
        self.create_keywords_tab()
        self.create_workflows_tab()
        self.create_tasks_tab()
        self.create_daily_tasks_tab()
        self.create_answer_system_tab()
        self.create_discovery_click_tab()
        self.create_projects_tab()
        self.create_activation_tab()
        
        # 标签页切换事件
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
    def on_tab_changed(self, event):
        """标签页切换事件"""
        pass  # 可以在tabs模块中实现
        
    def create_ai_chat_tab(self):
        """创建AI对话标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='AI对话')
        
        # 聊天显示区域
        chat_frame = ttk.LabelFrame(tab, text='自然对话')
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.chat_display = scrolledtext.ScrolledText(chat_frame, height=20, state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 输入区域
        input_frame = ttk.Frame(chat_frame)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.chat_input = scrolledtext.ScrolledText(input_frame, height=3)
        self.chat_input.pack(fill=tk.X, padx=5, pady=5)
        
        # 按钮区域
        button_frame = ttk.Frame(chat_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text='AI生成工作流', command=self.execute_from_chat).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='发送聊天', command=self.send_message).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text='清空', command=self.clear_chat).pack(side=tk.RIGHT, padx=5)
        
        # 状态显示区域
        status_frame = ttk.LabelFrame(tab, text='运行状态')
        status_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_display = scrolledtext.ScrolledText(
            status_frame, 
            height=10,
            bg='#1e1e1e',
            fg='#00ff00',
            font=('Consolas', 10)
        )
        self.status_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.status_display.insert(tk.END, "系统就绪,等待操作...\n提示:点击鼠标右键可随时停止所有正在执行的任务\n")
        
        # 重定向输出
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = StatusOutput(self.status_display, sys.stdout)
        sys.stderr = StatusOutput(self.status_display, sys.stderr)
        
    def add_status_message(self, message):
        """添加状态信息"""
        self.status_display.insert(tk.END, message + '\n')
        self.status_display.see(tk.END)
        
    def _initialize_default_keywords(self):
        """初始化默认关键词"""
        # 检查多图关键词是否存在
        if not self.keyword_manager.get_keyword('多图'):
            multi_image_script = """
import os
# 多图关键词:查找多张图片,点击第一个找到的
image_paths = [p.strip() for p in image_paths.split('|') if p.strip()]
if not image_paths:
    print("错误:没有提供图片路径")
else:
    # 构建完整的图片路径
    full_paths = []
    for img_path in image_paths:
        if not os.path.isabs(img_path):
            # 相对路径,添加到pic目录
            full_path = os.path.join(config.pic_directory, img_path)
        else:
            full_path = img_path
        full_paths.append(full_path)
    
    # 调用多图查找和点击
    result = mouse.find_and_click_multiple_images(full_paths, timeout=10)
    if result['success']:
        print(f"成功:{result['message']}")
        # 保存坐标供后续使用
        last_x = result['x']
        last_y = result['y']
    else:
        print(f"失败:{result['error']}")
"""
            self.keyword_manager.add_keyword(
                '多图',
                '查找多张图片,点击第一个找到的',
                multi_image_script,
                ['image_paths']
            )
            print("已添加默认关键词:多图")
        
        # 检查间隔关键词
        if not self.keyword_manager.get_keyword('间隔'):
            interval_script = """
import time
# 间隔关键词:等待指定时间(毫秒)
interval_ms = interval_ms.strip() if interval_ms else ''
if not interval_ms:
    # 使用全局间隔时间
    wait_time = config.global_interval / 1000.0
    print(f"等待 {config.global_interval}ms (使用全局设置)")
else:
    try:
        wait_time = int(interval_ms) / 1000.0
        print(f"等待 {interval_ms}ms")
    except:
        wait_time = config.global_interval / 1000.0
        print(f"参数错误,使用全局设置:{config.global_interval}ms")

time.sleep(wait_time)
"""
            self.keyword_manager.add_keyword(
                '间隔',
                '等待指定时间(毫秒),不输入参数使用全局设置',
                interval_script,
                ['interval_ms']
            )
            print("已添加默认关键词:间隔")
        
        # 检查快找关键词
        quick_find_script = """
import os
import time
# 快找关键词:快速找图并点击,只使用全局相似度单次查找
image_path = image_path.strip() if image_path else ''
if not image_path:
    print("错误:没有提供图片路径")
else:
    # 构建完整的图片路径
    if not os.path.isabs(image_path):
        full_path = os.path.join(config.pic_directory, image_path)
    else:
        full_path = image_path
    
    # 使用trigger模式:只进行单次查找,不进行多算法多相似度轮换
    location = image.find_image(full_path, timeout=0, confidence=config.global_similarity/100.0, mode='trigger')
    
    if location:
        print(f"快找成功: {image_path} at ({location[0]}, {location[1]})")
        mouse.click(location[0], location[1])
    else:
        print(f"快找失败: 未找到 {image_path}")
"""
        if not self.keyword_manager.get_keyword('快找'):
            self.keyword_manager.add_keyword(
                '快找',
                '快速找图并点击,只使用全局相似度单次查找,找不到立即结束',
                quick_find_script,
                ['image_path']
            )
            print("已添加默认关键词:快找")
        else:
            self.keyword_manager.update_keyword('快找', script=quick_find_script)
            print("已更新关键词:快找")
        
        # 检查找图关键词
        find_image_script = """
import pyautogui
import time
# 找图关键词:查找图片并点击,只使用全局相似度单次查找
image_path = image_path.strip() if image_path else ''
if image_path:
    try:
        pic_dir = config.pic_directory
        if not image_path.startswith(pic_dir):
            full_path = os.path.join(pic_dir, image_path)
        else:
            full_path = image_path
        
        confidence = config.global_similarity / 100.0
        
        # 使用trigger模式:只进行单次查找,不进行多算法多相似度轮换
        coords = image.find_image(full_path, timeout=0, confidence=confidence, mode='trigger')
        
        if coords:
            if len(coords) == 2:
                center_x, center_y = coords
            else:
                center_x = coords[0] + coords[2] // 2
                center_y = coords[1] + coords[3] // 2
            pyautogui.click(center_x, center_y)
            print(f"找图成功: {image_path} at ({center_x}, {center_y})")
        else:
            print(f"找图失败: 未找到 {image_path}")
    except Exception as e:
        print(f"找图失败: {e}")
else:
    print("错误:未提供图片路径")
"""
        if not self.keyword_manager.get_keyword('找图'):
            self.keyword_manager.add_keyword(
                '找图',
                '查找图片并点击,只使用全局相似度单次查找,找不到立即结束',
                find_image_script,
                ['image_path']
            )
            print("已添加默认关键词:找图")
        else:
            self.keyword_manager.update_keyword('找图', script=find_image_script)
            print("已更新关键词:找图")
        
        # 检查点击关键词
        if not self.keyword_manager.get_keyword('点击'):
            click_script = """
import pyautogui
# 点击关键词:在指定坐标点击
params = params.strip() if params else ''
if params:
    try:
        parts = params.split(',')
        x = int(parts[0].strip())
        y = int(parts[1].strip()) if len(parts) > 1 else 0
        pyautogui.click(x, y)
        print(f"点击坐标: ({x}, {y})")
    except Exception as e:
        print(f"点击失败: {e}")
else:
    print("错误:未提供坐标参数")
"""
            self.keyword_manager.add_keyword(
                '点击',
                '在指定坐标点击,参数格式:x,y',
                click_script,
                ['params']
            )
            print("已添加默认关键词:点击")
        
        # 检查双击关键词
        if not self.keyword_manager.get_keyword('双击'):
            double_click_script = """
import pyautogui
# 双击关键词:在指定坐标双击
params = params.strip() if params else ''
if params:
    try:
        parts = params.split(',')
        x = int(parts[0].strip())
        y = int(parts[1].strip()) if len(parts) > 1 else 0
        pyautogui.doubleClick(x, y)
        print(f"双击坐标: ({x}, {y})")
    except Exception as e:
        print(f"双击失败: {e}")
else:
    print("错误:未提供坐标参数")
"""
            self.keyword_manager.add_keyword(
                '双击',
                '在指定坐标双击,参数格式:x,y',
                double_click_script,
                ['params']
            )
            print("已添加默认关键词:双击")
        
        # 检查右击关键词
        if not self.keyword_manager.get_keyword('右击'):
            right_click_script = """
import pyautogui
# 右击关键词:在指定坐标右击
params = params.strip() if params else ''
if params:
    try:
        parts = params.split(',')
        x = int(parts[0].strip())
        y = int(parts[1].strip()) if len(parts) > 1 else 0
        pyautogui.rightClick(x, y)
        print(f"右击坐标: ({x}, {y})")
    except Exception as e:
        print(f"右击失败: {e}")
else:
    print("错误:未提供坐标参数")
"""
            self.keyword_manager.add_keyword(
                '右击',
                '在指定坐标右击,参数格式:x,y',
                right_click_script,
                ['params']
            )
            print("已添加默认关键词:右击")
        
        # 检查拖动关键词
        if not self.keyword_manager.get_keyword('拖动'):
            drag_script = """
import pyautogui
import time
# 拖动关键词:从起点拖动到终点
params = params.strip() if params else ''
if params:
    try:
        parts = params.split(',')
        start_x = int(parts[0].strip())
        start_y = int(parts[1].strip()) if len(parts) > 1 else 0
        end_x = int(parts[2].strip()) if len(parts) > 2 else start_x
        end_y = int(parts[3].strip()) if len(parts) > 3 else start_y
        
        pyautogui.moveTo(start_x, start_y)
        time.sleep(0.05)
        pyautogui.drag(end_x - start_x, end_y - start_y, duration=0.5)
        print(f"拖动: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
    except Exception as e:
        print(f"拖动失败: {e}")
else:
    print("错误:未提供坐标参数")
"""
            self.keyword_manager.add_keyword(
                '拖动',
                '从起点拖动到终点,参数格式:start_x,start_y,end_x,end_y',
                drag_script,
                ['params']
            )
            print("已添加默认关键词:拖动")
        
        # 检查滚动关键词
        if not self.keyword_manager.get_keyword('滚动'):
            scroll_script = """
import pyautogui
# 滚动关键词:鼠标滚动
params = params.strip() if params else ''
if params:
    try:
        parts = params.split(',')
        x = int(parts[0].strip())
        y = int(parts[1].strip()) if len(parts) > 1 else 0
        dy = int(parts[2].strip()) if len(parts) > 2 else 0
        pyautogui.scroll(dy, x, y)
        direction = "向上" if dy > 0 else "向下"
        print(f"滚动: ({x}, {y}) {direction} {abs(dy)} 单位")
    except Exception as e:
        print(f"滚动失败: {e}")
else:
    print("错误:未提供参数")
"""
            self.keyword_manager.add_keyword(
                '滚动',
                '鼠标滚动,参数格式:x,y,dy(dy正数向上,负数向下)',
                scroll_script,
                ['params']
            )
            print("已添加默认关键词:滚动")
        
        # 检查按键关键词
        if not self.keyword_manager.get_keyword('按键'):
            key_press_script = """
import pyautogui
# 按键关键词:模拟按键
key = key.strip() if key else ''
if key:
    try:
        if len(key) == 1:
            pyautogui.press(key)
        else:
            key_name = key.replace('Key.', '').lower()
            pyautogui.press(key_name)
        print(f"按键: {key}")
    except Exception as e:
        print(f"按键失败: {e}")
else:
    print("错误:未提供按键参数")
"""
            self.keyword_manager.add_keyword(
                '按键',
                '模拟按键,参数为按键名称',
                key_press_script,
                ['key']
            )
            print("已添加默认关键词:按键")


# 将tabs中的创建标签页函数绑定到MainWindow类
def create_tools_tab(self):
    """创建工具标签页"""
    return tabs_module.create_tools_tab(self)

def create_keywords_tab(self):
    """创建关键词标签页"""
    return tabs_module.create_keywords_tab(self)

def create_workflows_tab(self):
    """创建工作流标签页"""
    return tabs_module.create_workflows_tab(self)

def create_tasks_tab(self):
    """创建任务标签页"""
    return tabs_module.create_tasks_tab(self)

def create_projects_tab(self):
    """创建项目标签页"""
    return tabs_module.create_projects_tab(self)

def create_daily_tasks_tab(self):
    """创建日常任务标签页"""
    return tabs_module.create_daily_tasks_tab(self)

def create_answer_system_tab(self):
    """创建答题系统标签页"""
    return tabs_module.create_answer_system_tab(self)

def create_discovery_click_tab(self):
    """创建发现即点标签页"""
    return tabs_module.create_discovery_click_tab(self)

def create_command_tab(self):
    """创建指挥标签页"""
    return tabs_module.create_command_tab(self)

def create_activation_tab(self):
    """创建激活标签页"""
    return tabs_module.create_activation_tab(self)


# 绑定标签页创建方法到MainWindow类
MainWindow.create_tools_tab = create_tools_tab
MainWindow.create_keywords_tab = create_keywords_tab
MainWindow.create_workflows_tab = create_workflows_tab
MainWindow.create_tasks_tab = create_tasks_tab
MainWindow.create_projects_tab = create_projects_tab
MainWindow.create_daily_tasks_tab = create_daily_tasks_tab
MainWindow.create_answer_system_tab = create_answer_system_tab
MainWindow.create_discovery_click_tab = create_discovery_click_tab
MainWindow.create_command_tab = create_command_tab
MainWindow.create_activation_tab = create_activation_tab


# 将handlers中的函数绑定到MainWindow类
handlers_to_bind = [
    'on_mouse_coord_changed', 'on_interval_changed', 'on_thread_count_changed', 
    'on_similarity_changed', 'on_model_selection_changed', 'on_api_settings_clicked', 
    'on_multimodal_model_changed', 'update_mouse_coordinates',
    'take_screenshot', '_do_screenshot', '_on_screenshot_taken', '_on_screenshot_widget_closed', 
    'toggle_recording', 'start_multi_screenshot',
    'insert_keyword', 'create_keyword', 'edit_keyword', 'delete_keyword', 'copy_keyword',
    'use_keyword', 'load_keywords',
    'create_workflow', 'edit_workflow', 'delete_workflow', 'copy_workflow', 'clear_all_workflows',
    'execute_workflow', 'load_workflows',
    'add_task', 'edit_task', 'delete_task', 'toggle_task_pause', 'execute_task_now', 'clear_all_tasks',
    'save_tasks_to_file', 'load_tasks_from_file', 'load_tasks_list',
    'send_message', 'execute_from_chat', 'clear_chat', 'load_chat_history',
    'start_left_click_record', 'start_double_click_record', 'start_right_click_record',
    'on_click_record', 'finish_click_record',
    'start_manual_record', 'start_auto_record',
    'add_screenshot_step', 'finish_screenshot_record', 'on_right_click_in_record',
    'save_record_as_workflow', '_prompt_save_workflow', '_clear_screenshot_display', '_auto_record_loop',
    'init_global_click_listener', 'on_global_click',
    'execute_workflow_by_name',
    'start_long_recording', 'stop_long_recording', 'add_long_recording_event',
    'save_long_recording_record', 'load_records', 'execute_record', '_execute_record_events',
    '_convert_events_to_workflow_steps', 'edit_record', 'delete_record', 'clear_screenshot_display', 'test_mouse_click',
    # 日常任务处理函数
    'on_daily_tasks_main_switch_changed', 'add_daily_task', 'edit_daily_task', 'delete_daily_task',
    'move_daily_task_up', 'move_daily_task_down', 'toggle_daily_task_pause', 'execute_daily_tasks_now',
    'stop_all_daily_tasks', '_execute_daily_tasks_sequence', 'save_daily_tasks_to_file', 'load_daily_tasks_from_file',
    'clear_all_daily_tasks', 'load_daily_tasks_list', 'save_daily_tasks', 'on_daily_task_item_changed',
    'on_loop_all_changed', 'on_global_repeat_count_changed', 'on_global_time_mode_changed',
    'on_global_schedule_time_changed', 'on_global_delay_minutes_changed',
    'save_daily_tasks_global_settings', 'load_daily_tasks_global_settings',
    # 答题系统处理函数
    'on_answer_tasks_main_switch_changed', 'add_answer_task', 'edit_answer_task', 'delete_answer_task',
    'move_answer_task_up', 'move_answer_task_down', 'execute_answer_tasks_now',
    'stop_all_answer_tasks', '_execute_answer_tasks_sequence', 'save_answer_tasks_to_file', 'load_answer_tasks_from_file',
    'clear_all_answer_tasks', 'load_answer_tasks_list', 'save_answer_tasks', 'on_answer_task_item_changed',
    'on_answer_loop_all_changed', 'on_answer_repeat_count_changed', 'on_answer_time_mode_changed',
    'on_answer_schedule_time_changed', 'on_answer_delay_minutes_changed',
    'save_answer_tasks_global_settings', 'load_answer_tasks_global_settings',
    # 发现即点处理函数
    'on_discovery_tasks_main_switch_changed', 'add_discovery_task', 'edit_discovery_task', 'delete_discovery_task',
    'move_discovery_task_up', 'move_discovery_task_down', 'execute_discovery_tasks_now',
    'stop_all_discovery_tasks', '_execute_discovery_tasks_sequence', 'save_discovery_tasks_to_file', 'load_discovery_tasks_from_file',
    'clear_all_discovery_tasks', 'load_discovery_tasks_list', 'save_discovery_tasks', 'on_discovery_task_item_changed',
    'on_discovery_loop_all_changed', 'on_discovery_repeat_count_changed', 'on_discovery_time_mode_changed',
    'on_discovery_schedule_time_changed', 'on_discovery_delay_minutes_changed',
    'save_discovery_tasks_global_settings', 'load_discovery_tasks_global_settings',
    # 项目管理函数
    'create_project', '_browse_project_path', 'switch_project_by_name', 'switch_project', 
    'pack_project', 'unpack_project', 'load_projects',
    'edit_current_project', 'save_current_project', 'on_project_selected', '_clear_all_task_lists',
    # 指挥系统处理函数
    'cmd_refresh_template_buttons', 'cmd_refresh_workflow_combo', 'cmd_use_template',
    'cmd_new_template', 'cmd_copy_template', 'cmd_delete_template', 'cmd_template_dialog',
    'cmd_edit_template_code', 'cmd_edit_selected_template', 'cmd_backup_all_templates', 'cmd_restore_all_templates',
    'cmd_add_coord', 'cmd_remove_coord', 'cmd_pick_coord',
    'cmd_add_workflow', 'cmd_remove_workflow', 'cmd_confirm_edit', 'cmd_clear_edit',
    'cmd_refresh_tree', '_on_cmd_tree_select', '_on_cmd_tree_toggle', '_on_cmd_tree_double_click', '_open_cmd_code_editor',
    'cmd_add_command', 'cmd_edit_command', 'cmd_delete_command',
    'cmd_execute_all', 'cmd_pause_all', 'cmd_resume_all', 'cmd_stop_all',
    'cmd_clear_all', 'cmd_save_list', 'cmd_load_list', 'cmd_upload_sync',
    '_on_exec_mode_changed',
    '_load_command_templates', '_save_command_templates', '_collect_edit_data',
    '_format_coords_text', '_format_exec_mode_text', '_format_exec_mode_short', '_get_countdown_text', '_get_countdown_display', '_get_remaining_seconds',
    '_cmd_execute_thread', '_execute_single_command', '_wait_until_time', '_parse_time_to_seconds',
    '_update_cmd_status_message', '_update_cmd_list_source', '_process_next_queued_command', '_stop_countdown_timer', '_start_countdown_timer', '_update_countdown_display',
    # 工作组处理函数
    'wg_create_dialog', 'wg_manage_dialog', 'wg_join_dialog', 'wg_pause_control', 'wg_leave',
    '_get_server_url', '_detect_best_server', '_get_username', '_get_workgroup_local_dir',
    '_start_wg_sync', '_stop_wg_sync', '_wg_sync_tick', '_refresh_shared_commands_tick',
    '_pause_sync_temporarily', '_resume_sync', '_update_command_to_server',
    '_load_shared_commands', '_save_shared_commands', '_wg_request',
    '_is_paused', '_check_pause_remaining', '_start_pause_timer', '_stop_pause_timer', '_check_pause_expired',
    '_save_local_cmd_list_backup', '_load_local_cmd_list_backup',
    '_sync_workgroup_files', '_upload_local_files', '_download_server_files',
    '_start_countdown_timer', '_stop_countdown_timer', '_update_countdown_display',
    # 激活系统处理函数
    'load_activation_config', 'save_activation_config',
    'activation_api_post', 'activation_api_get',
    'auto_activation_login', 'on_activation_login', 'on_activation_register', 'on_activation_logout',
    'on_activation_purchase', 'on_activation_activate', 'on_activation_sync',
    'on_activation_auto_sync', 'on_activation_ticket', 'update_activation_status',
    'switch_to_tab_if_needed',
    'update_trial_status_display', 'on_daily_trial_tick', 'on_daily_trial_expired',
    '_lock_functional_tabs', '_unlock_functional_tabs',
    '_get_activation_server_url', 'set_activation_server_url',
    # API设置辅助函数
    '_get_api_placeholder', '_get_model_placeholder', '_get_api_suffix', '_get_current_api_config',
    # AI代码执行函数
    '_execute_ai_code_workflow'
]

# 绑定ActivationManager和对话框类到MainWindow
if hasattr(tabs_module, 'ActivationManager'):
    MainWindow.ActivationManager = tabs_module.ActivationManager
if hasattr(tabs_module, 'ActivationRegisterDialog'):
    MainWindow.ActivationRegisterDialog = tabs_module.ActivationRegisterDialog
if hasattr(tabs_module, 'ActivationCodeDialog'):
    MainWindow.ActivationCodeDialog = tabs_module.ActivationCodeDialog
if hasattr(tabs_module, 'ActivationPurchaseDialog'):
    MainWindow.ActivationPurchaseDialog = tabs_module.ActivationPurchaseDialog
if hasattr(tabs_module, 'ActivationTicketDialog'):
    MainWindow.ActivationTicketDialog = tabs_module.ActivationTicketDialog
if hasattr(tabs_module, 'CommandEditDialog'):
    MainWindow.CommandEditDialog = tabs_module.CommandEditDialog


for handler_name in handlers_to_bind:
    if hasattr(handlers_module, handler_name):
        setattr(MainWindow, handler_name, getattr(handlers_module, handler_name))
    elif hasattr(discovery_handlers_module, handler_name):
        setattr(MainWindow, handler_name, getattr(discovery_handlers_module, handler_name))
    elif hasattr(tabs_module, handler_name):
        setattr(MainWindow, handler_name, getattr(tabs_module, handler_name))


def load_multimodal_model(self):
    """加载本地多模态大模型"""
    def show_message(msg):
        """显示消息"""
        if hasattr(self, 'status_display'):
            self.status_display.insert(tk.END, msg + '\n')
            self.status_display.see(tk.END)
        print(msg)

    try:
        # 检查配置
        if not self.config.load_multimodal_model:
            print("多模态大模型开关已关闭,不加载模型")
            return

        # 检查是否已经加载
        if self.multimodal_model is not None:
            print("多模态大模型已加载,无需重复加载")
            return

        # 导入多模态相关模块
        print("正在导入多模态模块...")
        try:
            from transformers import AutoProcessor, AutoModel, AutoTokenizer, AutoModelForImageTextToText
            from PIL import Image
            import torch
        except ImportError as e:
            show_message(f"错误:无法导入多模态模块 - {str(e)}")
            print(f"错误:无法导入多模态模块 - {str(e)}")
            self.config.load_multimodal_model = False
            self.config.save()
            return

        # 查找本地模型目录
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(base_dir, 'models', 'multimodal')

        if not os.path.exists(model_dir):
            show_message(f"错误:本地模型目录不存在 - {model_dir}")
            print(f"错误:本地模型目录不存在 - {model_dir}")
            self.config.load_multimodal_model = False
            self.config.save()
            return

        print(f"正在从本地加载多模态模型: {model_dir}")

        # 加载模型和处理器
        try:
            # 1. 加载处理器
            self.multimodal_processor = AutoProcessor.from_pretrained(model_dir)

            # 2. 只加载一次模型
            self.multimodal_model = AutoModelForImageTextToText.from_pretrained(
                model_dir,
                dtype=torch.float32,
                device_map="auto",
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )

            # 将模型和处理器共享给 AIEngine
            self.ai_engine.model = self.multimodal_model
            self.ai_engine.processor = self.multimodal_processor

            print(f"多模态模型加载成功")
            show_message("本地多模态大模型(models\\multimodal)加载成功")
        except Exception as e:
            show_message(f"错误:模型加载失败 - {str(e)}")
            print(f"错误:模型加载失败 - {str(e)}")
            self.multimodal_model = None
            self.multimodal_processor = None
            self.ai_engine.model = None
            self.ai_engine.processor = None
            self.config.load_multimodal_model = False
            self.config.save()
            return

    except Exception as e:
        show_message(f"加载多模态大模型时发生错误: {str(e)}")
        print(f"加载多模态大模型时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


def unload_multimodal_model(self):
    """卸载本地多模态大模型,释放内存"""
    def show_message(msg):
        """显示消息"""
        if hasattr(self, 'status_display'):
            self.status_display.insert(tk.END, msg + '\n')
            self.status_display.see(tk.END)
        print(msg)

    try:
        # 清空 main.py 的模型
        if self.multimodal_model is not None or self.multimodal_processor is not None:
            print("正在卸载多模态大模型...")
            self.multimodal_model = None
            self.multimodal_processor = None
        else:
            print("多模态大模型未加载,无需卸载")

        # 清空 AIEngine 的模型
        if self.ai_engine.model is not None or self.ai_engine.processor is not None:
            print("正在卸载 AIEngine 的多模态模型...")
            self.ai_engine.model = None
            self.ai_engine.processor = None

        # 清理 GPU 缓存
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print("GPU 缓存已清理")
        except:
            pass

        # 导入垃圾回收
        import gc
        gc.collect()

        print("多模态大模型已卸载")
        show_message("本地多模态大模型已卸载,内存已释放")

    except Exception as e:
        show_message(f"卸载多模态大模型时发生错误: {str(e)}")
        print(f"卸载多模态大模型时发生错误: {str(e)}")


# 绑定多模态模型加载方法到 MainWindow 类
MainWindow.load_multimodal_model = load_multimodal_model
MainWindow.unload_multimodal_model = unload_multimodal_model


def main():
    """主函数"""
    window = MainWindow()
    window.root.mainloop()


if __name__ == '__main__':
    main()
