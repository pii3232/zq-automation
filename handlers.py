"""AutoZS - 事件处理函数 - Tkinter版本"""
import os
import json
import time
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pyautogui
import requests

# 使用Tkinter
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, scrolledtext

# 导入消息框函数
from tabs import msg_warning, msg_information, msg_critical, msg_question, ActivationManager


# ==================== 全局监听器类 ====================

class GlobalClickListener:
    """全局点击监听器"""
    def __init__(self, main_window):
        self.main_window = main_window
        self.pynput_listener = None

    def start(self):
        """开始监听点击"""
        try:
            from pynput import mouse
            self.pynput_listener = mouse.Listener(on_click=self.on_click)
            self.pynput_listener.start()
        except ImportError as e:
            print(f"[GlobalClickListener] pynput 导入失败: {e}")
        except Exception as e:
            print(f"启动全局点击监听器失败: {e}")

    def stop(self):
        """停止监听"""
        if self.pynput_listener:
            try:
                self.pynput_listener.stop()
            except Exception as e:
                print(f"停止全局点击监听器失败: {e}")
            self.pynput_listener = None

    def on_click(self, x, y, button, pressed):
        """点击事件处理"""
        try:
            if pressed:  # 按下时才处理
                # button 是 pynput.mouse.Button 对象，需要用 str(button) 转换
                # str(button) 会返回 'Button.left' 或 'Button.right'
                button_str = str(button)
                self.main_window.on_global_click(x, y, button_str)
        except NotImplementedError:
            pass
        except Exception as e:
            print(f"处理点击事件失败: {e}")


class LongRecordingListener:
    """长时间录制监听器（同时监听鼠标和键盘）- 增强版支持双击、拖动、滑动"""
    def __init__(self, main_window):
        self.main_window = main_window
        self.mouse_listener = None
        self.keyboard_listener = None
        self.last_event_time = None
        self.is_running = False
        self.error_message = None
        
        self.last_click_time = None
        self.last_click_x = 0
        self.last_click_y = 0
        self.last_click_button = None
        self.double_click_threshold = 0.3
        
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.drag_start_time = None
        self.is_dragging = False
        self.drag_button = None
        self.drag_threshold = 5
        self.pending_click = None
        
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        
    def start(self):
        """开始监听，返回是否成功"""
        try:
            from pynput import mouse, keyboard
            
            self.mouse_listener = mouse.Listener(
                on_click=self.on_mouse_click,
                on_scroll=self.on_mouse_scroll,
                on_move=self.on_mouse_move
            )
            self.mouse_listener.start()
            
            self.keyboard_listener = keyboard.Listener(
                on_press=self.on_key_press,
                on_release=self.on_key_release
            )
            self.keyboard_listener.start()
            
            self.last_event_time = datetime.now()
            self.is_running = True
            return True
            
        except ImportError as e:
            self.error_message = f"缺少pynput库，请运行: pip install pynput\n错误: {e}"
            print(self.error_message)
            return False
        except Exception as e:
            self.error_message = f"启动长时间录制监听器失败: {e}"
            print(self.error_message)
            return False
            
    def stop(self):
        """停止监听"""
        self.is_running = False
        if self.mouse_listener:
            try:
                self.mouse_listener.stop()
            except Exception as e:
                print(f"停止鼠标监听器失败: {e}")
            self.mouse_listener = None
        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
            except Exception as e:
                print(f"停止键盘监听器失败: {e}")
            self.keyboard_listener = None
            
    def on_mouse_move(self, x, y):
        """鼠标移动事件 - 用于追踪滑动轨迹和检测拖动"""
        try:
            if self.is_dragging:
                self.last_mouse_x = x
                self.last_mouse_y = y
            else:
                self.last_mouse_x = x
                self.last_mouse_y = y
        except Exception as e:
            pass
            
    def on_mouse_click(self, x, y, button, pressed):
        """鼠标点击事件 - 支持双击和拖动检测"""
        try:
            button_map = {
                'Button.left': 'left',
                'Button.right': 'right',
                'Button.middle': 'middle'
            }
            button_name = button_map.get(str(button), str(button))
            
            if pressed:
                self.drag_start_x = x
                self.drag_start_y = y
                self.drag_start_time = datetime.now()
                self.is_dragging = True
                self.drag_button = button_name
                self.pending_click = {
                    'x': x,
                    'y': y,
                    'button': button_name,
                    'time': datetime.now()
                }
            else:
                if not self.is_dragging:
                    return
                    
                self.is_dragging = False
                distance = ((x - self.drag_start_x) ** 2 + (y - self.drag_start_y) ** 2) ** 0.5
                
                if distance > self.drag_threshold:
                    current_time = datetime.now()
                    delay = (current_time - self.last_event_time).total_seconds()
                    duration = (current_time - self.drag_start_time).total_seconds()
                    
                    self.main_window.add_long_recording_event({
                        'type': 'mouse_drag',
                        'button': button_name,
                        'start_x': self.drag_start_x,
                        'start_y': self.drag_start_y,
                        'end_x': x,
                        'end_y': y,
                        'duration': duration,
                        'distance': distance,
                        'delay': delay
                    })
                    
                    self.last_event_time = current_time
                    self.pending_click = None
                else:
                    self._handle_click_event(x, y, button_name)
                    
        except Exception as e:
            print(f"处理鼠标点击事件失败: {e}")
            import traceback
            traceback.print_exc()
            
    def _handle_click_event(self, x, y, button_name):
        """处理点击事件（包括双击检测）"""
        try:
            current_time = datetime.now()
            
            is_double_click = False
            if (self.last_click_time and 
                abs(self.last_click_x - x) < 5 and 
                abs(self.last_click_y - y) < 5 and
                self.last_click_button == button_name and
                (current_time - self.last_click_time).total_seconds() < self.double_click_threshold):
                is_double_click = True
                
            if is_double_click:
                delay = (current_time - self.last_event_time).total_seconds()
                self.main_window.add_long_recording_event({
                    'type': 'mouse_double_click',
                    'button': button_name,
                    'x': x,
                    'y': y,
                    'delay': delay
                })
                self.last_click_time = None
            else:
                delay = (current_time - self.last_event_time).total_seconds()
                self.main_window.add_long_recording_event({
                    'type': 'mouse_click',
                    'button': button_name,
                    'x': x,
                    'y': y,
                    'delay': delay
                })
                self.last_click_time = current_time
                self.last_click_x = x
                self.last_click_y = y
                self.last_click_button = button_name
                
            self.last_event_time = current_time
            self.pending_click = None
            
        except Exception as e:
            print(f"处理点击事件失败: {e}")
            
    def on_mouse_scroll(self, x, y, dx, dy):
        """鼠标滚动事件"""
        try:
            current_time = datetime.now()
            delay = (current_time - self.last_event_time).total_seconds()
            
            self.main_window.add_long_recording_event({
                'type': 'mouse_scroll',
                'x': x,
                'y': y,
                'dx': dx,
                'dy': dy,
                'delay': delay
            })
            
            self.last_event_time = current_time
        except NotImplementedError:
            pass
        except Exception as e:
            print(f"处理鼠标滚动事件失败: {e}")
        
    def on_key_press(self, key):
        """键盘按下事件"""
        try:
            try:
                key_char = key.char
            except AttributeError:
                key_char = str(key)
                
            current_time = datetime.now()
            delay = (current_time - self.last_event_time).total_seconds()
            
            self.main_window.add_long_recording_event({
                'type': 'key_press',
                'key': key_char,
                'delay': delay
            })
            
            self.last_event_time = current_time
        except NotImplementedError:
            pass
        except Exception as e:
            print(f"处理键盘按下事件失败: {e}")
        
    def on_key_release(self, key):
        """键盘释放事件"""
        try:
            try:
                key_char = key.char
            except AttributeError:
                key_char = str(key)
        except NotImplementedError:
            pass
        except Exception as e:
            print(f"处理键盘释放事件失败: {e}")


# ==================== 设置相关处理函数 ====================

def on_mouse_coord_changed(self):
    """鼠标坐标显示开关变化"""
    self.show_mouse_coordinates = self.mouse_coord_var.get()
    self.config.show_mouse_coordinates = self.show_mouse_coordinates
    self.config.save()
    
    if self.show_mouse_coordinates:
        self.update_mouse_coordinates()
    elif self.mouse_coord_timer:
        self.root.after_cancel(self.mouse_coord_timer)


def on_interval_changed(self):
    """间隔时间变化"""
    try:
        value = int(self.interval_var.get())
        self.config.global_interval = value
        self.config.save()
        print(f"间隔时间已更新为: {value}ms")
    except ValueError:
        pass


def on_thread_count_changed(self):
    """线程数变化"""
    try:
        value = int(self.thread_var.get())
        self.config.task_thread_count = value
        self.config.save()
        print(f"线程数已更新为: {value}")
    except ValueError:
        pass


def on_similarity_changed(self, value=None):
    """相似度变化"""
    try:
        value = int(self.similarity_var.get())
        self.config.global_similarity = value
        self.global_similarity = value / 100.0
        self.similarity_label.config(text=f'{value}%')
        self.config.save()
    except ValueError:
        pass


def on_model_selection_changed(self):
    """模型选择变化"""
    model = self.model_var.get()
    self.config.load_multimodal_model = (model == 'local')
    self.config.save()
    
    # 显示/隐藏API设置按钮
    if model == 'api':
        self.api_settings_button.pack(side=tk.LEFT, padx=5)
    else:
        self.api_settings_button.pack_forget()


def on_api_settings_clicked(self):
    """API设置按钮点击"""
    dialog = tk.Toplevel(self.root)
    dialog.title('API设置')
    dialog.geometry('500x400')
    
    # API提供商
    provider_frame = ttk.Frame(dialog)
    provider_frame.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(provider_frame, text='API提供商:').pack(side=tk.LEFT, padx=5)
    provider_combo = ttk.Combobox(provider_frame, values=['百度API', '小米API', '讯飞API', '智谱API'])
    provider_combo.insert(0, getattr(self.config, 'api_provider', '百度API'))
    provider_combo.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # Base URL
    url_frame = ttk.Frame(dialog)
    url_frame.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(url_frame, text='Base URL:').pack(side=tk.LEFT, padx=5)
    url_entry = ttk.Entry(url_frame, width=50)
    url_entry.insert(0, getattr(self.config, 'api_base_url', ''))
    url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # API Key
    key_frame = ttk.Frame(dialog)
    key_frame.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(key_frame, text='API Key:').pack(side=tk.LEFT, padx=5)
    key_entry = ttk.Entry(key_frame, width=50)
    key_entry.insert(0, getattr(self.config, 'api_key', ''))
    key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # Model
    model_frame = ttk.Frame(dialog)
    model_frame.pack(fill=tk.X, padx=5, pady=5)
    ttk.Label(model_frame, text='Model:').pack(side=tk.LEFT, padx=5)
    model_entry = ttk.Entry(model_frame, width=50)
    model_entry.insert(0, getattr(self.config, 'api_model', 'gpt-3.5-turbo'))
    model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    
    # 保存按钮
    def save():
        self.config.api_provider = provider_combo.get()
        self.config.api_base_url = url_entry.get()
        self.config.api_key = key_entry.get()
        self.config.api_model = model_entry.get()
        self.config.save()
        dialog.destroy()
        print("API设置已保存")
    
    ttk.Button(dialog, text='保存', command=save).pack(pady=10)


def on_multimodal_model_changed(self):
    """多模态模型设置变化"""
    pass


def update_mouse_coordinates(self):
    """更新鼠标坐标显示"""
    if self.show_mouse_coordinates:
        try:
            x, y = pyautogui.position()
            # 更新坐标显示标签
            if hasattr(self, 'mouse_coord_label'):
                self.mouse_coord_label.config(text=f'当前坐标: ({x}, {y})')
        except Exception as e:
            print(f"更新鼠标坐标显示失败: {e}")
        
        # 每隔100ms更新一次
        self.mouse_coord_timer = self.root.after(100, self.update_mouse_coordinates)


# ==================== 截图相关处理函数 ====================

def take_screenshot(self):
    """开始截图"""
    print("开始截图...")
    self.root.after(100, self._do_screenshot)


def _do_screenshot(self):
    """执行截图"""
    # 最小化主窗口
    self.root.iconify()
    
    time.sleep(0.3)
    
    from main import ScreenshotWidget
    self.screenshot_widget = ScreenshotWidget(self, recording_mode=None)
    self.screenshot_widget.pic_directory = self.config.pic_directory
    self.screenshot_widget.screenshot_callback = lambda path: self._on_screenshot_taken(path)
    self.screenshot_widget.right_click_callback = lambda: self._on_screenshot_widget_closed()
    self.screenshot_widget.start()


def _on_screenshot_taken(self, filepath):
    """截图完成回调"""
    self.root.deiconify()
    
    if filepath:
        print(f"截图已保存: {filepath}")
        self.current_screenshot = filepath
        
        if hasattr(self, 'tools_screenshot_label'):
            try:
                from PIL import Image, ImageTk
                img = Image.open(filepath)
                img.thumbnail((800, 200))
                photo = ImageTk.PhotoImage(img)
                self.tools_screenshot_label.config(image=photo, text='')
                self.tools_screenshot_label.image = photo
            except:
                self.tools_screenshot_label.config(text=f'截图已保存: {os.path.basename(filepath)}')
            
            if hasattr(self, '_screenshot_clear_timer') and self._screenshot_clear_timer:
                self.root.after_cancel(self._screenshot_clear_timer)
            self._screenshot_clear_timer = self.root.after(30000, self._clear_screenshot_display)
        
        if hasattr(self, 'recording_mode') and self.recording_mode == 'manual_record':
            self.add_screenshot_step(filepath)
            self.record_status_label.config(text=f'录制状态: 已录制 {len(self.recorded_steps)} 个步骤(点击截图继续,右键结束)')


def _clear_screenshot_display(self):
    """清空截图显示区"""
    if hasattr(self, 'tools_screenshot_label'):
        self.tools_screenshot_label.config(image='', text='暂无截图')
        if hasattr(self.tools_screenshot_label, 'image'):
            self.tools_screenshot_label.image = None
    self._screenshot_clear_timer = None


def _on_screenshot_widget_closed(self):
    """截图窗口关闭回调"""
    self.root.deiconify()


def toggle_recording(self):
    """切换录制状态"""
    pass


def start_multi_screenshot(self):
    """开始多图截图"""
    print("开始多图截图模式...")
    if hasattr(self, 'multi_screenshot_label'):
        self.multi_screenshot_label.config(text='多图截图模式:点击左键截图,右键结束')
    
    self.multi_screenshot_count = 0
    self._multi_screenshot_loop()


def _multi_screenshot_loop(self):
    """多图截图循环"""
    self.root.iconify()
    time.sleep(0.2)
    
    from main import ScreenshotWidget
    widget = ScreenshotWidget(self, recording_mode='multi')
    widget.pic_directory = self.config.pic_directory
    
    def on_taken(filepath):
        if filepath:
            self.multi_screenshot_count += 1
            if hasattr(self, 'multi_screenshot_label'):
                self.multi_screenshot_label.config(text=f'已截图 {self.multi_screenshot_count} 张,继续截图或右键结束')
            self.root.after(200, self._multi_screenshot_loop)
        else:
            self.root.deiconify()
            if hasattr(self, 'multi_screenshot_label'):
                self.multi_screenshot_label.config(text=f'多图截图完成,共 {self.multi_screenshot_count} 张')
    
    widget.screenshot_callback = on_taken
    widget.right_click_callback = lambda: self.root.deiconify()
    widget.start()


# ==================== 关键词相关处理函数 ====================

def insert_keyword(self, keyword):
    """插入关键词到当前输入框"""
    print(f"插入关键词: {keyword}")


def create_keyword(self):
    """创建新关键词"""
    name = simpledialog.askstring('创建关键词', '输入关键词名称:', parent=self.root)
    if name:
        # 简化版本:创建一个基本的关键词
        self.keyword_manager.add_keyword(name, '用户自定义关键词', 'print("执行自定义关键词")', [])
        self.load_keywords()
        print(f"关键词 '{name}' 已创建")


def edit_keyword(self):
    """编辑关键词"""
    selection = self.keyword_list.curselection()
    if not selection:
        msg_warning(self, '警告', '请先选择一个关键词')
        return
    
    index = selection[0]
    keywords = self.keyword_manager.get_all_keywords()
    if index < len(keywords):
        keyword = keywords[index]
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f'编辑关键词: {keyword["name"]}')
        edit_window.geometry('600x500')
        edit_window.transient(self.root)
        
        ttk.Label(edit_window, text='关键词名称:').pack(anchor=tk.W, padx=10, pady=5)
        name_entry = ttk.Entry(edit_window, width=60)
        name_entry.insert(0, keyword['name'])
        name_entry.pack(padx=10, pady=5)
        
        ttk.Label(edit_window, text='描述:').pack(anchor=tk.W, padx=10, pady=5)
        desc_entry = ttk.Entry(edit_window, width=60)
        desc_entry.insert(0, keyword.get('description', ''))
        desc_entry.pack(padx=10, pady=5)
        
        ttk.Label(edit_window, text='脚本代码:').pack(anchor=tk.W, padx=10, pady=5)
        script_text = scrolledtext.ScrolledText(edit_window, width=70, height=15)
        script_text.insert(tk.END, keyword.get('script', ''))
        script_text.pack(padx=10, pady=5)
        
        ttk.Label(edit_window, text='参数(逗号分隔):').pack(anchor=tk.W, padx=10, pady=5)
        params_entry = ttk.Entry(edit_window, width=60)
        params_entry.insert(0, ','.join(keyword.get('parameters', [])))
        params_entry.pack(padx=10, pady=5)
        
        def save_changes():
            new_name = name_entry.get().strip()
            new_desc = desc_entry.get().strip()
            new_script = script_text.get('1.0', tk.END).strip()
            new_params = [p.strip() for p in params_entry.get().split(',') if p.strip()]
            
            if new_name:
                old_name = keyword['name']
                keyword['name'] = new_name
                keyword['description'] = new_desc
                keyword['script'] = new_script
                keyword['parameters'] = new_params
                self.keyword_manager.save_keywords()
                self.load_keywords()
                edit_window.destroy()
                print(f"关键词 '{old_name}' 已更新")
        
        ttk.Button(edit_window, text='保存', command=save_changes).pack(pady=10)


def delete_keyword(self):
    """删除关键词"""
    selection = self.keyword_list.curselection()
    if not selection:
        msg_warning(self, '警告', '请先选择一个关键词')
        return
    
    if msg_question(self, '确认', '确定要删除选中的关键词吗?'):
        index = selection[0]
        keywords = self.keyword_manager.get_all_keywords()
        if index < len(keywords):
            name = keywords[index]['name']
            self.keyword_manager.delete_keyword(name)
            self.load_keywords()
            print(f"关键词 '{name}' 已删除")


def copy_keyword(self):
    """复制关键词"""
    selection = self.keyword_list.curselection()
    if not selection:
        msg_warning(self, '警告', '请先选择一个关键词')
        return
    
    new_name = simpledialog.askstring('复制关键词', '输入新关键词名称:', parent=self.root)
    if new_name:
        index = selection[0]
        keywords = self.keyword_manager.get_all_keywords()
        if index < len(keywords):
            old_name = keywords[index]['name']
            self.keyword_manager.copy_keyword(old_name, new_name)
            self.load_keywords()
            print(f"关键词 '{old_name}' 已复制为 '{new_name}'")


def use_keyword(self):
    """使用关键词"""
    selection = self.keyword_list.curselection()
    if selection:
        index = selection[0]
        keywords = self.keyword_manager.get_all_keywords()
        if index < len(keywords):
            keyword = keywords[index]
            print(f"使用关键词: {keyword['name']}")


def load_keywords(self):
    """加载关键词列表"""
    self.keyword_list.delete(0, tk.END)
    keywords = self.keyword_manager.get_all_keywords()
    for kw in keywords:
        self.keyword_list.insert(tk.END, f"{kw['name']} - {kw.get('description', '')}")


# ==================== 工作流相关处理函数 ====================

def create_workflow(self):
    """创建新工作流"""
    from tabs import WorkflowEditDialog
    dialog = WorkflowEditDialog(self)
    self.root.wait_window(dialog.dialog)
    
    if dialog.result:
        if self.workflow_manager.add_workflow(dialog.result['name'], dialog.result['steps']):
            self.load_workflows()
            print(f"工作流 '{dialog.result['name']}' 已创建")
        else:
            msg_warning(self, '警告', '工作流名称已存在')


def edit_workflow(self):
    """编辑工作流"""
    selection = self.workflow_table.selection()
    if not selection:
        msg_warning(self, '警告', '请先选择一个工作流')
        return
    
    item = selection[0]
    index = self.workflow_table.index(item)
    workflows = self.workflow_manager.get_all_workflows()
    
    if index < len(workflows):
        workflow = workflows[index]
        from tabs import WorkflowEditDialog
        dialog = WorkflowEditDialog(self, workflow=workflow)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.workflow_manager.update_workflow(workflow['name'], **dialog.result)
            self.load_workflows()
            print(f"工作流 '{workflow['name']}' 已更新")


def delete_workflow(self):
    """删除工作流"""
    selection = self.workflow_table.selection()
    if not selection:
        msg_warning(self, '警告', '请先选择一个工作流')
        return
    
    if msg_question(self, '确认', '确定要删除选中的工作流吗?'):
        item = selection[0]
        index = self.workflow_table.index(item)
        workflows = self.workflow_manager.get_all_workflows()
        
        if index < len(workflows):
            name = workflows[index]['name']
            self.workflow_manager.delete_workflow(name)
            self.load_workflows()
            print(f"工作流 '{name}' 已删除")


def copy_workflow(self):
    """复制工作流"""
    selection = self.workflow_table.selection()
    if not selection:
        msg_warning(self, '警告', '请先选择一个工作流')
        return
    
    new_name = simpledialog.askstring('复制工作流', '输入新工作流名称:', parent=self.root)
    if new_name:
        item = selection[0]
        index = self.workflow_table.index(item)
        workflows = self.workflow_manager.get_all_workflows()
        
        if index < len(workflows):
            old_name = workflows[index]['name']
            self.workflow_manager.copy_workflow(old_name, new_name)
            self.load_workflows()
            print(f"工作流 '{old_name}' 已复制为 '{new_name}'")


def clear_all_workflows(self):
    """清空所有工作流"""
    if msg_question(self, '确认', '确定要清空所有工作流吗?'):
        self.workflow_manager.clear_all_workflows()
        self.load_workflows()
        print("所有工作流已清空")


def execute_workflow(self, row=None):
    """执行工作流"""
    selection = self.workflow_table.selection()
    if not selection:
        msg_warning(self, '警告', '请先选择一个工作流')
        return
    
    item = selection[0]
    index = self.workflow_table.index(item)
    workflows = self.workflow_manager.get_all_workflows()
    
    if index < len(workflows):
        workflow = workflows[index]
        workflow_name = workflow['name']
        print(f"执行工作流: {workflow_name}")
        
        # 在新线程中执行工作流
        def run_workflow():
            try:
                self.task_manager._execute_workflow(workflow_name)
                print(f"工作流 '{workflow_name}' 执行完成")
            except Exception as e:
                print(f"工作流执行失败: {e}")
        
        thread = threading.Thread(target=run_workflow, daemon=True)
        thread.start()


def load_workflows(self):
    """加载工作流列表"""
    # 清空表格
    for item in self.workflow_table.get_children():
        self.workflow_table.delete(item)
    
    workflows = self.workflow_manager.get_all_workflows()
    for wf in workflows:
        status = '就绪'
        name = wf.get('name', '')
        steps_count = len(wf.get('steps', []))
        self.workflow_table.insert('', tk.END, values=(status, name, steps_count))


# ==================== 任务相关处理函数 ====================

def add_task(self):
    """添加任务"""
    workflows = self.workflow_manager.get_all_workflows()
    if not workflows:
        msg_warning(self, '警告', '没有可用的工作流,请先创建工作流')
        return
    
    # 简化版本:让用户选择一个工作流
    from tkinter import simpledialog
    workflow_names = [w['name'] for w in workflows]
    
    dialog = tk.Toplevel(self.root)
    dialog.title('添加任务')
    dialog.geometry('400x200')
    
    ttk.Label(dialog, text='选择工作流:').pack(pady=5)
    workflow_combo = ttk.Combobox(dialog, values=workflow_names, state='readonly')
    workflow_combo.pack(pady=5, padx=10, fill=tk.X)
    
    ttk.Label(dialog, text='执行次数:').pack(pady=5)
    repeat_spin = ttk.Spinbox(dialog, from_=1, to=100, width=10)
    repeat_spin.delete(0, tk.END)
    repeat_spin.insert(0, '1')
    repeat_spin.pack(pady=5)
    
    def add():
        workflow = workflow_combo.get()
        if workflow:
            repeat_count = int(repeat_spin.get())
            task_id = self.task_manager.add_task(workflow_name=workflow, repeat_count=repeat_count)
            self.load_tasks_list()
            dialog.destroy()
            print(f"任务已添加: {workflow}, 任务ID: {task_id}")
    
    ttk.Button(dialog, text='添加', command=add).pack(pady=10)


def edit_task(self):
    """编辑任务"""
    selection = self.task_list.curselection()
    if not selection:
        msg_warning(self, '警告', '请先选择一个任务')
        return
    
    index = selection[0]
    tasks = self.task_manager.get_all_tasks()
    if index >= len(tasks):
        return
    
    task = tasks[index]
    
    edit_window = tk.Toplevel(self.root)
    edit_window.title(f'编辑任务: {task.get("id", "")}')
    edit_window.geometry('400x250')
    edit_window.transient(self.root)
    
    workflows = self.workflow_manager.get_all_workflows()
    workflow_names = [w['name'] for w in workflows]
    
    ttk.Label(edit_window, text='工作流:').pack(anchor=tk.W, padx=10, pady=5)
    workflow_combo = ttk.Combobox(edit_window, values=workflow_names, state='readonly')
    workflow_combo.set(task.get('workflow_name', ''))
    workflow_combo.pack(padx=10, pady=5, fill=tk.X)
    
    ttk.Label(edit_window, text='执行次数:').pack(anchor=tk.W, padx=10, pady=5)
    repeat_spin = ttk.Spinbox(edit_window, from_=1, to=100, width=10)
    repeat_spin.delete(0, tk.END)
    repeat_spin.insert(0, str(task.get('repeat_count', 1)))
    repeat_spin.pack(padx=10, pady=5)
    
    ttk.Label(edit_window, text='状态:').pack(anchor=tk.W, padx=10, pady=5)
    status_var = tk.StringVar(value=task.get('status', 'pending'))
    status_combo = ttk.Combobox(edit_window, textvariable=status_var, 
                                values=['pending', 'running', 'completed', 'paused'], state='readonly')
    status_combo.pack(padx=10, pady=5, fill=tk.X)
    
    def save_changes():
        task['workflow_name'] = workflow_combo.get()
        task['repeat_count'] = int(repeat_spin.get())
        task['status'] = status_var.get()
        self.task_manager.save_tasks()
        self.load_tasks_list()
        edit_window.destroy()
        print(f"任务已更新: {task.get('id', '')}")
    
    ttk.Button(edit_window, text='保存', command=save_changes).pack(pady=10)


def delete_task(self):
    """删除任务"""
    selection = self.task_list.curselection()
    if not selection:
        msg_warning(self, '警告', '请先选择一个任务')
        return
    
    if msg_question(self, '确认', '确定要删除选中的任务吗?'):
        index = selection[0]
        tasks = self.task_manager.get_all_tasks()
        if index < len(tasks):
            task_id = tasks[index]['id']
            self.task_manager.delete_task(task_id)
            self.load_tasks_list()
            print(f"任务已删除: {task_id}")


def toggle_task_pause(self):
    """切换任务暂停状态"""
    selection = self.task_list.curselection()
    if not selection:
        msg_warning(self, '警告', '请先选择一个任务')
        return
    
    index = selection[0]
    tasks = self.task_manager.get_all_tasks()
    if index < len(tasks):
        task = tasks[index]
        task_id = task['id']
        
        if task['status'] == 'paused':
            self.task_manager.resume_task(task_id)
            print(f"任务 {task_id} 已恢复")
        else:
            self.task_manager.pause_task(task_id)
            print(f"任务 {task_id} 已暂停")
        
        self.load_tasks_list()


def execute_task_now(self, task_id=None):
    """立即执行任务"""
    if not task_id:
        selection = self.task_list.curselection()
        if not selection:
            msg_warning(self, '警告', '请先选择一个任务')
            return
        
        index = selection[0]
        tasks = self.task_manager.get_all_tasks()
        if index < len(tasks):
            task_id = tasks[index]['id']
    
    if task_id:
        self.task_manager.execute_task_now(task_id)
        print(f"任务 {task_id} 已开始执行")


def clear_all_tasks(self):
    """清空所有任务"""
    if msg_question(self, '确认', '确定要清空所有任务吗?'):
        tasks = self.task_manager.get_all_tasks()
        for task in tasks:
            self.task_manager.delete_task(task['id'])
        self.load_tasks_list()
        print("所有任务已清空")


def save_tasks_to_file(self):
    """保存任务列表到文件"""
    filename = filedialog.asksaveasfilename(
        defaultextension='.json',
        filetypes=[('JSON文件', '*.json')],
        parent=self.root
    )
    if filename:
        self.task_manager.save_tasks_to_file(filename)
        msg_information(self, '成功', '任务列表保存成功')


def load_tasks_from_file(self):
    """从文件加载任务列表"""
    filename = filedialog.askopenfilename(
        filetypes=[('JSON文件', '*.json')],
        parent=self.root
    )
    if filename:
        self.task_manager.load_tasks_from_file(filename)
        self.load_tasks_list()
        msg_information(self, '成功', '任务列表加载成功')


def load_tasks_list(self):
    """加载任务列表"""
    self.task_list.delete(0, tk.END)
    tasks = self.task_manager.get_all_tasks()
    for task in tasks:
        workflow_items = task.get('workflow_items', [])
        if workflow_items:
            workflow_names = [item.get('workflow', '') for item in workflow_items]
            workflow_text = ' -> '.join(workflow_names)
        else:
            workflow_text = task.get('workflow', '未知')
        
        status = task.get('status', 'pending')
        status_text = {'pending': '待执行', 'running': '执行中', 'paused': '已暂停', 'completed': '已完成'}.get(status, status)
        
        self.task_list.insert(tk.END, f"{workflow_text} - {status_text}")


# ==================== AI聊天相关处理函数 ====================

def send_message(self):
    """发送聊天消息"""
    message = self.chat_input.get('1.0', tk.END).strip()
    if not message:
        return
    
    # 显示用户消息
    self.chat_display.config(state=tk.NORMAL)
    self.chat_display.insert(tk.END, f"用户: {message}\n\n")
    self.chat_display.see(tk.END)
    
    # 清空输入
    self.chat_input.delete('1.0', tk.END)
    
    # 保存到数据库
    self.database_manager.add_chat_message('user', message)
    
    # 调用AI引擎生成回复(简化版本)
    try:
        if self.ai_engine.model:
            # 本地模型
            messages = [{'role': 'user', 'content': message}]
            response = self.ai_engine.chat(messages)
        else:
            # API调用(简化版本)
            response = "AI模型未加载,请先配置API或加载本地模型"
        
        # 显示回复
        self.chat_display.insert(tk.END, f"AI: {response}\n\n")
        self.chat_display.see(tk.END)
        
        # 保存到数据库
        self.database_manager.add_chat_message('assistant', response)
        
    except Exception as e:
        error_msg = f"AI调用失败: {e}"
        self.chat_display.insert(tk.END, f"系统: {error_msg}\n\n")
        self.chat_display.see(tk.END)


def execute_from_chat(self):
    """从聊天生成工作流"""
    message = self.chat_input.get('1.0', tk.END).strip()
    if not message:
        msg_warning(self, '警告', '请输入您的指令')
        return
    
    # 简化版本:直接提示功能
    msg_information(self, '提示', 'AI生成工作流功能需要配置API或加载本地模型')


def clear_chat(self):
    """清空聊天记录"""
    self.chat_display.config(state=tk.NORMAL)
    self.chat_display.delete('1.0', tk.END)
    self.chat_display.config(state=tk.DISABLED)


def load_chat_history(self):
    """加载聊天历史"""
    try:
        history = self.database_manager.get_chat_history(limit=50)
        
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete('1.0', tk.END)
        
        for msg in reversed(history):
            role = '用户' if msg['role'] == 'user' else 'AI'
            self.chat_display.insert(tk.END, f"{role}: {msg['content']}\n\n")
        
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)
        
    except Exception as e:
        print(f"加载聊天历史失败: {e}")


# ==================== 录制相关处理函数 ====================

def start_left_click_record(self):
    """开始左击录制"""
    print("开始左击录制...")
    self.recording_mode = 'left_click'
    self.record_status_label.config(text='录制状态: 左击录制中...')


def start_double_click_record(self):
    """开始双击录制"""
    print("开始双击录制...")
    self.recording_mode = 'double_click'
    self.record_status_label.config(text='录制状态: 双击录制中...')


def start_right_click_record(self):
    """开始右击录制"""
    print("开始右击录制...")
    self.recording_mode = 'right_click'
    self.record_status_label.config(text='录制状态: 右击录制中...')


def on_click_record(self, x, y, button):
    """点击录制回调"""
    print(f"录制点击: ({x}, {y}) - {button}")


def finish_click_record(self):
    """完成点击录制"""
    print("点击录制完成")
    self.recording_mode = None
    self.record_status_label.config(text='录制状态: 未录制')


def start_manual_record(self):
    """开始手动截图录制 - 只进入录制状态，等待用户点击截图按钮"""
    print("开始手动截图录制...")
    self.recording_mode = 'manual_record'
    self.recorded_steps = []
    self.stop_record_button.config(state=tk.NORMAL)
    self.record_status_label.config(text='录制状态: 手动截图录制中(点击截图按钮截图,右键结束)')


def start_auto_record(self):
    """开始自动截图录制"""
    print("开始自动截图录制...")
    self.recording_mode = 'auto_record'
    self.stop_record_button.config(state=tk.NORMAL)
    self.record_status_label.config(text='录制状态: 自动截图录制中(右键结束)')
    
    self._auto_record_loop()


def _auto_record_loop(self):
    """自动截图录制循环"""
    if self.recording_mode != 'auto_record':
        return
    
    self.root.iconify()
    time.sleep(0.2)
    
    from main import ScreenshotWidget
    widget = ScreenshotWidget(self, recording_mode='auto_record')
    widget.pic_directory = self.config.pic_directory
    
    def on_taken(filepath):
        if filepath and self.recording_mode == 'auto_record':
            self.add_screenshot_step(filepath)
            self.root.after(200, self._auto_record_loop)
        else:
            self.root.deiconify()
    
    widget.screenshot_callback = on_taken
    widget.right_click_callback = lambda: self.finish_screenshot_record()
    widget.start()


def add_screenshot_step(self, filepath):
    """添加截图步骤"""
    if not hasattr(self, 'recorded_steps'):
        self.recorded_steps = []
    
    self.recorded_steps.append({
        'type': 'screenshot',
        'path': filepath,
        'timestamp': datetime.now().isoformat()
    })
    
    print(f"添加截图步骤: {filepath}")


def finish_screenshot_record(self):
    """完成截图录制"""
    print("截图录制完成")
    self.recording_mode = None
    self.stop_record_button.config(state=tk.DISABLED)
    
    step_count = len(self.recorded_steps) if hasattr(self, 'recorded_steps') else 0
    self.record_status_label.config(text=f'录制状态: 已录制 {step_count} 个步骤')
    
    self.root.deiconify()
    
    if step_count > 0:
        self.root.after(100, self._prompt_save_workflow)


def _prompt_save_workflow(self):
    """提示用户保存工作流"""
    result = messagebox.askyesno('保存工作流', '是否将录制内容保存为工作流？')
    if result:
        self.save_record_as_workflow()


def save_record_as_workflow(self):
    """将录制内容保存为工作流"""
    if not hasattr(self, 'recorded_steps') or not self.recorded_steps:
        self.add_status_message("没有录制内容可保存")
        return
    
    workflow_name = simpledialog.askstring('保存工作流', '输入工作流名称:', parent=self.root)
    if not workflow_name:
        return
    
    steps = []
    for step in self.recorded_steps:
        if isinstance(step, dict):
            if step.get('type') == 'screenshot':
                path = step.get('path', '')
                filename = os.path.basename(path) if path else ''
                if filename:
                    steps.append({
                        'keyword': '找图',
                        'params': filename
                    })
            elif 'keyword' in step:
                steps.append(step)
            else:
                pass
        elif isinstance(step, str):
            if step.startswith('点击|'):
                parts = step.split('|')
                if len(parts) > 1:
                    coords = parts[1].split(',')
                    steps.append({
                        'keyword': '点击',
                        'params': f'{coords[0]},{coords[1]}'
                    })
            elif step.startswith('双击|'):
                parts = step.split('|')
                if len(parts) > 1:
                    coords = parts[1].split(',')
                    steps.append({
                        'keyword': '双击',
                        'params': f'{coords[0]},{coords[1]}'
                    })
            elif step.startswith('右击|'):
                parts = step.split('|')
                if len(parts) > 1:
                    coords = parts[1].split(',')
                    steps.append({
                        'keyword': '右击',
                        'params': f'{coords[0]},{coords[1]}'
                    })
            elif step.startswith('找图|'):
                parts = step.split('|')
                if len(parts) > 1:
                    steps.append({
                        'keyword': '找图',
                        'params': parts[1]
                    })
            elif step.startswith('间隔|'):
                parts = step.split('|')
                if len(parts) > 1:
                    steps.append({
                        'keyword': '间隔',
                        'params': parts[1]
                    })
            else:
                steps.append({
                    'keyword': step,
                    'params': ''
                })
    
    if self.workflow_manager.add_workflow(workflow_name, steps):
        self.load_workflows()
        self.add_status_message(f"工作流已保存: {workflow_name}")
    else:
        self.add_status_message(f"工作流名称已存在: {workflow_name}")


def on_right_click_in_record(self):
    """录制中右键点击"""
    print("右键点击,结束录制")
    self.finish_screenshot_record()


def init_global_click_listener(self):
    """初始化全局点击监听器"""
    self.global_click_listener = GlobalClickListener(self)
    self.global_click_listener.start()


def on_global_click(self, x, y, button):
    """全局点击事件处理（从pynput线程调用，需要线程安全）"""
    # 自动截图录制模式 - 左键点击截图
    if getattr(self, 'recording_mode', None) == 'auto_record':
        if button == 'Button.left':
            # 确保PIC目录存在
            pic_dir = getattr(self.config, 'pic_directory', 'pic')
            os.makedirs(pic_dir, exist_ok=True)

            # 以点击坐标为中心，截取75x75的图片
            try:
                screenshot = pyautogui.screenshot(region=(x - 37, y - 37, 75, 75))

                # 保存截图
                record_prefix = getattr(self, 'record_prefix', 'screenshot')
                record_count = getattr(self, 'record_count', 0)
                filename = f"{record_prefix}_{record_count + 1}.png"
                filepath = os.path.join(pic_dir, filename)
                screenshot.save(filepath)

                # 添加步骤
                self.add_screenshot_step(filename, mode='find')

                # 显示状态提示（使用root.after确保线程安全）
                self.root.after(0, lambda fn=filename, mx=x, my=y: 
                    self.add_status_message(f"自动截图: {fn}，坐标({mx}, {my})"))

                # 在截图显示区显示截图
                try:
                    from PIL import ImageTk, Image
                    img = Image.open(filepath)
                    # 调整图片大小以适应标签
                    img = img.resize((200, 200), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.tools_screenshot_label.config(image=photo, text='')
                    self.tools_screenshot_label.image = photo  # 保持引用
                    self.current_screenshot = filepath
                except Exception as e:
                    print(f"自动截图显示失败: {e}")
                    
            except Exception as e:
                print(f"自动截图失败: {e}")

    # 右键停止录制（手动/自动录制模式）或停止所有任务
    if button == 'Button.right':
        if hasattr(self, 'recording_mode') and self.recording_mode in ['manual_record', 'auto_record']:
            # 使用root.after确保在主线程中执行
            self.root.after(0, self.on_right_click_in_record)
            # 录制模式下右键只停止录制，不停止其他任务
        else:
            # 非录制模式下，右键停止正在运行的任务
            # 检查是否有任务在运行，如果有则停止所有任务
            has_running_tasks = False
            if hasattr(self, 'daily_tasks_running') and self.daily_tasks_running:
                has_running_tasks = True
                self.stop_all_daily_tasks()
            if hasattr(self, 'answer_tasks_running') and self.answer_tasks_running:
                has_running_tasks = True
                self.stop_all_answer_tasks()
            if hasattr(self, 'discovery_tasks_running') and self.discovery_tasks_running:
                has_running_tasks = True
                self.stop_all_discovery_tasks()
            
            if has_running_tasks:
                self.root.after(0, lambda: self.add_status_message("已停止所有运行中的任务"))


# ==================== 其他处理函数 ====================

def execute_workflow_by_name(self, workflow_name):
    """按名称执行工作流"""
    print(f"执行工作流: {workflow_name}")
    
    def run():
        try:
            self.task_manager._execute_workflow(workflow_name)
            print(f"工作流 '{workflow_name}' 执行完成")
        except Exception as e:
            print(f"工作流执行失败: {e}")
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()


def start_long_recording(self):
    """开始长时间录制"""
    print("开始长时间录制...")
    
    # 创建监听器
    self.long_recording_listener = LongRecordingListener(self)
    
    # 启动监听器
    success = self.long_recording_listener.start()
    
    if success:
        self.long_recording_start_time = time.time()
        self.long_recording_events = []
        self.long_record_button.config(state=tk.DISABLED)
        self.stop_long_record_button.config(state=tk.NORMAL)
        self.add_status_message("长时间录制已开始")
    else:
        error_msg = getattr(self.long_recording_listener, 'error_message', '未知错误')
        msg_critical(self, "错误", f"启动长时间录制失败:\n{error_msg}")


def stop_long_recording(self):
    """停止长时间录制"""
    print("停止长时间录制")
    
    if hasattr(self, 'long_recording_listener') and self.long_recording_listener:
        self.long_recording_listener.stop()
        self.long_recording_listener = None
    
    self.long_record_button.config(state=tk.NORMAL)
    self.stop_long_record_button.config(state=tk.DISABLED)
    
    if self.long_recording_events:
        if len(self.long_recording_events) > 1:
            self.long_recording_events = self.long_recording_events[:-1]
        
        self.save_long_recording_record()
    else:
        self.add_status_message("长时间录制已停止（无事件记录）")


def add_long_recording_event(self, event):
    """添加长时间录制事件"""
    if hasattr(self, 'long_recording_events'):
        self.long_recording_events.append(event)


def save_long_recording_record(self):
    """保存长时间录制记录，同时保存到工作流列表"""
    if not self.long_recording_events:
        return
    
    record_name = simpledialog.askstring('保存记录', '输入记录名称:', parent=self.root)
    if record_name:
        record_file = os.path.join(self.config.projects_directory, 'records', f'{record_name}.json')
        os.makedirs(os.path.dirname(record_file), exist_ok=True)
        
        record = {
            'name': record_name,
            'events': self.long_recording_events,
            'created_at': datetime.now().isoformat()
        }
        
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        
        self.load_records()
        print(f"记录已保存: {record_name}")
        
        workflow_steps = self._convert_events_to_workflow_steps(self.long_recording_events)
        
        if workflow_steps:
            workflow = {
                'name': record_name,
                'steps': workflow_steps,
                'created_at': datetime.now().isoformat(),
                'source': 'long_recording'
            }
            
            if self.workflow_manager.add_workflow(record_name, workflow_steps):
                self.load_workflows()
                self.add_status_message(f"录制记录已保存，并添加到工作流列表: {record_name}")
            else:
                self.add_status_message(f"录制记录已保存，但工作流名称已存在: {record_name}")

def _convert_events_to_workflow_steps(self, events):
    """将录制事件转换为工作流步骤"""
    steps = []
    for event in events:
        event_type = event.get('type', '')
        
        if event_type == 'mouse_click':
            button = event.get('button', 'left')
            x = event.get('x', 0)
            y = event.get('y', 0)
            delay = event.get('delay', 0)
            
            if delay > 0.1:
                steps.append({
                    'keyword': '间隔',
                    'params': str(int(delay * 1000))
                })
            
            if button == 'right':
                steps.append({
                    'keyword': '右击',
                    'params': f'{x},{y}'
                })
            else:
                steps.append({
                    'keyword': '点击',
                    'params': f'{x},{y}'
                })
                
        elif event_type == 'mouse_double_click':
            button = event.get('button', 'left')
            x = event.get('x', 0)
            y = event.get('y', 0)
            delay = event.get('delay', 0)
            
            if delay > 0.1:
                steps.append({
                    'keyword': '间隔',
                    'params': str(int(delay * 1000))
                })
            
            steps.append({
                'keyword': '双击',
                'params': f'{x},{y}'
            })
            
        elif event_type == 'mouse_drag':
            button = event.get('button', 'left')
            start_x = event.get('start_x', 0)
            start_y = event.get('start_y', 0)
            end_x = event.get('end_x', 0)
            end_y = event.get('end_y', 0)
            delay = event.get('delay', 0)
            
            if delay > 0.1:
                steps.append({
                    'keyword': '间隔',
                    'params': str(int(delay * 1000))
                })
            
            steps.append({
                'keyword': '拖动',
                'params': f'{start_x},{start_y},{end_x},{end_y}'
            })
            
        elif event_type == 'mouse_scroll':
            x = event.get('x', 0)
            y = event.get('y', 0)
            dy = event.get('dy', 0)
            delay = event.get('delay', 0)
            
            if delay > 0.1:
                steps.append({
                    'keyword': '间隔',
                    'params': str(int(delay * 1000))
                })
            
            steps.append({
                'keyword': '滚动',
                'params': f'{x},{y},{dy}'
            })
            
        elif event_type == 'key_press':
            key = event.get('key', '')
            delay = event.get('delay', 0)
            
            if delay > 0.1:
                steps.append({
                    'keyword': '间隔',
                    'params': str(int(delay * 1000))
                })
            
            steps.append({
                'keyword': '按键',
                'params': key
            })
    
    return steps


def load_records(self):
    """加载录制记录列表"""
    self.record_list.delete(0, tk.END)
    
    records_dir = os.path.join(self.config.projects_directory, 'records')
    if os.path.exists(records_dir):
        for filename in os.listdir(records_dir):
            if filename.endswith('.json'):
                self.record_list.insert(tk.END, filename[:-5])


def execute_record(self):
    """执行录制记录"""
    selection = self.record_list.curselection()
    if not selection:
        return
    
    record_name = self.record_list.get(selection[0])
    record_file = os.path.join(self.config.projects_directory, 'records', f'{record_name}.json')
    
    if os.path.exists(record_file):
        with open(record_file, 'r', encoding='utf-8') as f:
            record = json.load(f)
        
        events = record.get('events', [])
        print(f"执行记录: {record_name}, 共 {len(events)} 个事件")
        self._execute_record_events(events)


def _execute_record_events(self, events):
    """执行记录事件 - 增强版支持双击、拖动、滑动等操作"""
    def run_events():
        try:
            self.add_status_message(f"开始执行录制操作，共 {len(events)} 个事件")
            
            for i, event in enumerate(events):
                event_type = event.get('type', '')
                delay = event.get('delay', 0)
                
                if delay > 0.1:
                    time.sleep(delay)
                
                if event_type == 'mouse_click':
                    button = event.get('button', 'left')
                    x = event.get('x', 0)
                    y = event.get('y', 0)
                    
                    if button == 'right':
                        pyautogui.rightClick(x, y)
                        self.add_status_message(f"执行右击: ({x}, {y})")
                    elif button == 'middle':
                        pyautogui.middleClick(x, y)
                        self.add_status_message(f"执行中键点击: ({x}, {y})")
                    else:
                        pyautogui.click(x, y)
                        self.add_status_message(f"执行点击: ({x}, {y})")
                        
                elif event_type == 'mouse_double_click':
                    button = event.get('button', 'left')
                    x = event.get('x', 0)
                    y = event.get('y', 0)
                    
                    if button == 'right':
                        pyautogui.rightClick(x, y)
                        time.sleep(0.05)
                        pyautogui.rightClick(x, y)
                        self.add_status_message(f"执行右键双击: ({x}, {y})")
                    else:
                        pyautogui.doubleClick(x, y)
                        self.add_status_message(f"执行双击: ({x}, {y})")
                        
                elif event_type == 'mouse_drag':
                    button = event.get('button', 'left')
                    start_x = event.get('start_x', 0)
                    start_y = event.get('start_y', 0)
                    end_x = event.get('end_x', 0)
                    end_y = event.get('end_y', 0)
                    duration = event.get('duration', 0.5)
                    
                    pyautogui.moveTo(start_x, start_y)
                    time.sleep(0.05)
                    
                    if button == 'right':
                        pyautogui.mouseDown(button='right')
                        pyautogui.moveTo(end_x, end_y, duration=min(duration, 1.0))
                        pyautogui.mouseUp(button='right')
                        self.add_status_message(f"执行右键拖动: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
                    else:
                        pyautogui.drag(end_x - start_x, end_y - start_y, duration=min(duration, 1.0))
                        self.add_status_message(f"执行拖动: ({start_x}, {start_y}) -> ({end_x}, {end_y})")
                        
                elif event_type == 'mouse_scroll':
                    x = event.get('x', 0)
                    y = event.get('y', 0)
                    dy = event.get('dy', 0)
                    
                    pyautogui.scroll(dy, x, y)
                    direction = "向上" if dy > 0 else "向下"
                    self.add_status_message(f"执行滚动: ({x}, {y}) {direction} {abs(dy)} 单位")
                    
                elif event_type == 'key_press':
                    key = event.get('key', '')
                    
                    if len(key) == 1:
                        pyautogui.press(key)
                    else:
                        key_name = key.replace('Key.', '').lower()
                        pyautogui.press(key_name)
                    
                    self.add_status_message(f"执行按键: {key}")
                    
            self.add_status_message("录制操作执行完成")
            
        except Exception as e:
            self.add_status_message(f"执行录制操作失败: {e}")
            print(f"执行录制操作失败: {e}")
            import traceback
            traceback.print_exc()
    
    thread = threading.Thread(target=run_events, daemon=True)
    thread.start()


def edit_record(self):
    """编辑录制记录"""
    selection = self.record_list.curselection()
    if not selection:
        msg_warning(self, '警告', '请先选择一个记录')
        return
    
    record_name = self.record_list.get(selection[0])
    record_file = os.path.join(self.config.projects_directory, 'records', f'{record_name}.json')
    
    if not os.path.exists(record_file):
        msg_warning(self, '警告', f'记录文件不存在: {record_name}')
        return
    
    with open(record_file, 'r', encoding='utf-8') as f:
        record = json.load(f)
    
    events = record.get('events', [])
    
    edit_window = tk.Toplevel(self.root)
    edit_window.title(f'编辑录制记录: {record_name}')
    edit_window.geometry('700x500')
    edit_window.transient(self.root)
    
    ttk.Label(edit_window, text='记录名称:').pack(anchor=tk.W, padx=10, pady=5)
    name_entry = ttk.Entry(edit_window, width=60)
    name_entry.insert(0, record_name)
    name_entry.pack(padx=10, pady=5)
    
    ttk.Label(edit_window, text='事件列表:').pack(anchor=tk.W, padx=10, pady=5)
    
    events_frame = ttk.Frame(edit_window)
    events_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    events_listbox = tk.Listbox(events_frame, height=15)
    events_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar = ttk.Scrollbar(events_frame, orient=tk.VERTICAL, command=events_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    events_listbox.config(yscrollcommand=scrollbar.set)
    
    for i, event in enumerate(events):
        event_type = event.get('type', 'unknown')
        if event_type == 'mouse_click':
            events_listbox.insert(tk.END, f"{i+1}. 点击 ({event.get('x', 0)}, {event.get('y', 0)})")
        elif event_type == 'mouse_double_click':
            events_listbox.insert(tk.END, f"{i+1}. 双击 ({event.get('x', 0)}, {event.get('y', 0)})")
        elif event_type == 'mouse_drag':
            events_listbox.insert(tk.END, f"{i+1}. 拖动 ({event.get('start_x', 0)}, {event.get('start_y', 0)}) -> ({event.get('end_x', 0)}, {event.get('end_y', 0)})")
        elif event_type == 'key_press':
            events_listbox.insert(tk.END, f"{i+1}. 按键 {event.get('key', '')}")
        else:
            events_listbox.insert(tk.END, f"{i+1}. {event_type}")
    
    btn_frame = ttk.Frame(edit_window)
    btn_frame.pack(pady=10)
    
    def delete_selected():
        sel = events_listbox.curselection()
        if sel:
            idx = sel[0]
            events.pop(idx)
            events_listbox.delete(idx)
    
    def move_up():
        sel = events_listbox.curselection()
        if sel and sel[0] > 0:
            idx = sel[0]
            events[idx], events[idx-1] = events[idx-1], events[idx]
            events_listbox.delete(idx)
            events_listbox.insert(idx-1, f"{idx}. {events[idx-1].get('type', 'unknown')}")
            events_listbox.selection_set(idx-1)
    
    def move_down():
        sel = events_listbox.curselection()
        if sel and sel[0] < len(events) - 1:
            idx = sel[0]
            events[idx], events[idx+1] = events[idx+1], events[idx]
            events_listbox.delete(idx)
            events_listbox.insert(idx+1, f"{idx+2}. {events[idx+1].get('type', 'unknown')}")
            events_listbox.selection_set(idx+1)
    
    ttk.Button(btn_frame, text='删除选中', command=delete_selected).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='上移', command=move_up).pack(side=tk.LEFT, padx=5)
    ttk.Button(btn_frame, text='下移', command=move_down).pack(side=tk.LEFT, padx=5)
    
    def save_changes():
        new_name = name_entry.get().strip()
        record['events'] = events
        record['name'] = new_name
        
        if new_name != record_name:
            old_file = record_file
            record_file = os.path.join(self.config.projects_directory, 'records', f'{new_name}.json')
            if os.path.exists(old_file):
                os.remove(old_file)
        
        with open(record_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        
        self.load_records()
        edit_window.destroy()
        print(f"记录已更新: {new_name}")
    
    ttk.Button(edit_window, text='保存', command=save_changes).pack(pady=10)


def delete_record(self):
    """删除录制记录"""
    selection = self.record_list.curselection()
    if not selection:
        msg_warning(self, '警告', '请先选择一个记录')
        return
    
    if msg_question(self, '确认', '确定要删除选中的记录吗?'):
        record_name = self.record_list.get(selection[0])
        record_file = os.path.join(self.config.projects_directory, 'records', f'{record_name}.json')
        
        if os.path.exists(record_file):
            os.remove(record_file)
            self.load_records()
            print(f"记录已删除: {record_name}")


def clear_screenshot_display(self):
    """清除截图显示"""
    if hasattr(self, 'tools_screenshot_label'):
        self.tools_screenshot_label.config(image='', text='暂无截图')


def test_mouse_click(self):
    """测试鼠标点击功能"""
    print("测试鼠标点击功能...")
    try:
        # 获取当前鼠标位置
        x, y = pyautogui.position()
        print(f"当前鼠标位置: ({x}, {y})")
        
        # 执行测试点击
        self.execution_engine.click(x, y)
        
        msg_information(self, '成功', f'测试点击成功\n坐标: ({x}, {y})')
    except Exception as e:
        msg_critical(self, '错误', f'测试点击失败: {e}')


# 需要导入simpledialog
from tkinter import simpledialog


# ==================== 日常任务处理函数 ====================

def on_daily_tasks_main_switch_changed(self):
    """日常任务总开关变化"""
    self.save_daily_tasks_global_settings()


def on_loop_all_changed(self):
    """日常任务循环执行开关变化"""
    self.save_daily_tasks_global_settings()


def on_global_repeat_count_changed(self):
    """日常任务执行遍数变化"""
    self.save_daily_tasks_global_settings()


def on_global_time_mode_changed(self):
    """日常任务时间模式变化"""
    self.save_daily_tasks_global_settings()


def save_daily_tasks_global_settings(self):
    """保存日常任务全局设置"""
    try:
        # 保存总开关状态
        if hasattr(self, 'daily_tasks_main_switch_var'):
            self.config.daily_tasks_main_switch_enabled = self.daily_tasks_main_switch_var.get()
        
        # 保存循环执行状态
        if hasattr(self, 'daily_loop_all_var'):
            self.config.daily_tasks_loop_enabled = self.daily_loop_all_var.get()
        
        # 保存执行遍数
        if hasattr(self, 'daily_repeat_count_var'):
            self.config.daily_tasks_repeat_count = self.daily_repeat_count_var.get()
        
        # 保存时间模式
        if hasattr(self, 'daily_time_mode_var'):
            self.config.daily_tasks_time_mode = self.daily_time_mode_var.get()
        
        self.config.save()
        
    except Exception as e:
        print(f"保存日常任务全局设置失败: {e}")


def add_daily_task(self):
    """添加日常任务"""
    try:
        if not hasattr(self, 'workflow_manager'):
            msg_warning(self, "警告", "工作流管理器未初始化")
            return
        
        workflows = self.workflow_manager.get_all_workflows()
        if not workflows:
            msg_warning(self, "警告", "没有可用的工作流,请先创建工作流")
            return
        
        from tabs import DailyTaskEditDialog
        dialog = DailyTaskEditDialog(workflows=workflows, parent=self)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            if not hasattr(self, 'daily_tasks'):
                self.daily_tasks = []
            
            # 生成唯一ID
            task_id = f"daily_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.daily_tasks)}"
            dialog.result['id'] = task_id
            dialog.result['status'] = '待执行'
            
            self.daily_tasks.append(dialog.result)
            self.save_daily_tasks()
            self.load_daily_tasks_list()
            
            workflow_text = dialog.result.get('workflow', '未知工作流')
            self.add_status_message(f"添加日常任务: {workflow_text}")
            
    except Exception as e:
        print(f"添加日常任务失败: {e}")
        import traceback
        traceback.print_exc()
        msg_critical(self, "错误", f"添加日常任务失败: {e}")


def edit_daily_task(self):
    """编辑日常任务"""
    try:
        selection = self.daily_task_table.selection()
        if not selection:
            msg_warning(self, "警告", "请先选择一个任务")
            return
        
        item = selection[0]
        index = self.daily_task_table.index(item)
        
        if not hasattr(self, 'daily_tasks') or index >= len(self.daily_tasks):
            return
        
        task = self.daily_tasks[index]
        workflows = self.workflow_manager.get_all_workflows() if hasattr(self, 'workflow_manager') else []
        
        from tabs import DailyTaskEditDialog
        dialog = DailyTaskEditDialog(task=task, workflows=workflows, parent=self)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            # 保留原有ID
            dialog.result['id'] = task.get('id')
            self.daily_tasks[index] = dialog.result
            self.save_daily_tasks()
            self.load_daily_tasks_list()
            
            workflow_text = dialog.result.get('workflow', '未知工作流')
            self.add_status_message(f"编辑日常任务: {workflow_text}")
            
    except Exception as e:
        print(f"编辑日常任务失败: {e}")
        msg_critical(self, "错误", f"编辑日常任务失败: {e}")


def delete_daily_task(self):
    """删除日常任务"""
    try:
        selection = self.daily_task_table.selection()
        if not selection:
            msg_warning(self, "警告", "请先选择一个任务")
            return
        
        if msg_question(self, "确认删除", "确定要删除选中的日常任务吗?"):
            item = selection[0]
            index = self.daily_task_table.index(item)
            
            if hasattr(self, 'daily_tasks') and index < len(self.daily_tasks):
                task = self.daily_tasks.pop(index)
                self.save_daily_tasks()
                self.load_daily_tasks_list()
                self.add_status_message(f"删除日常任务: {task.get('workflow', '未知')}")
                
    except Exception as e:
        print(f"删除日常任务失败: {e}")
        msg_critical(self, "错误", f"删除日常任务失败: {e}")


def move_daily_task_up(self):
    """日常任务上移"""
    try:
        selection = self.daily_task_table.selection()
        if not selection:
            return
        
        item = selection[0]
        row = self.daily_task_table.index(item)
        
        if row > 0 and hasattr(self, 'daily_tasks'):
            self.daily_tasks[row], self.daily_tasks[row-1] = \
                self.daily_tasks[row-1], self.daily_tasks[row]
            self.save_daily_tasks()
            self.load_daily_tasks_list()
            
    except Exception as e:
        print(f"日常任务上移失败: {e}")


def move_daily_task_down(self):
    """日常任务下移"""
    try:
        selection = self.daily_task_table.selection()
        if not selection:
            return
        
        item = selection[0]
        row = self.daily_task_table.index(item)
        
        if hasattr(self, 'daily_tasks') and row < len(self.daily_tasks) - 1:
            self.daily_tasks[row], self.daily_tasks[row+1] = \
                self.daily_tasks[row+1], self.daily_tasks[row]
            self.save_daily_tasks()
            self.load_daily_tasks_list()
            
    except Exception as e:
        print(f"日常任务下移失败: {e}")


def execute_daily_tasks_now(self):
    """立即执行日常任务"""
    try:
        if not hasattr(self, 'daily_tasks') or not self.daily_tasks:
            msg_warning(self, "警告", "没有可执行的日常任务")
            return
        
        # 检查是否有启用的任务
        enabled_tasks = [t for t in self.daily_tasks if t.get('enabled', True)]
        if not enabled_tasks:
            msg_warning(self, "警告", "没有启用的日常任务")
            return
        
        # 延迟3秒后执行
        self.root.after(3000, self._execute_daily_tasks_sequence)
        
    except Exception as e:
        print(f"执行日常任务失败: {e}")
        import traceback
        traceback.print_exc()
        msg_critical(self, "错误", f"执行日常任务失败: {e}")


def _execute_daily_tasks_sequence(self):
    """执行日常任务序列(内部)"""
    try:
        if not hasattr(self, 'daily_tasks') or not self.daily_tasks:
            return
        
        # 获取启用的任务
        enabled_tasks = [t for t in self.daily_tasks if t.get('enabled', True)]
        if not enabled_tasks:
            self.add_status_message("没有启用的日常任务")
            return
        
        # 设置循环标志
        self.daily_tasks_running = True
        self.add_status_message("日常任务开始执行...")
        
        # 在新线程中执行
        def run_tasks():
            loop_count = 0
            while self.daily_tasks_running:
                loop_count += 1
                if loop_count > 1:
                    self.add_status_message(f"开始第 {loop_count} 轮循环执行...")
                
                # 按顺序执行每个启用的任务
                for i, task in enumerate(enabled_tasks):
                    if not self.daily_tasks_running:
                        break
                        
                    workflow_name = task.get('workflow', '')
                    repeat = task.get('repeat_count', 1)
                    
                    # 更新状态为"正在执行"
                    task['status'] = '正在执行'
                    self.root.after(0, self.load_daily_tasks_list)
                    
                    self.add_status_message(f"【日常任务】正在执行 {i+1}/{len(enabled_tasks)}: {workflow_name}")
                    
                    # 执行工作流
                    for r in range(repeat):
                        if not self.daily_tasks_running:
                            break
                        
                        if hasattr(self, 'task_manager'):
                            self.task_manager._execute_workflow(
                                workflow_name,
                                stop_check_fn=lambda: not self.daily_tasks_running
                            )
                    
                    # 执行完毕后更新状态为"待执行"
                    task['status'] = '待执行'
                    self.root.after(0, self.load_daily_tasks_list)
                    task['last_executed'] = datetime.now().isoformat()
                    
                    self.add_status_message(f"【日常任务】已完成: {workflow_name}")
                
                # 保存任务状态
                self.save_daily_tasks()
                
                # 检查是否需要循环
                if not hasattr(self, 'daily_loop_all_var') or not self.daily_loop_all_var.get():
                    break
            
            # 停止后重置所有任务状态
            for task in enabled_tasks:
                task['status'] = '待执行'
            self.root.after(0, self.load_daily_tasks_list)
            self.save_daily_tasks()
            
            self.add_status_message("日常任务执行完成")
        
        thread = threading.Thread(target=run_tasks, daemon=True)
        thread.start()
        
    except Exception as e:
        print(f"执行日常任务序列失败: {e}")
        import traceback
        traceback.print_exc()
        self.add_status_message(f"执行日常任务失败: {e}")


def stop_all_daily_tasks(self):
    """停止所有日常任务"""
    try:
        self.daily_tasks_running = False
        self.add_status_message("日常任务已停止")
    except Exception as e:
        print(f"停止日常任务失败: {e}")


def save_daily_tasks(self):
    """保存日常任务"""
    try:
        if hasattr(self, 'daily_tasks'):
            tasks_file = os.path.join(self.config.projects_directory, 'daily_tasks.json')
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.daily_tasks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存日常任务失败: {e}")


def load_daily_tasks_list(self):
    """加载日常任务列表显示"""
    try:
        # 清空表格
        for item in self.daily_task_table.get_children():
            self.daily_task_table.delete(item)
        
        # 尝试从文件加载
        tasks_file = os.path.join(self.config.projects_directory, 'daily_tasks.json')
        if os.path.exists(tasks_file):
            with open(tasks_file, 'r', encoding='utf-8') as f:
                self.daily_tasks = json.load(f)
        elif not hasattr(self, 'daily_tasks'):
            self.daily_tasks = []
        
        for task in self.daily_tasks:
            enabled = '是' if task.get('enabled', True) else '否'
            workflow = task.get('workflow', '未知工作流')
            repeat_count = task.get('repeat_count', 1)
            status = task.get('status', '待执行')
            
            self.daily_task_table.insert('', tk.END, values=(enabled, workflow, repeat_count, status))
            
    except Exception as e:
        print(f"加载日常任务列表失败: {e}")


# ==================== 答题任务处理函数 ====================

def on_answer_tasks_main_switch_changed(self):
    """答题任务总开关变化"""
    self.save_answer_tasks_global_settings()


def on_answer_loop_all_changed(self):
    """答题任务循环执行开关变化"""
    self.save_answer_tasks_global_settings()


def on_answer_repeat_count_changed(self):
    """答题任务执行遍数变化"""
    self.save_answer_tasks_global_settings()


def on_answer_time_mode_changed(self):
    """答题任务时间模式变化"""
    self.save_answer_tasks_global_settings()


def save_answer_tasks_global_settings(self):
    """保存答题任务全局设置"""
    try:
        # 保存总开关状态
        if hasattr(self, 'answer_tasks_main_switch_var'):
            self.config.answer_tasks_main_switch_enabled = self.answer_tasks_main_switch_var.get()
        
        # 保存循环执行状态
        if hasattr(self, 'answer_loop_all_var'):
            self.config.answer_tasks_loop_enabled = self.answer_loop_all_var.get()
        
        # 保存执行遍数
        if hasattr(self, 'answer_repeat_count_var'):
            self.config.answer_tasks_repeat_count = self.answer_repeat_count_var.get()
        
        # 保存时间模式
        if hasattr(self, 'answer_time_mode_var'):
            self.config.answer_tasks_time_mode = self.answer_time_mode_var.get()
        
        self.config.save()
        
    except Exception as e:
        print(f"保存答题任务全局设置失败: {e}")


def add_answer_task(self):
    """添加答题任务"""
    try:
        if not hasattr(self, 'workflow_manager'):
            msg_warning(self, "警告", "工作流管理器未初始化")
            return
        
        workflows = self.workflow_manager.get_all_workflows()
        if not workflows:
            msg_warning(self, "警告", "没有可用的工作流,请先创建工作流")
            return
        
        from tabs import AnswerTaskEditDialog
        dialog = AnswerTaskEditDialog(workflows=workflows, parent=self)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            if not hasattr(self, 'answer_tasks'):
                self.answer_tasks = []
            
            # 生成唯一ID
            task_id = f"answer_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.answer_tasks)}"
            dialog.result['id'] = task_id
            dialog.result['status'] = '待执行'
            
            self.answer_tasks.append(dialog.result)
            self.save_answer_tasks()
            self.load_answer_tasks_list()
            
            workflow_text = dialog.result.get('workflow', '未知工作流')
            self.add_status_message(f"添加答题任务: {workflow_text}")
            
    except Exception as e:
        print(f"添加答题任务失败: {e}")
        import traceback
        traceback.print_exc()
        msg_critical(self, "错误", f"添加答题任务失败: {e}")


def edit_answer_task(self):
    """编辑答题任务"""
    try:
        selection = self.answer_task_table.selection()
        if not selection:
            msg_warning(self, "警告", "请先选择一个任务")
            return
        
        item = selection[0]
        index = self.answer_task_table.index(item)
        
        if not hasattr(self, 'answer_tasks') or index >= len(self.answer_tasks):
            return
        
        task = self.answer_tasks[index]
        workflows = self.workflow_manager.get_all_workflows() if hasattr(self, 'workflow_manager') else []
        
        from tabs import AnswerTaskEditDialog
        dialog = AnswerTaskEditDialog(task=task, workflows=workflows, parent=self)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            # 保留原有ID
            dialog.result['id'] = task.get('id')
            self.answer_tasks[index] = dialog.result
            self.save_answer_tasks()
            self.load_answer_tasks_list()
            
            workflow_text = dialog.result.get('workflow', '未知工作流')
            self.add_status_message(f"编辑答题任务: {workflow_text}")
            
    except Exception as e:
        print(f"编辑答题任务失败: {e}")
        msg_critical(self, "错误", f"编辑答题任务失败: {e}")


def delete_answer_task(self):
    """删除答题任务"""
    try:
        selection = self.answer_task_table.selection()
        if not selection:
            msg_warning(self, "警告", "请先选择一个任务")
            return
        
        if msg_question(self, "确认删除", "确定要删除选中的答题任务吗?"):
            item = selection[0]
            index = self.answer_task_table.index(item)
            
            if hasattr(self, 'answer_tasks') and index < len(self.answer_tasks):
                task = self.answer_tasks.pop(index)
                self.save_answer_tasks()
                self.load_answer_tasks_list()
                self.add_status_message(f"删除答题任务: {task.get('workflow', '未知')}")
                
    except Exception as e:
        print(f"删除答题任务失败: {e}")
        msg_critical(self, "错误", f"删除答题任务失败: {e}")


def move_answer_task_up(self):
    """答题任务上移"""
    try:
        selection = self.answer_task_table.selection()
        if not selection:
            return
        
        item = selection[0]
        row = self.answer_task_table.index(item)
        
        if row > 0 and hasattr(self, 'answer_tasks'):
            self.answer_tasks[row], self.answer_tasks[row-1] = \
                self.answer_tasks[row-1], self.answer_tasks[row]
            self.save_answer_tasks()
            self.load_answer_tasks_list()
            
    except Exception as e:
        print(f"答题任务上移失败: {e}")


def move_answer_task_down(self):
    """答题任务下移"""
    try:
        selection = self.answer_task_table.selection()
        if not selection:
            return
        
        item = selection[0]
        row = self.answer_task_table.index(item)
        
        if hasattr(self, 'answer_tasks') and row < len(self.answer_tasks) - 1:
            self.answer_tasks[row], self.answer_tasks[row+1] = \
                self.answer_tasks[row+1], self.answer_tasks[row]
            self.save_answer_tasks()
            self.load_answer_tasks_list()
            
    except Exception as e:
        print(f"答题任务下移失败: {e}")


def execute_answer_tasks_now(self):
    """立即执行答题任务"""
    try:
        if not hasattr(self, 'answer_tasks') or not self.answer_tasks:
            msg_warning(self, "警告", "没有可执行的答题任务")
            return
        
        # 检查是否有启用的任务
        enabled_tasks = [t for t in self.answer_tasks if t.get('enabled', True)]
        if not enabled_tasks:
            msg_warning(self, "警告", "没有启用的答题任务")
            return
        
        # 延迟3秒后执行
        self.root.after(3000, self._execute_answer_tasks_sequence)
        
    except Exception as e:
        print(f"执行答题任务失败: {e}")
        import traceback
        traceback.print_exc()
        msg_critical(self, "错误", f"执行答题任务失败: {e}")


def _execute_answer_tasks_sequence(self):
    """执行答题任务序列(内部)"""
    try:
        if not hasattr(self, 'answer_tasks') or not self.answer_tasks:
            return
        
        # 获取启用的任务
        enabled_tasks = [t for t in self.answer_tasks if t.get('enabled', True)]
        if not enabled_tasks:
            self.add_status_message("没有启用的答题任务")
            return
        
        # 设置循环标志
        self.answer_tasks_running = True
        self.add_status_message("答题任务开始执行...")
        
        # 在新线程中执行
        def run_tasks():
            loop_count = 0
            while self.answer_tasks_running:
                loop_count += 1
                if loop_count > 1:
                    self.add_status_message(f"开始第 {loop_count} 轮循环执行...")
                
                # 按顺序执行每个启用的任务
                for i, task in enumerate(enabled_tasks):
                    if not self.answer_tasks_running:
                        break
                        
                    workflow_name = task.get('workflow', '')
                    repeat = task.get('repeat_count', 1)
                    
                    # 更新状态为"正在执行"
                    task['status'] = '正在执行'
                    self.root.after(0, self.load_answer_tasks_list)
                    
                    self.add_status_message(f"【答题任务】正在执行 {i+1}/{len(enabled_tasks)}: {workflow_name}")
                    
                    # 执行工作流
                    for r in range(repeat):
                        if not self.answer_tasks_running:
                            break
                        
                        if hasattr(self, 'task_manager'):
                            self.task_manager._execute_workflow(
                                workflow_name,
                                stop_check_fn=lambda: not self.answer_tasks_running
                            )
                    
                    # 执行完毕后更新状态为"待执行"
                    task['status'] = '待执行'
                    self.root.after(0, self.load_answer_tasks_list)
                    task['last_executed'] = datetime.now().isoformat()
                    
                    self.add_status_message(f"【答题任务】已完成: {workflow_name}")
                
                # 保存任务状态
                self.save_answer_tasks()
                
                # 检查是否需要循环
                if not hasattr(self, 'answer_loop_all_var') or not self.answer_loop_all_var.get():
                    break
            
            # 停止后重置所有任务状态
            for task in enabled_tasks:
                task['status'] = '待执行'
            self.root.after(0, self.load_answer_tasks_list)
            self.save_answer_tasks()
            
            self.add_status_message("答题任务执行完成")
        
        thread = threading.Thread(target=run_tasks, daemon=True)
        thread.start()
        
    except Exception as e:
        print(f"执行答题任务序列失败: {e}")
        import traceback
        traceback.print_exc()
        self.add_status_message(f"执行答题任务失败: {e}")


def stop_all_answer_tasks(self):
    """停止所有答题任务"""
    try:
        self.answer_tasks_running = False
        self.add_status_message("答题任务已停止")
    except Exception as e:
        print(f"停止答题任务失败: {e}")


def save_answer_tasks(self):
    """保存答题任务"""
    try:
        if hasattr(self, 'answer_tasks'):
            tasks_file = os.path.join(self.config.projects_directory, 'answer_tasks.json')
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.answer_tasks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存答题任务失败: {e}")


def load_answer_tasks_list(self):
    """加载答题任务列表显示"""
    try:
        # 清空表格
        for item in self.answer_task_table.get_children():
            self.answer_task_table.delete(item)
        
        # 尝试从文件加载
        tasks_file = os.path.join(self.config.projects_directory, 'answer_tasks.json')
        if os.path.exists(tasks_file):
            with open(tasks_file, 'r', encoding='utf-8') as f:
                self.answer_tasks = json.load(f)
        elif not hasattr(self, 'answer_tasks'):
            self.answer_tasks = []
        
        for task in self.answer_tasks:
            enabled = '是' if task.get('enabled', True) else '否'
            workflow = task.get('workflow', '未知工作流')
            repeat_count = task.get('repeat_count', 1)
            status = task.get('status', '待执行')
            
            self.answer_task_table.insert('', tk.END, values=(enabled, workflow, repeat_count, status))
            
    except Exception as e:
        print(f"加载答题任务列表失败: {e}")


# ==================== 日常任务其他方法 ====================

def toggle_daily_task_pause(self):
    """暂停/继续日常任务"""
    pass


def save_daily_tasks_to_file(self):
    """保存日常任务到文件"""
    try:
        if not hasattr(self, 'daily_tasks'):
            msg_warning(self, "警告", "没有可保存的日常任务")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON文件', '*.json')],
            parent=self.root
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.daily_tasks, f, ensure_ascii=False, indent=2)
            msg_information(self, "成功", "日常任务列表保存成功")
            
    except Exception as e:
        msg_critical(self, "错误", f"保存日常任务列表失败: {e}")


def load_daily_tasks_from_file(self):
    """从文件加载日常任务"""
    try:
        filename = filedialog.askopenfilename(
            filetypes=[('JSON文件', '*.json')],
            parent=self.root
        )
        if filename:
            with open(filename, 'r', encoding='utf-8') as f:
                self.daily_tasks = json.load(f)
            self.save_daily_tasks()
            self.load_daily_tasks_list()
            msg_information(self, "成功", "日常任务列表加载成功")
            
    except Exception as e:
        msg_critical(self, "错误", f"加载日常任务列表失败: {e}")


def clear_all_daily_tasks(self):
    """清空所有日常任务"""
    try:
        if msg_question(self, "确认清空", "确定要清空所有日常任务吗?"):
            if hasattr(self, 'daily_tasks'):
                self.daily_tasks.clear()
                self.save_daily_tasks()
                self.load_daily_tasks_list()
                msg_information(self, "成功", "日常任务已清空")
                
    except Exception as e:
        msg_critical(self, "错误", f"清空日常任务失败: {e}")


def on_daily_task_item_changed(self, item):
    """日常任务项复选框变化处理"""
    pass


def on_global_schedule_time_changed(self, datetime):
    """日常任务定时执行时间变化"""
    self.save_daily_tasks_global_settings()


def on_global_delay_minutes_changed(self):
    """日常任务延时执行分钟数变化"""
    self.save_daily_tasks_global_settings()


def load_daily_tasks_global_settings(self):
    """加载日常任务全局设置"""
    try:
        # 加载总开关
        if hasattr(self, 'daily_tasks_main_switch_var'):
            self.daily_tasks_main_switch_var.set(
                getattr(self.config, 'daily_tasks_main_switch_enabled', True)
            )
        
        # 加载循环执行
        if hasattr(self, 'daily_loop_all_var'):
            self.daily_loop_all_var.set(
                getattr(self.config, 'daily_tasks_loop_enabled', False)
            )
        
        # 加载执行遍数
        if hasattr(self, 'daily_repeat_count_var'):
            self.daily_repeat_count_var.set(
                getattr(self.config, 'daily_tasks_repeat_count', 1)
            )
        
        # 加载时间模式
        if hasattr(self, 'daily_time_mode_var'):
            time_mode = getattr(self.config, 'daily_tasks_time_mode', 'none')
            self.daily_time_mode_var.set(time_mode)
        
    except Exception as e:
        print(f"加载日常任务全局设置失败: {e}")


# ==================== 答题任务其他方法 ====================

def save_answer_tasks_to_file(self):
    """保存答题任务到文件"""
    try:
        if not hasattr(self, 'answer_tasks'):
            msg_warning(self, "警告", "没有可保存的答题任务")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON文件', '*.json')],
            parent=self.root
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.answer_tasks, f, ensure_ascii=False, indent=2)
            msg_information(self, "成功", "答题任务列表保存成功")
            
    except Exception as e:
        msg_critical(self, "错误", f"保存答题任务列表失败: {e}")


def load_answer_tasks_from_file(self):
    """从文件加载答题任务"""
    try:
        filename = filedialog.askopenfilename(
            filetypes=[('JSON文件', '*.json')],
            parent=self.root
        )
        if filename:
            with open(filename, 'r', encoding='utf-8') as f:
                self.answer_tasks = json.load(f)
            self.save_answer_tasks()
            self.load_answer_tasks_list()
            msg_information(self, "成功", "答题任务列表加载成功")
            
    except Exception as e:
        msg_critical(self, "错误", f"加载答题任务列表失败: {e}")


def clear_all_answer_tasks(self):
    """清空所有答题任务"""
    try:
        if msg_question(self, "确认清空", "确定要清空所有答题任务吗?"):
            if hasattr(self, 'answer_tasks'):
                self.answer_tasks.clear()
                self.save_answer_tasks()
                self.load_answer_tasks_list()
                msg_information(self, "成功", "答题任务已清空")
                
    except Exception as e:
        msg_critical(self, "错误", f"清空答题任务失败: {e}")


def on_answer_task_item_changed(self, item):
    """答题任务项复选框变化处理"""
    pass


def on_answer_schedule_time_changed(self, datetime):
    """答题任务定时执行时间变化"""
    self.save_answer_tasks_global_settings()


def on_answer_delay_minutes_changed(self):
    """答题任务延时执行分钟数变化"""
    self.save_answer_tasks_global_settings()


def load_answer_tasks_global_settings(self):
    """加载答题任务全局设置"""
    try:
        # 加载总开关
        if hasattr(self, 'answer_tasks_main_switch_var'):
            self.answer_tasks_main_switch_var.set(
                getattr(self.config, 'answer_tasks_main_switch_enabled', True)
            )
        
        # 加载循环执行
        if hasattr(self, 'answer_loop_all_var'):
            self.answer_loop_all_var.set(
                getattr(self.config, 'answer_tasks_loop_enabled', False)
            )
        
        # 加载执行遍数
        if hasattr(self, 'answer_repeat_count_var'):
            self.answer_repeat_count_var.set(
                getattr(self.config, 'answer_tasks_repeat_count', 1)
            )
        
        # 加载时间模式
        if hasattr(self, 'answer_time_mode_var'):
            time_mode = getattr(self.config, 'answer_tasks_time_mode', 'none')
            self.answer_time_mode_var.set(time_mode)
        
    except Exception as e:
        print(f"加载答题任务全局设置失败: {e}")


# ==================== 项目管理函数 ====================

def create_project(self):
    """创建项目"""
    try:
        dialog = tk.Toplevel(self.root)
        dialog.title('创建项目')
        dialog.geometry('500x400')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 项目名称
        ttk.Label(dialog, text='项目名称:').pack(pady=5)
        name_entry = ttk.Entry(dialog, width=40)
        name_entry.pack(pady=5)
        
        # 项目路径
        ttk.Label(dialog, text='项目路径:').pack(pady=5)
        path_frame = ttk.Frame(dialog)
        path_frame.pack(pady=5, fill=tk.X, padx=20)
        
        path_entry = ttk.Entry(path_frame, width=40)
        path_entry.pack(side=tk.LEFT, padx=5)
        
        def browse():
            from tkinter import filedialog
            path = filedialog.askdirectory(parent=dialog)
            if path:
                path_entry.delete(0, tk.END)
                path_entry.insert(0, path)
        
        ttk.Button(path_frame, text='浏览', command=browse).pack(side=tk.LEFT)
        
        def ok():
            name = name_entry.get().strip()
            path = path_entry.get().strip()
            
            if not name:
                messagebox.showwarning('警告', '请输入项目名称', parent=dialog)
                return
            
            if not path:
                messagebox.showwarning('警告', '请选择项目路径', parent=dialog)
                return
            
            # 创建项目
            project_path = os.path.join(path, name)
            os.makedirs(project_path, exist_ok=True)
            
            # 创建默认文件夹
            os.makedirs(os.path.join(project_path, 'workflows'), exist_ok=True)
            os.makedirs(os.path.join(project_path, 'keywords'), exist_ok=True)
            os.makedirs(os.path.join(project_path, 'screenshots'), exist_ok=True)
            
            # 保存项目配置
            project_config = {
                'name': name,
                'path': project_path,
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            with open(os.path.join(project_path, 'project.json'), 'w', encoding='utf-8') as f:
                json.dump(project_config, f, ensure_ascii=False, indent=2)
            
            dialog.destroy()
            self.load_projects()
            msg_information(self, '成功', f'项目创建成功: {name}')
        
        ttk.Button(dialog, text='确定', command=ok).pack(pady=20)
        
    except Exception as e:
        msg_critical(self, "错误", f"创建项目失败: {e}")


def _browse_project_path(self):
    """浏览项目路径"""
    pass


def switch_project_by_name(self, project_name, clear_tasks=True):
    """通过名称切换项目"""
    try:
        if hasattr(self, 'project_manager'):
            self.project_manager.switch_project(project_name)
            self.config.current_project = project_name
            self.config.save()
            self.load_projects()
            if clear_tasks:
                self._clear_all_task_lists()
            self.add_status_message(f"已切换到项目: {project_name}")
    except Exception as e:
        print(f"切换项目失败: {e}")


def switch_project(self):
    """切换项目"""
    try:
        selection = self.project_list.curselection()
        if not selection:
            msg_warning(self, "警告", "请先选择一个项目")
            return
        
        project_name = self.project_list.get(selection[0])
        self.switch_project_by_name(project_name)
        
    except Exception as e:
        msg_critical(self, "错误", f"切换项目失败: {e}")


def pack_project(self):
    """打包项目"""
    try:
        selection = self.project_list.curselection()
        if not selection:
            msg_warning(self, "警告", "请先选择一个项目")
            return
        
        project_name = self.project_list.get(selection[0])
        
        # 选择保存位置
        filename = filedialog.asksaveasfilename(
            defaultextension='.zip',
            filetypes=[('ZIP文件', '*.zip')],
            parent=self.root
        )
        
        if filename:
            project_path = os.path.join(self.config.projects_directory, project_name)
            
            # 创建ZIP文件
            import zipfile
            with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(project_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, project_path)
                        zipf.write(file_path, arcname)
            
            msg_information(self, "成功", f"项目打包成功: {filename}")
            
    except Exception as e:
        msg_critical(self, "错误", f"打包项目失败: {e}")


def unpack_project(self):
    """解包项目"""
    try:
        filename = filedialog.askopenfilename(
            filetypes=[('ZIP文件', '*.zip')],
            parent=self.root
        )
        
        if filename:
            project_name = os.path.splitext(os.path.basename(filename))[0]
            project_path = os.path.join(self.config.projects_directory, project_name)
            
            # 解压ZIP文件
            import zipfile
            with zipfile.ZipFile(filename, 'r') as zipf:
                zipf.extractall(project_path)
            
            self.load_projects()
            msg_information(self, "成功", f"项目解包成功: {project_name}")
            
    except Exception as e:
        msg_critical(self, "错误", f"解包项目失败: {e}")


def load_projects(self):
    """加载项目列表"""
    try:
        # 清空列表
        self.project_list.delete(0, tk.END)
        
        # 扫描项目目录
        if os.path.exists(self.config.projects_directory):
            for item in os.listdir(self.config.projects_directory):
                project_path = os.path.join(self.config.projects_directory, item)
                if os.path.isdir(project_path) and os.path.exists(os.path.join(project_path, 'project.json')):
                    self.project_list.insert(tk.END, item)
        
        # 更新当前项目显示
        if hasattr(self, 'current_project_name_label'):
            current_project = self.project_manager.get_current_project() if hasattr(self, 'project_manager') else ''
            self.current_project_name_label.config(text=current_project)
            # 自动填充当前项目的详细信息
            if current_project and hasattr(self, 'project_manager'):
                project_data = self.project_manager.projects
                proj = next((p for p in project_data if p.get('name') == current_project), None)
                if proj:
                    if hasattr(self, 'current_project_path_label'):
                        self.current_project_path_label.config(text=proj.get('path', ''))
                    if hasattr(self, 'current_project_version_edit'):
                        self.current_project_version_edit.delete(0, tk.END)
                        self.current_project_version_edit.insert(0, proj.get('version', ''))
                    if hasattr(self, 'current_project_created_edit'):
                        self.current_project_created_edit.delete(0, tk.END)
                        self.current_project_created_edit.insert(0, proj.get('created_at', ''))
                    if hasattr(self, 'current_project_program_edit'):
                        self.current_project_program_edit.delete(0, tk.END)
                        self.current_project_program_edit.insert(0, proj.get('program', ''))
                    if hasattr(self, 'current_project_resolution_combo'):
                        self.current_project_resolution_combo.set(proj.get('resolution', ''))
                    if hasattr(self, 'current_project_resolution_custom'):
                        self.current_project_resolution_custom.delete(0, tk.END)
                    if hasattr(self, 'current_project_notes_edit'):
                        self.current_project_notes_edit.config(state='normal')
                        self.current_project_notes_edit.delete('1.0', tk.END)
                        self.current_project_notes_edit.insert('1.0', proj.get('notes', ''))
                        self.current_project_notes_edit.config(state='disabled')
            
    except Exception as e:
        print(f"加载项目列表失败: {e}")


def edit_current_project(self):
    """编辑当前项目"""
    try:
        # 启用编辑
        self.current_project_version_edit.config(state='normal')
        self.current_project_created_edit.config(state='normal')
        self.current_project_program_edit.config(state='normal')
        self.current_project_resolution_combo.config(state='readonly')
        self.current_project_resolution_custom.config(state='normal')
        self.current_project_notes_edit.config(state='normal')
        
        self.edit_project_button.config(state=tk.DISABLED)
        self.save_project_button.config(state=tk.NORMAL)
        
    except Exception as e:
        print(f"编辑当前项目失败: {e}")


def save_current_project(self):
    """保存当前项目"""
    try:
        # 禁用编辑
        self.current_project_version_edit.config(state='disabled')
        self.current_project_created_edit.config(state='disabled')
        self.current_project_program_edit.config(state='disabled')
        self.current_project_resolution_combo.config(state='disabled')
        self.current_project_resolution_custom.config(state='disabled')
        self.current_project_notes_edit.config(state='disabled')
        
        self.edit_project_button.config(state=tk.NORMAL)
        self.save_project_button.config(state=tk.DISABLED)
        
        msg_information(self, "成功", "项目保存成功")
        
    except Exception as e:
        print(f"保存当前项目失败: {e}")


def on_project_selected(self):
    """项目选择事件"""
    try:
        selection = self.project_list.curselection()
        if not selection:
            return
        
        project_name = self.project_list.get(selection[0])
        project_path = os.path.join(self.config.projects_directory, project_name)
        project_config_file = os.path.join(project_path, 'project.json')
        
        if os.path.exists(project_config_file):
            with open(project_config_file, 'r', encoding='utf-8') as f:
                project_config = json.load(f)
            
            # 更新显示
            self.current_project_name_label.config(text=project_config.get('name', ''))
            self.current_project_version_edit.delete(0, tk.END)
            self.current_project_version_edit.insert(0, project_config.get('version', ''))
            self.current_project_path_label.config(text=project_path)
            self.current_project_created_edit.delete(0, tk.END)
            self.current_project_created_edit.insert(0, project_config.get('created_at', ''))
            
    except Exception as e:
        print(f"项目选择事件处理失败: {e}")


def _clear_all_task_lists(self):
    """清空所有任务列表"""
    try:
        if hasattr(self, 'daily_tasks'):
            self.daily_tasks.clear()
        if hasattr(self, 'answer_tasks'):
            self.answer_tasks.clear()
        if hasattr(self, 'discovery_tasks'):
            self.discovery_tasks.clear()
    except Exception as e:
        print(f"清空任务列表失败: {e}")


# ==================== 激活系统处理函数 ====================

def load_activation_config(self):
    """加载激活配置"""
    try:
        config_file = os.path.join(self.config.projects_directory, 'activation.json')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                activation_config = json.load(f)
                # 更新UI显示
                if hasattr(self, 'activation_username_edit'):
                    username = activation_config.get('username', '')
                    self.activation_username_edit.delete(0, tk.END)
                    self.activation_username_edit.insert(0, username)
                if hasattr(self, 'activation_password_edit'):
                    password = activation_config.get('password', '')
                    self.activation_password_edit.delete(0, tk.END)
                    self.activation_password_edit.insert(0, password)
                if hasattr(self, 'save_password_var'):
                    self.save_password_var.set(activation_config.get('save_password', False))
                if hasattr(self, 'activation_expiry_label'):
                    self.activation_expiry_label.config(text=activation_config.get('expire_time', '-'))
                if hasattr(self, 'activation_status_label'):
                    status = activation_config.get('status', '未登录')
                    self.activation_status_label.config(text=status, foreground='green' if status == '已激活' or status.startswith('已登录') else 'red')
    except Exception as e:
        print(f"加载激活配置失败: {e}")


def save_activation_config(self):
    """保存激活配置"""
    try:
        activation_config = {
            'username': self.activation_username_edit.get() if hasattr(self, 'activation_username_edit') else '',
            'password': self.activation_password_edit.get() if hasattr(self, 'activation_password_edit') else '',
            'save_password': self.save_password_var.get() if hasattr(self, 'save_password_var') else False,
            'expire_time': self.activation_expiry_label.cget('text') if hasattr(self, 'activation_expiry_label') else '-',
            'status': self.activation_status_label.cget('text') if hasattr(self, 'activation_status_label') else '未登录'
        }
        config_file = os.path.join(self.config.projects_directory, 'activation.json')
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(activation_config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存激活配置失败: {e}")


def activation_api_post(self, endpoint, data=None):
    """发送POST请求到激活服务端"""
    try:
        server_url = self._get_activation_server_url()
        response = requests.post(f"{server_url}{endpoint}", json=data or {}, timeout=10)
        return response.json()
    except Exception as e:
        print(f"激活API请求失败: {e}")
        return {'success': False, 'message': f'网络错误: {str(e)}'}


def activation_api_get(self, endpoint):
    """发送GET请求到激活服务端"""
    try:
        server_url = self._get_activation_server_url()
        response = requests.get(f"{server_url}{endpoint}", timeout=10)
        return response
    except Exception as e:
        print(f"激活API请求失败: {e}")
        return None


def auto_activation_login(self):
    """自动登录（程序启动时）"""
    username = self.activation_username_edit.get().strip()
    password = self.activation_password_edit.get().strip()
    save_password = self.save_password_var.get()

    if not username or not password:
        # 没有保存的用户名和密码，锁定功能标签页
        self._lock_functional_tabs()
        self.update_activation_status()
        return

    result = self.activation_api_post('/api/login', {
        'username': username,
        'password': password
    })

    if result.get('success'):
        self.activation_manager = ActivationManager(username)
        self.activation_manager.load_from_local()

        # 从服务端同步激活状态
        self.activation_manager.sync_from_server()

        self.update_activation_status()

        # 显示登录成功
        print("连接服务端成功")
        self.activation_status_label.config(text="已连接服务端", foreground='green')

        # 检查是否可以开始试用
        if not self.activation_manager.is_activated():
            # 检查是否可以试用
            if self.activation_manager.can_use_daily_trial():
                # 可以试用，解锁标签页
                self._unlock_functional_tabs()
                self.trial_session_started = False
                self.daily_trial_active = False
            else:
                # 首次使用或试用已结束，锁定标签页
                self._lock_functional_tabs()
                self.daily_trial_active = False
        else:
            self._unlock_functional_tabs()
    else:
        # 登录失败，锁定功能标签页
        self._lock_functional_tabs()
        self.update_activation_status()
        print("连接服务端失败")

    # 自动恢复工作组状态
    if hasattr(self, '_restore_workgroup_state'):
        self.root.after(500, self._restore_workgroup_state)


def on_activation_login(self):
    """用户登录"""
    username = self.activation_username_edit.get().strip()
    password = self.activation_password_edit.get().strip()

    if len(username) < 6:
        messagebox.showwarning('错误', '用户名至少需要6位', parent=self.root)
        return

    if len(password) < 6:
        messagebox.showwarning('错误', '密码至少需要6位', parent=self.root)
        return

    result = self.activation_api_post('/api/login', {
        'username': username,
        'password': password
    })

    if result.get('success'):
        self.activation_manager = ActivationManager(username)
        self.activation_manager.load_from_local()

        # 从服务端同步激活状态
        self.activation_manager.sync_from_server()

        self.update_activation_status()

        # 保存配置
        self.save_activation_config()

        # 检查是否可以开始试用
        if not self.activation_manager.is_activated():
            # 检查是否是新的一天
            today = datetime.now().strftime('%Y-%m-%d')
            if self.activation_manager.daily_trial_date != today:
                # 新的一天，检查是否可以试用
                if self.activation_manager.can_use_daily_trial():
                    # 可以试用，开始计时
                    self._unlock_functional_tabs()
                    self.trial_session_started = False
                    self.daily_trial_active = False
                else:
                    # 首次使用，今天不能试用
                    self._lock_functional_tabs()
                    self.daily_trial_active = False
            else:
                # 同一天，检查是否还有剩余时间
                if self.activation_manager.can_use_daily_trial():
                    self._unlock_functional_tabs()
                    self.trial_session_started = False
                    self.daily_trial_active = False
                else:
                    # 试用时间已用完
                    self._lock_functional_tabs()
        else:
            self._unlock_functional_tabs()

        # 显示激活状态
        if self.activation_manager.expires_at:
            messagebox.showinfo('成功', f"登录成功！\n\n已连接到服务端\n\n有效期至：{self.activation_manager.expires_at.strftime('%Y-%m-%d %H:%M:%S')}\n剩余天数：{self.activation_manager.days_remaining} 天", parent=self.root)
        else:
            if self.activation_manager.first_run_today:
                messagebox.showinfo('成功', "登录成功！\n\n已连接到服务端\n\n首次使用，今天不能免费试用。\n\n明天开始每天可免费试用1小时。", parent=self.root)
            else:
                messagebox.showinfo('成功', "登录成功！\n\n已连接到服务端\n\n当前未激活，可使用每日1小时免费试用。", parent=self.root)

        # 自动恢复工作组状态
        if hasattr(self, '_restore_workgroup_state'):
            self.root.after(500, self._restore_workgroup_state)
    else:
        messagebox.showerror('错误', result.get('message', '登录失败'), parent=self.root)


def on_activation_register(self):
    """打开注册窗口"""
    dialog = self.ActivationRegisterDialog(self)
    if dialog.result:
        # 注册成功后自动填入用户名和密码
        self.activation_username_edit.delete(0, tk.END)
        self.activation_username_edit.insert(0, dialog.username)
        self.activation_password_edit.delete(0, tk.END)
        self.activation_password_edit.insert(0, dialog.password)
        self.on_activation_login()


def on_activation_logout(self):
    """退出登录"""
    if not getattr(self, 'activation_manager', None):
        messagebox.showinfo('提示', '当前未登录', parent=self.root)
        return

    result = messagebox.askyesno('确认', '确定要退出登录吗？', parent=self.root)
    if not result:
        return

    username = ''
    if hasattr(self, 'activation_username_edit'):
        username = self.activation_username_edit.get().strip()

    if hasattr(self, 'activation_manager'):
        del self.activation_manager
    self.activation_manager = None

    if hasattr(self, 'activation_username_edit'):
        self.activation_username_edit.delete(0, tk.END)
    if hasattr(self, 'activation_password_edit'):
        self.activation_password_edit.delete(0, tk.END)

    if hasattr(self, 'save_password_var'):
        self.save_password_var.set(False)

    if hasattr(self, 'activation_status_label'):
        self.activation_status_label.config(text='未登录', foreground='red')
    if hasattr(self, 'days_remaining_label'):
        self.days_remaining_label.config(text='剩余天数: -')
    if hasattr(self, 'activation_expiry_label'):
        self.activation_expiry_label.config(text='有效期至: -')

    self._lock_functional_tabs()

    if hasattr(self, 'wg_info') and self.wg_info.get('id'):
        self.wg_info = {'id': None, 'name': None, 'role': None, 'sync_dir': None, 'last_sync': None, 'disabled': False}
        self._stop_wg_sync()
        if hasattr(self, 'wg_status_label'):
            self.wg_status_label.config(text='未加入工作组', foreground='gray')
        if hasattr(self, 'wg_member_status_label'):
            self.wg_member_status_label.config(text='未加入工作组', foreground='gray')
        self._update_cmd_status_message('已退出登录，工作组已退出')
        self._save_workgroup_state()

    messagebox.showinfo('成功', '已退出登录', parent=self.root)


def on_activation_purchase(self):
    """购买激活码"""
    dialog = self.ActivationPurchaseDialog(self)


def on_activation_activate(self):
    """激活使用激活码"""
    if not self.activation_manager:
        messagebox.showwarning('错误', '请先登录', parent=self.root)
        return

    # 检查用户是否被禁用
    result = self.activation_api_post('/api/login', {
        'username': self.activation_manager.username,
        'password': self.activation_password_edit.get().strip()
    })

    if not result.get('success'):
        messagebox.showerror('错误', result.get('message', '登录验证失败'), parent=self.root)
        return

    # 打开激活使用对话框
    dialog = self.ActivationCodeDialog(self, self.activation_manager.username)
    self.root.wait_window(dialog.dialog)
    if dialog.result:
        username = dialog.username
        code = dialog.code
        invite_code = dialog.invite_code

        result = self.activation_api_post('/api/activation/activate', {
            'username': username,
            'code': code,
            'invite_code': invite_code.strip() if invite_code else ''
        })

        if result.get('success'):
            data = result.get('data', {})
            expires_at = data.get('expires_at')
            days_remaining = data.get('days_remaining', 0)
            if expires_at:
                self.activation_manager.expires_at = datetime.fromisoformat(expires_at)
                self.activation_manager.days_remaining = days_remaining
                self.activation_manager.save_to_local()
                self.save_activation_config()

            # 解锁功能标签页
            self._unlock_functional_tabs()
            self.update_activation_status()

            messagebox.showinfo('成功', f"激活成功！\n\n有效期至：{expires_at}\n剩余天数：{days_remaining} 天", parent=self.root)
        else:
            messagebox.showerror('错误', result.get('message', '激活失败'), parent=self.root)


def on_activation_sync(self):
    """同步激活状态"""
    if not self.activation_manager:
        messagebox.showwarning('错误', '请先登录', parent=self.root)
        return

    self.activation_manager.sync_from_server()
    self.update_activation_status()

    # 根据同步结果锁定/解锁标签页
    if self.activation_manager.is_activated():
        self._unlock_functional_tabs()
    else:
        self._lock_functional_tabs()

    messagebox.showinfo('成功', '状态已同步', parent=self.root)


def on_activation_auto_sync(self):
    """自动同步激活状态（每24小时）"""
    if self.activation_manager:
        self.activation_manager.sync_from_server()
        self.update_activation_status()
    # 继续设置下一个24小时的定时器
    self.activation_sync_timer_id = self.root.after(86400000, self.on_activation_auto_sync)


def on_activation_ticket(self):
    """报障"""
    if not self.activation_manager:
        messagebox.showwarning('错误', '请先登录', parent=self.root)
        return

    dialog = self.ActivationTicketDialog(self, self.activation_manager.username)


def update_activation_status(self):
    """更新激活状态显示"""
    if not self.activation_manager:
        self.activation_status_label.config(text="未登录", foreground='red')
        if hasattr(self, 'days_remaining_label'):
            self.days_remaining_label.config(text="剩余天数: -")
        self.activation_expiry_label.config(text="有效期至: -")
        # 更新试用状态
        self.trial_status_label.config(text="未登录", foreground='gray')
        self.trial_countdown_label.config(text="剩余时间: --:--:--")
        self.trial_hint_label.config(text="登录后启动每日1小时免费试用")
        return

    if self.activation_manager.is_activated():
        self.activation_status_label.config(text="已激活", foreground='green')
        if hasattr(self, 'days_remaining_label'):
            self.days_remaining_label.config(text=f"剩余天数: {self.activation_manager.days_remaining}")
        # 更新试用状态 - 已激活用户不显示试用
        self.trial_status_label.config(text="已激活，无需试用", foreground='green')
        self.trial_countdown_label.config(text="剩余时间: --:--:--")
        self.trial_hint_label.config(text="您已激活，可无限使用")
        self.tabs_locked = False
    else:
        self.activation_status_label.config(text="未激活", foreground='orange')
        if hasattr(self, 'days_remaining_label'):
            self.days_remaining_label.config(text="剩余天数: 0")
        # 更新试用状态
        self.update_trial_status_display()

    if self.activation_manager.expires_at:
        self.activation_expiry_label.config(text=f"有效期至: {self.activation_manager.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        self.activation_expiry_label.config(text="有效期至: 未激活")

    # 根据激活状态锁定/解锁功能标签页
    if self.activation_manager.is_activated():
        self._unlock_functional_tabs()
    else:
        self._lock_functional_tabs()


def _lock_functional_tabs(self):
    """锁定功能标签页"""
    self.tabs_locked = True
    locked_tabs = {'工作流', '必用', '日常任务', '答题', '发现即点', '指挥'}
    for i in range(self.notebook.index('end')):
        tab_text = self.notebook.tab(i, 'text')
        if tab_text in locked_tabs:
            self.notebook.tab(i, state='disabled')
    # 切换到激活标签
    for i in range(self.notebook.index('end')):
        if self.notebook.tab(i, 'text') == '激活':
            self.notebook.select(i)
            break


def _unlock_functional_tabs(self):
    """解锁功能标签页"""
    self.tabs_locked = False
    locked_tabs = {'工作流', '必用', '日常任务', '答题', '发现即点', '指挥'}
    for i in range(self.notebook.index('end')):
        tab_text = self.notebook.tab(i, 'text')
        if tab_text in locked_tabs:
            self.notebook.tab(i, state='normal')


def switch_to_tab_if_needed(self, tab_name):
    try:
        tab_names = ['工具', '关键词', '工作流', '必用', '项目', '日常任务', '答题', '发现即点', '激活']
        if tab_name in tab_names:
            index = tab_names.index(tab_name)
            self.notebook.select(index)
    except Exception as e:
        print(f"切换标签页失败: {e}")


def update_trial_status_display(self):
    """更新试用状态显示"""
    if not self.activation_manager:
        return

    # 如果是首次使用（今天），显示特殊提示
    if self.activation_manager.first_run_today:
        self.trial_status_label.config(text="首次使用（今日禁用）", foreground='#dc3545')
        self.trial_countdown_label.config(text="剩余时间: 01:00:00")
        self.trial_hint_label.config(text="首次使用，今天不能免费试用，明天开始每天可免费试用1小时")
        return

    if self.activation_manager.can_use_daily_trial():
        remaining = self.activation_manager.daily_trial_remaining_seconds
        if remaining > 0:
            self.trial_status_label.config(text="试用进行中", foreground='#28a745')
            self.trial_countdown_label.config(text=f"剩余时间: {self.activation_manager.get_formatted_trial_time()}")
            self.trial_hint_label.config(text="本次运行剩余试用时间，结束后需激活")
        else:
            self.trial_status_label.config(text="本次试用已结束", foreground='red')
            self.trial_countdown_label.config(text="剩余时间: 00:00:00")
            self.trial_hint_label.config(text="请激活后继续使用")
    else:
        self.trial_status_label.config(text="本次试用已结束", foreground='red')
        self.trial_countdown_label.config(text="剩余时间: 00:00:00")
        self.trial_hint_label.config(text="请激活后继续使用")


def on_daily_trial_tick(self):
    """每日试用倒计时定时器回调 - 从程序启动开始倒计时，1小时后结束"""
    # 如果没有activation_manager，直接返回
    if not self.activation_manager:
        return

    # 如果已激活，不需要倒计时
    if self.activation_manager.is_activated():
        self._unlock_functional_tabs()
        return

    # 检查是否是首次使用（今天）
    if self.activation_manager.first_run_today:
        # 首次使用，锁定功能（只锁定一次）
        if not self.tabs_locked:
            self._lock_functional_tabs()
            self.daily_trial_active = False
            messagebox.showinfo('提示', "首次使用，今天不能免费试用。\n\n明天开始每天可免费试用1小时。", parent=self.root)
        # 更新显示
        self.update_trial_status_display()
        return

    # 检查是否可以使用每日试用
    if not self.activation_manager.can_use_daily_trial():
        # 试用时间已用完，锁定功能
        if not self.tabs_locked:
            self.on_daily_trial_expired()
        return

    # 从程序启动时就开始倒计时
    if not self.trial_session_started:
        self.trial_session_started = True
        self.daily_trial_active = True
        self.activation_manager.start_daily_trial()

    # 扣减时间（5秒扣5秒）
    self.activation_manager.update_daily_trial_time(5)

    # 更新显示
    self.update_trial_status_display()

    # 检查是否时间用完
    if self.activation_manager.daily_trial_remaining_seconds <= 0:
        self.on_daily_trial_expired()

    # 继续设置下一个5秒的定时器
    self.daily_trial_timer_id = self.root.after(5000, self.on_daily_trial_tick)


def on_daily_trial_expired(self):
    """每日试用时间到期处理"""
    self._lock_functional_tabs()
    self.daily_trial_active = False

    # 弹窗提示
    messagebox.showwarning('提示', '本次免费试用时间已结束，请激活后继续使用。', parent=self.root)

    # 锁定功能标签页，切换到激活标签
    # 找到激活标签页的索引并切换
    for i in range(self.notebook.index('end')):
        if self.notebook.tab(i, 'text') == '激活':
            self.notebook.select(i)
            break

    # 更新显示
    self.update_trial_status_display()


def _get_activation_server_url(self):
    """获取激活服务器地址"""
    return "https://9793tg1lo456.vicp.fun"


def set_activation_server_url(self, url):
    """设置激活服务器URL"""
    self.config.activation_server_url = url
    self.config.save()


# ==================== API设置辅助函数 ====================

def _get_api_placeholder(self, api_type):
    """获取API占位符"""
    placeholders = {
        'openai': 'sk-...',
        'claude': 'sk-ant-...',
        'custom': 'your-api-key'
    }
    return placeholders.get(api_type, 'your-api-key')


def _get_model_placeholder(self, api_type):
    """获取模型占位符"""
    placeholders = {
        'openai': 'gpt-4',
        'claude': 'claude-3-sonnet-20240229',
        'custom': 'model-name'
    }
    return placeholders.get(api_type, 'model-name')


def _get_api_suffix(self, api_type):
    """获取API后缀"""
    suffixes = {
        'openai': '/v1/chat/completions',
        'claude': '/v1/messages',
        'custom': ''
    }
    return suffixes.get(api_type, '')


def _get_current_api_config(self):
    """获取当前API配置"""
    return {
        'api_type': getattr(self.config, 'api_type', 'openai'),
        'api_key': getattr(self.config, 'api_key', ''),
        'api_base': getattr(self.config, 'api_base', ''),
        'model': getattr(self.config, 'model', 'gpt-4')
    }


# ==================== AI代码执行函数 ====================

def _parse_pyautogui_code(self, code: str):
    """解析pyautogui代码，转换为actions格式"""
    import re
    
    actions = []
    lines = code.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        
        # 跳过注释和空行
        if not line or line.startswith('#'):
            continue
        
        # 解析 pyautogui.click(x, y)
        click_match = re.search(r'pyautogui\.click\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line)
        if click_match:
            x = int(click_match.group(1))
            y = int(click_match.group(2))
            actions.append({
                'type': 'click',
                'x': x,
                'y': y,
                'param_type': 'fixed',
                'description': f'点击坐标 ({x}, {y})'
            })
            continue
        
        # 解析 pyautogui.doubleClick(x, y)
        double_click_match = re.search(r'pyautogui\.doubleClick\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line)
        if double_click_match:
            x = int(double_click_match.group(1))
            y = int(double_click_match.group(2))
            actions.append({'type': 'click', 'x': x, 'y': y, 'param_type': 'fixed'})
            actions.append({'type': 'click', 'x': x, 'y': y, 'param_type': 'fixed'})
            continue
        
        # 解析 pyautogui.rightClick(x, y)
        right_click_match = re.search(r'pyautogui\.rightClick\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', line)
        if right_click_match:
            x = int(right_click_match.group(1))
            y = int(right_click_match.group(2))
            actions.append({
                'type': 'click',
                'x': x,
                'y': y,
                'param_type': 'fixed',
                'button': 'right',
                'description': f'右键点击 ({x}, {y})'
            })
            continue
        
        # 解析 pyautogui.moveTo(x, y, duration=...)
        move_match = re.search(r'pyautogui\.moveTo\s*\(\s*(\d+)\s*,\s*(\d+)\s*', line)
        if move_match:
            x = int(move_match.group(1))
            y = int(move_match.group(2))
            actions.append({
                'type': 'move',
                'x': x,
                'y': y,
                'param_type': 'fixed',
                'description': f'移动鼠标到 ({x}, {y})'
            })
            continue
        
        # 解析 pyautogui.typewrite(text)
        type_match = re.search(r'pyautogui\.typewrite\s*\(\s*[\'\"](.+)[\'\"]\s*\)', line)
        if type_match:
            text = type_match.group(1)
            actions.append({
                'type': 'type',
                'text': text,
                'param_type': 'fixed',
                'description': f'输入文本: {text}'
            })
            continue
        
        # 解析 pyautogui.press(key)
        press_match = re.search(r'pyautogui\.press\s*\(\s*[\'\"](.+)[\'\"]\s*\)', line)
        if press_match:
            key = press_match.group(1)
            actions.append({
                'type': 'key',
                'key': key,
                'param_type': 'fixed',
                'description': f'按键: {key}'
            })
            continue
        
        # 解析 pyautogui.sleep(seconds)
        sleep_match = re.search(r'pyautogui\.sleep\s*\(\s*(\d+\.?\d*)\s*\)', line)
        if sleep_match:
            sleep_seconds = float(sleep_match.group(1))
            if actions:
                actions[-1]['delay'] = sleep_seconds
            continue
    
    return actions


def _execute_ai_code_workflow(self, code):
    """执行AI生成的代码工作流"""
    try:
        # 解析代码
        actions = self._parse_pyautogui_code(code)
        
        if not actions:
            # 如果无法解析，尝试直接执行
            exec(code, {'__builtins__': __builtins__, 'self': self, 'pyautogui': pyautogui})
            return
        
        # 创建临时工作流
        temp_workflow = {
            'name': 'AI Generated Workflow',
            'actions': actions
        }
        
        # 执行工作流
        if hasattr(self, 'task_manager'):
            self.task_manager._execute_workflow_actions(actions)
            
    except Exception as e:
        print(f"执行AI代码失败: {e}")
        import traceback
        traceback.print_exc()
        self.add_status_message(f"执行AI代码失败: {e}")
