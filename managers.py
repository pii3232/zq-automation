"""管理器模块：关键词、工作流、任务、项目管理"""
import os
import json
import time
import random
import threading
import zipfile
import shutil
import queue
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import pyautogui
import cv2
import numpy as np

from apscheduler.schedulers.background import BackgroundScheduler


class KeywordManager:
    """关键词管理器"""
    def __init__(self, config):
        self.config = config
        # keywords.json 在项目目录中
        self.update_keywords_file()
        self.keywords = self.load_keywords()
        self.initialize_default_keywords()
    
    def update_keywords_file(self):
        """更新关键词文件路径"""
        os.makedirs(self.config.projects_directory, exist_ok=True)
        self.keywords_file = os.path.join(self.config.projects_directory, 'keywords.json')
        print(f"[KeywordManager] 关键词文件路径已更新: {self.keywords_file}")
        
    def initialize_default_keywords(self):
        default_keywords = [
            {
                'name': '发现',
                'description': '在指定范围内查找图片并点击',
                'script': '''if last_x == 0 and last_y == 0:
    coords = image.find(image_path, timeout=10)
else:
    coords = image.find_image_in_range(image_path, last_x, last_y, search_range=300, timeout=10)
if coords:
    time.sleep(random.uniform(0.3, 0.5))
    mouse.click(coords[0], coords[1])
    last_x, last_y = coords''',
                'parameters': ['image_path'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': '查找',
                'description': '在全屏范围查找图片并点击',
                'script': '''coords = image.find(image_path, timeout=10)
if coords:
    time.sleep(random.uniform(0.3, 0.5))
    mouse.click(coords[0], coords[1])
    last_x, last_y = coords''',
                'parameters': ['image_path'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': '点击',
                'description': '鼠标左键点击指定坐标',
                'script': 'mouse.click(x, y)\nlast_x, last_y = x, y',
                'parameters': ['x', 'y'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': '双击',
                'description': '鼠标左键双击指定坐标',
                'script': 'mouse.double_click(x, y)\nlast_x, last_y = x, y',
                'parameters': ['x', 'y'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': '拖到',
                'description': '鼠标从坐标1拖动到坐标2',
                'script': 'mouse.drag_to(x1, y1, x2, y2)\nlast_x, last_y = x2, y2',
                'parameters': ['x1', 'y1', 'x2', 'y2'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': '滑动',
                'description': '从坐标1滑动到坐标2',
                'script': 'mouse.scroll(x1, y1, x2, y2)\nlast_x, last_y = x2, y2',
                'parameters': ['x1', 'y1', 'x2', 'y2'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': '键盘输入',
                'description': '输入文本',
                'script': 'keyboard.type(text)',
                'parameters': ['text'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'name': '延时',
                'description': '延时等待一段时间（单位：毫秒）',
                'script': '''import time
time.sleep(delay_ms / 1000.0)''',
                'parameters': ['delay_ms'],
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        for kw in default_keywords:
            if kw['name'] not in [k['name'] for k in self.keywords]:
                self.keywords.append(kw)
        self.save_keywords()
        
    def load_keywords(self) -> List[Dict]:
        if os.path.exists(self.keywords_file):
            try:
                with open(self.keywords_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
        
    def save_keywords(self):
        with open(self.keywords_file, 'w', encoding='utf-8') as f:
            json.dump(self.keywords, f, ensure_ascii=False, indent=2)
            
    def add_keyword(self, name: str, description: str, script: str, parameters: List[str]) -> bool:
        if any(k['name'] == name for k in self.keywords):
            return False
        self.keywords.append({
            'name': name,
            'description': description,
            'script': script,
            'parameters': parameters,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.save_keywords()
        return True
        
    def get_keyword(self, name: str) -> Optional[Dict]:
        for kw in self.keywords:
            if kw['name'] == name:
                return kw
        return None
        
    def get_all_keywords(self) -> List[Dict]:
        return self.keywords
        
    def update_keyword(self, name: str, **kwargs) -> bool:
        for kw in self.keywords:
            if kw['name'] == name:
                kw.update(kwargs)
                self.save_keywords()
                return True
        return False
        
    def delete_keyword(self, name: str) -> bool:
        for i, kw in enumerate(self.keywords):
            if kw['name'] == name:
                self.keywords.pop(i)
                self.save_keywords()
                return True
        return False
        
    def copy_keyword(self, name: str, new_name: str) -> bool:
        kw = self.get_keyword(name)
        if kw:
            new_kw = kw.copy()
            new_kw['name'] = new_name
            new_kw['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.keywords.append(new_kw)
            self.save_keywords()
            return True
        return False


class WorkflowManager:
    """工作流管理器"""
    def __init__(self, config):
        self.config = config
        self.update_workflows_file()
        self.workflows = self.load_workflows()
    
    def update_workflows_file(self):
        """更新工作流文件路径"""
        os.makedirs(self.config.projects_directory, exist_ok=True)
        self.workflows_file = os.path.join(self.config.projects_directory, 'workflows.json')
        print(f"[WorkflowManager] 工作流文件路径已更新: {self.workflows_file}")
        
    def load_workflows(self) -> List[Dict]:
        if os.path.exists(self.workflows_file):
            try:
                with open(self.workflows_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
        
    def save_workflows(self):
        with open(self.workflows_file, 'w', encoding='utf-8') as f:
            json.dump(self.workflows, f, ensure_ascii=False, indent=2)
            
    def add_workflow(self, name: str, steps: List[Dict], description: str = '') -> bool:
        if any(w['name'] == name for w in self.workflows):
            return False
        self.workflows.append({
            'name': name,
            'description': description,
            'steps': steps,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        self.save_workflows()
        return True

    def create_workflow_from_dict(self, workflow_dict: Dict) -> bool:
        """从字典创建工作流"""
        return self.add_workflow(
            workflow_dict['name'],
            workflow_dict['steps'],
            workflow_dict.get('description', '')
        )

    def get_workflow(self, name: str) -> Optional[Dict]:
        for wf in self.workflows:
            if wf['name'] == name:
                return wf
        return None

    def get_all_workflows(self) -> List[Dict]:
        return self.workflows
        
    def update_workflow(self, old_name: str, **kwargs) -> bool:
        for wf in self.workflows:
            if wf['name'] == old_name:
                if 'name' in kwargs:
                    wf['name'] = kwargs.pop('name')
                wf.update(kwargs)
                self.save_workflows()
                return True
        return False
        
    def delete_workflow(self, name: str) -> bool:
        for i, wf in enumerate(self.workflows):
            if wf['name'] == name:
                self.workflows.pop(i)
                self.save_workflows()
                return True
        return False
        
    def copy_workflow(self, name: str, new_name: str) -> bool:
        wf = self.get_workflow(name)
        if wf:
            new_wf = wf.copy()
            new_wf['name'] = new_name
            new_wf['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.workflows.append(new_wf)
            self.save_workflows()
            return True
        return False

    def clear_all_workflows(self) -> bool:
        """清空所有工作流"""
        try:
            self.workflows.clear()
            self.save_workflows()
            return True
        except Exception as e:
            print(f"清空工作流失败: {e}")
            return False


class TaskManager:
    """任务管理器"""
    def __init__(self, config, execution_engine, keyboard_engine, image_recognition, keyword_manager):
        self.config = config
        os.makedirs(config.projects_directory, exist_ok=True)
        self.tasks_file = os.path.join(config.projects_directory, 'tasks.json')
        self.tasks = self.load_tasks()
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        self.execution_engine = execution_engine
        self.keyboard_engine = keyboard_engine
        self.image_recognition = image_recognition
        self.keyword_manager = keyword_manager
        self.running_tasks = {}
        
        # 多线程相关
        self.task_thread_count = getattr(self.config, 'task_thread_count', 3)
        self.task_queue = queue.Queue()
        self.mouse_lock = threading.Lock()
        self.active_threads = 0
        self.stop_event = threading.Event()
        
        # 启动工作线程
        self._start_worker_threads()
        
    def _start_worker_threads(self):
        """启动工作线程池"""
        for i in range(self.task_thread_count):
            thread = threading.Thread(target=self._worker_thread, args=(i,), daemon=True)
            thread.start()
            print(f"[TaskManager] 启动工作线程 {i+1}/{self.task_thread_count}")
    
    def _worker_thread(self, thread_id):
        """工作线程，处理任务队列"""
        while not self.stop_event.is_set():
            try:
                # 从队列获取任务（超时1秒）
                task_id = self.task_queue.get(timeout=1)
                if task_id is None:
                    continue
                
                # 获取任务数据
                task = self.get_task(task_id)
                if not task:
                    print(f"[Worker {thread_id}] 任务不存在: {task_id}")
                    continue
                
                # 增加活动线程计数
                with threading.Lock():
                    self.active_threads += 1
                
                print(f"[Worker {thread_id}] 开始执行任务: {task_id}")
                
                # 执行任务（使用鼠标锁）
                try:
                    self._execute_task_with_lock(task)
                except Exception as e:
                    print(f"[Worker {thread_id}] 任务执行失败: {e}")
                    import traceback
                    traceback.print_exc()
                
                # 减少活动线程计数
                with threading.Lock():
                    self.active_threads -= 1
                
                print(f"[Worker {thread_id}] 任务完成: {task_id}")
                
            except queue.Empty:
                # 队列空，继续等待
                continue
            except Exception as e:
                print(f"[Worker {thread_id}] 工作线程异常: {e}")
    
    def _execute_task_with_lock(self, task: Dict):
        """带鼠标锁的任务执行（支持workflow_items）"""
        task_id = task['id']
        workflow_items = task.get('workflow_items', [])
        
        if not workflow_items:
            print(f"[TaskManager] 任务 {task_id} 没有工作流项目")
            return
        
        # 检查任务是否需要鼠标锁（如果有任何一个工作流需要鼠标操作）
        needs_mouse_lock = False
        for item in workflow_items:
            workflow_name = item.get('workflow', '')
            if workflow_name and self._needs_mouse_operation(workflow_name):
                needs_mouse_lock = True
                break
        
        if needs_mouse_lock:
            with self.mouse_lock:
                print(f"[MouseLock] 获取鼠标锁，执行任务: {task_id}")
                self._execute_task_workflows(task)
                print(f"[MouseLock] 释放鼠标锁，任务完成: {task_id}")
        else:
            # 不需要鼠标操作的任务，直接执行
            self._execute_task_workflows(task)
    
    def _needs_mouse_operation(self, workflow_name):
        """检查工作流是否需要鼠标操作"""
        # 简化的判断：检查工作流名称或步骤中是否包含点击、查找等关键词
        workflow = self._get_workflow_by_name(workflow_name)
        if not workflow:
            return False
        
        steps = workflow.get('steps', [])
        for step in steps:
            keyword = step.get('keyword', '')
            if any(kw in keyword for kw in ['点击', '查找', '发现', '多图', '快找']):
                return True
        return False
    
    def queue_task(self, task_id):
        """将任务加入队列"""
        self.task_queue.put(task_id)
        print(f"[TaskManager] 任务已加入队列: {task_id}, 队列大小: {self.task_queue.qsize()}")
        
    def get_queue_size(self):
        """获取队列大小"""
        return self.task_queue.qsize()
    
    def get_active_threads(self):
        """获取活动线程数"""
        return self.active_threads
        
    def load_tasks(self) -> List[Dict]:
        if os.path.exists(self.tasks_file):
            try:
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
        
    def save_tasks(self):
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)
            
    def add_task(self, workflow_name: str = None, schedule_time: str = None, 
                delay_minutes: int = None, repeat_count: int = 1, 
                repeat_type: str = 'none', schedule_type: int = 0,
                workflow_items: list = None) -> str:
        task_id = f"task_{int(time.time())}"
        
        # 根据schedule_type设置执行时间
        if schedule_type == 0:  # 立即执行
            schedule_time = None
            delay_minutes = None
        elif schedule_type == 1:  # 定时执行
            # schedule_time已经传进来了，直接使用
            delay_minutes = None
        elif schedule_type == 2:  # 延时执行
            schedule_time = None
            # delay_minutes已经传进来了，直接使用
        else:
            # 如果schedule_time为None，设置为当前时间加1小时
            if schedule_time is None:
                schedule_datetime = datetime.now() + timedelta(hours=1)
                schedule_time = schedule_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建任务数据
        task = {
            'id': task_id,
            'status': 'pending',
            'schedule_time': schedule_time,
            'delay_minutes': delay_minutes,
            'repeat_count': repeat_count,
            'repeat_type': repeat_type,
            'executed_count': 0,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 支持新的workflow_items格式或旧的workflow_name格式（向后兼容）
        if workflow_items:
            task['workflow_items'] = workflow_items
        elif workflow_name:
            # 向后兼容：将单个workflow转换为workflow_items格式
            task['workflow_items'] = [{
                'workflow': workflow_name,
                'delay_minutes': 0
            }]
        else:
            raise ValueError("必须提供 workflow_name 或 workflow_items")
        
        self.tasks.append(task)
        
        # 调度任务
        self.schedule_task(task)
        
        self.save_tasks()
        return task_id
        
    def get_task(self, task_id: str) -> Optional[Dict]:
        for task in self.tasks:
            if task['id'] == task_id:
                return task
        return None
        
    def get_all_tasks(self) -> List[Dict]:
        return self.tasks
        
    def update_task(self, task_id: str, **kwargs) -> bool:
        for task in self.tasks:
            if task['id'] == task_id:
                task.update(kwargs)
                self.save_tasks()
                return True
        return False
        
    def delete_task(self, task_id: str) -> bool:
        for i, task in enumerate(self.tasks):
            if task['id'] == task_id:
                # 从调度器中移除任务
                try:
                    if self.scheduler.get_job(task_id):
                        self.scheduler.remove_job(task_id)
                except:
                    pass
                
                self.tasks.pop(i)
                self.save_tasks()
                return True
        return False
        
    def schedule_task(self, task: Dict):
        """调度任务"""
        task_id = task['id']
        
        # 如果任务已经在调度器中，先移除
        try:
            if self.scheduler.get_job(task_id):
                self.scheduler.remove_job(task_id)
        except:
            pass
        
        # 立即执行 - 加入队列
        if not task['schedule_time'] and not task['delay_minutes']:
            print(f"调度立即执行任务: {task_id}")
            self.queue_task(task_id)
            
        # 定时执行
        elif task['schedule_time']:
            try:
                run_time = datetime.strptime(task['schedule_time'], '%Y-%m-%d %H:%M:%S')
                print(f"调度定时任务: {task_id}, 执行时间: {run_time}")
                
                # 使用lambda包装，将任务加入队列
                self.scheduler.add_job(
                    lambda: self.queue_task(task_id),
                    'date',
                    run_date=run_time,
                    id=task_id
                )
            except Exception as e:
                print(f"调度定时任务失败: {e}")
                
        # 延时执行
        elif task['delay_minutes']:
            delay_seconds = task['delay_minutes'] * 60
            print(f"调度延时任务: {task_id}, 延时: {task['delay_minutes']}分钟")
            
            run_time = datetime.now() + timedelta(seconds=delay_seconds)
            self.scheduler.add_job(
                lambda: self.queue_task(task_id),
                'date',
                run_date=run_time,
                id=task_id
            )
        
    def pause_task(self, task_id: str) -> bool:
        return self.update_task(task_id, status='paused')
        
    def resume_task(self, task_id: str) -> bool:
        return self.update_task(task_id, status='pending')
        
    def execute_task_now(self, task_id: str) -> bool:
        task = self.get_task(task_id)
        if task:
            threading.Thread(target=self._execute_task_with_lock, args=(task,)).start()
            return True
        return False
        
    def _execute_task_workflows(self, task: Dict, stop_check_fn=None):
        """执行任务中的所有工作流（按顺序执行）"""
        task_id = task['id']
        workflow_items = task.get('workflow_items', [])
        
        if not workflow_items:
            print(f"[TaskManager] 任务 {task_id} 没有工作流项目")
            return
        
        print(f"[TaskManager] 开始执行任务 {task_id}，包含 {len(workflow_items)} 个工作流")
        
        # 按顺序执行每个工作流项目
        for i, item in enumerate(workflow_items):
            workflow_name = item.get('workflow', '')
            delay_minutes = item.get('delay_minutes', 0)
            
            if not workflow_name:
                print(f"[TaskManager] 工作流项目 {i+1} 没有指定工作流名称，跳过")
                continue
            
            print(f"[TaskManager] 执行工作流 {i+1}/{len(workflow_items)}: {workflow_name}")
            
            # 执行当前工作流
            self._execute_workflow(workflow_name, task_id, stop_check_fn)
            
            # 如果不是最后一个工作流，添加延时
            if i < len(workflow_items) - 1 and delay_minutes > 0:
                print(f"[TaskManager] 工作流 {workflow_name} 执行完成，等待 {delay_minutes} 分钟...")
                import time
                # 使用非阻塞方式等待，每秒检查一次停止标志
                delay_seconds = delay_minutes * 60
                elapsed = 0
                while elapsed < delay_seconds:
                    if stop_check_fn and stop_check_fn():
                        print(f"[TaskManager] 检测到停止信号，中止等待")
                        return
                    time.sleep(1)  # 每秒检查一次
                    elapsed += 1
        
        print(f"[TaskManager] 任务 {task_id} 的所有工作流执行完成")

    def _execute_workflow(self, workflow_name: str, task_id: str = None, stop_check_fn=None):
        """执行工作流
        Args:
            workflow_name: 工作流名称
            task_id: 任务ID（可选）
            stop_check_fn: 停止检查函数（可选），如果返回True则停止执行
        """
        # 先检查工作流，再检查关键词（修复：工作流名称可能与关键词名称相同的问题）
        workflow = self._get_workflow_by_name(workflow_name)
        if not workflow:
            # 如果工作流不存在，再检查是否是关键词
            workflow = self.keyword_manager.get_keyword(workflow_name)
        if not workflow:
            print(f"工作流不存在: {workflow_name}")
            return
            
        if task_id:
            self.update_task(task_id, status='running')
            
        last_x, last_y = 0, 0
        
        try:
            steps = workflow.get('steps', [])
            
            # 触发判断：查找第一个触发步骤（step_type为'触发'）
            trigger_step_idx = -1
            for i, step in enumerate(steps):
                if isinstance(step, dict) and step.get('step_type') == '触发':
                    trigger_step_idx = i
                    break
            
            # 如果存在触发步骤，先执行触发判断
            if trigger_step_idx >= 0:
                trigger_step = steps[trigger_step_idx]
                keyword_name = trigger_step['keyword']
                
                # 只对"发现丨截图"类型的触发步骤进行特殊处理
                if '发现丨截图' in keyword_name:
                    image_path = trigger_step.get('params', trigger_step.get('parameters', ''))
                    pic_dir = self.config.pic_directory
                    if not image_path.startswith(pic_dir):
                        image_path = os.path.join(pic_dir, image_path)
                    
                    if not os.path.exists(image_path):
                        print(f"触发判断失败：图片不存在: {image_path}")
                        print("工作流不执行，立即退出")
                        return

                    print(f"触发判断：查找图片: {image_path}, 相似度: 0.8")
                    # 触发判断只用一次找图，相似度0.8
                    coords = self.image_recognition.find_image(image_path, timeout=0, confidence=0.8)

                    if not coords:
                        print("触发判断失败：未找到图片，工作流不执行")
                        print("立即退出")
                        return
                    
                    print("触发判断成功：找到图片，继续执行工作流")
            
            # 执行工作流步骤
            for step_index, step in enumerate(steps):
                # 检查是否应该停止
                if stop_check_fn and stop_check_fn():
                    print(f"工作流 '{workflow_name}' 执行被停止")
                    return
                
                keyword_name = step['keyword']
                params = step.get('params', step.get('parameters', ''))
                delay = step.get('delay', 0)
                timeout = step.get('timeout', 10)
                step_type = step.get('step_type', '普通')

                if delay > 0:
                    # 分段延时，允许响应停止命令
                    delay_seconds = delay / 1000.0
                    for i in range(int(delay_seconds * 10)):  # 每100ms检查一次
                        if stop_check_fn and stop_check_fn():
                            print(f"工作流 '{workflow_name}' 执行被停止")
                            return
                        time.sleep(0.1)
                    # 剩余的小于100ms的延时
                    remaining = delay_seconds % 0.1
                    if remaining > 0:
                        time.sleep(remaining)
                    
                print(f"执行步骤 {step_index + 1}/{len(steps)}: {keyword_name} {params} (类型: {step_type})")

                # 特殊处理发现丨截图关键词
                if keyword_name == '发现' or keyword_name == '查找':
                    try:
                        image_path = params
                        pic_dir = self.config.pic_directory
                        if not image_path.startswith(pic_dir):
                            image_path = os.path.join(pic_dir, image_path)

                        if not os.path.exists(image_path):
                            print(f"图片不存在: {image_path}")
                            continue

                        # 根据步骤类型选择查找模式
                        if step_type == '触发':
                            # 触发模式：只执行一次找图判断
                            print(f"触发步骤：执行单次找图判断")
                            coords = self.image_recognition.find_image(image_path, timeout=0, confidence=0.8, mode='trigger')

                            if not coords:
                                print("触发判断失败：未找到图片，整个工作流退出")
                                return

                            print("触发判断成功：找到图片，继续执行后续步骤")

                            # 执行点击操作
                            if coords:
                                last_x, last_y = coords
                                print(f"触发步骤：找到图片，坐标: ({last_x}, {last_y})")

                                # 随机等待 300-400ms
                                wait_before_click = random.uniform(0.3, 0.4)
                                print(f"触发步骤：等待 {wait_before_click*1000:.0f}ms 后进行点击...")

                                # 分段等待，每 50ms 检查一次停止标志
                                elapsed = 0
                                while elapsed < wait_before_click:
                                    if stop_check_fn and stop_check_fn():
                                        print(f"触发步骤：检测到停止信号，中止点击前等待")
                                        return None
                                    time.sleep(0.05)
                                    elapsed += 0.05

                                print(f"触发步骤：点击前等待完成，准备点击坐标: ({last_x}, {last_y})")

                                # 点击
                                try:
                                    self.execution_engine.click(int(last_x), int(last_y))
                                    print(f"触发步骤：点击成功")
                                except Exception as e:
                                    print(f"触发步骤：点击失败: {e}")
                                    import traceback
                                    traceback.print_exc()

                                # 随机等待 1400-1600ms
                                wait_after_click = random.uniform(1.4, 1.6)
                                print(f"触发步骤：等待 {wait_after_click*1000:.0f}ms，本条找图工作结束")

                                # 分段等待，每 100ms 检查一次停止标志
                                elapsed = 0
                                while elapsed < wait_after_click:
                                    if stop_check_fn and stop_check_fn():
                                        print(f"触发步骤：检测到停止信号，中止点击后等待")
                                        return None
                                    time.sleep(0.1)
                                    elapsed += 0.1

                                print(f"触发步骤：点击后等待完成，本条找图工作结束")
                        else:
                            # 正常或终结模式：使用3种算法轮换找图
                            print(f"使用3种算法轮换找图（{step_type}状态）...")
                            print(f"[DEBUG] 准备调用_find_image_with_3_algos，image_path={image_path}")
                            coords = self._find_image_with_3_algos(image_path, stop_check_fn=stop_check_fn)
                            print(f"[DEBUG] _find_image_with_3_algos 返回: {coords}")

                            # 更新last_x和last_y（用于后续步骤）
                            if coords:
                                last_x, last_y = coords
                                print(f"已更新last坐标: ({last_x}, {last_y})")

                    except Exception as e:
                        print(f"发现丨截图失败: {e}")
                        import traceback
                        traceback.print_exc()

                    # 检查是否是终结步骤（在执行完发现丨截图之后检查）
                    if step_type == '终结':
                        print(f"步骤 {step_index + 1} 是终结步骤，工作流执行结束")
                        break

                    # 跳过exec执行
                    continue
                
                elif keyword_name == '任意指令':
                    # 任意指令：直接执行用户输入的代码
                    try:
                        code = step.get('code', '')
                        if not code:
                            print("任意指令的代码为空，跳过")
                            continue
                        
                        print(f"执行任意指令代码")
                        
                        # 准备执行环境
                        exec_globals = {
                            'mouse': self.execution_engine,
                            'keyboard': self.keyboard_engine,
                            'image': self.image_recognition,
                            'config': self.config,
                            'time': time,
                            'random': random,
                            'last_x': last_x,
                            'last_y': last_y,
                            'pyautogui': pyautogui,  # 直接提供pyautogui模块
                            'cv2': cv2,
                            'np': np,
                            'os': os
                        }
                        
                        # 执行代码
                        exec(code, exec_globals)
                        
                        print("任意指令执行完成")
                        
                    except Exception as e:
                        print(f"执行任意指令时出错: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                else:
                    # 其他关键词通过exec执行
                    keyword = self.keyword_manager.get_keyword(keyword_name)
                    if not keyword:
                        print(f"关键词不存在: {keyword_name}")
                        continue
                        
                    script = keyword['script']
                    
                    # 调试信息：打印关键词信息
                    if keyword_name == '延时':
                        print(f"执行延时关键词，参数: {params}")
                    
                    param_list = []
                    if params:
                        if '|' in params:
                            param_list = params.split('|')
                        elif ',' in params and len(keyword['parameters']) > 1:
                            param_list = [p.strip() for p in params.split(',')]
                        else:
                            param_list = [params]
                    
                    # 调试输出：打印参数解析结果
                    print(f"[DEBUG] 关键词 '{keyword_name}' 参数解析: params='{params}', param_list={param_list}")
                    
                    exec_globals = {
                        'mouse': self.execution_engine,
                        'keyboard': self.keyboard_engine,
                        'image': self.image_recognition,
                        'config': self.config,  # 添加config变量
                        'time': time,
                        'random': random,
                        'last_x': last_x,
                        'last_y': last_y
                    }
                    
                    for i, param in enumerate(param_list):
                        param_name = keyword['parameters'][i] if i < len(keyword['parameters']) else f'param_{i}'
                        try:
                            if param_name in ['x', 'y', 'x1', 'y1', 'x2', 'y2']:
                                exec_globals[param_name] = int(param)
                            elif param_name == 'delay_ms':
                                # 延时关键词的参数，转换为整数（毫秒）
                                exec_globals[param_name] = int(param)
                            elif param_name == 'image_path':
                                pic_dir = self.config.pic_directory
                                if not param.startswith(pic_dir):
                                    exec_globals[param_name] = os.path.join(pic_dir, param)
                                else:
                                    exec_globals[param_name] = param
                            else:
                                exec_globals[param_name] = param
                        except ValueError:
                            if param_name == 'image_path':
                                pic_dir = self.config.pic_directory
                                exec_globals[param_name] = os.path.join(pic_dir, param)
                            elif param_name == 'delay_ms':
                                # 如果转换失败，默认为0
                                exec_globals[param_name] = 0
                            else:
                                exec_globals[param_name] = param
                    
                    # 调试信息：打印坐标参数
                    if keyword_name == '拖到':
                        print(f"[DEBUG] 拖到参数: x1={exec_globals.get('x1')}, y1={exec_globals.get('y1')}, x2={exec_globals.get('x2')}, y2={exec_globals.get('y2')}")

                    try:
                        exec(script, exec_globals)

                        # 更新last_x和last_y
                        if 'last_x' in exec_globals:
                            last_x = exec_globals['last_x']
                        if 'last_y' in exec_globals:
                            last_y = exec_globals['last_y']
                    except Exception as e:
                        print(f"执行脚本时出错: {e}")
                        import traceback
                        traceback.print_exc()

            print(f"[DEBUG] 工作流 '{workflow_name}' 所有步骤执行完成")

            if task_id:
                task = self.get_task(task_id)
                if task:
                    executed_count = task.get('executed_count', 0) + 1
                    repeat_count = task.get('repeat_count', 1)

                    if task['repeat_type'] == 'daily':
                        self.update_task(task_id, status='pending', executed_count=executed_count)
                        next_run = datetime.now() + timedelta(days=1)
                        self.scheduler.add_job(
                            self._execute_workflow,
                            'date',
                            run_date=next_run,
                            args=[workflow_name, task_id],
                            id=task_id
                        )
                    elif executed_count < repeat_count:
                        self.update_task(task_id, status='pending', executed_count=executed_count)
                    else:
                        self.update_task(task_id, status='completed')

            print(f"[DEBUG] 工作流 '{workflow_name}' 执行完成，准备返回")

        except Exception as e:
            print(f"工作流执行异常: {str(e)}")
            if task_id:
                self.update_task(task_id, status='failed')
    
    def _get_workflow_by_name(self, name: str) -> Optional[Dict]:
        from managers import WorkflowManager
        wf_manager = WorkflowManager(self.config)
        return wf_manager.get_workflow(name)

    def _find_image_with_3_algos(self, image_path: str, stop_check_fn=None) -> Optional[tuple]:
        """
        使用3种算法轮换找图（用于普通和终结状态的发现丨截图）
        算法顺序：TemplateMatching -> CCORR_NORMED -> SQDIFF_NORMED
        相似度：0.9 -> 0.8 -> 0.7
        每次切换延时：400ms
        找到后：随机等待300-400ms -> 点击 -> 随机等待1400-1600ms
        """
        import os

        print(f"[3算法找图] 开始查找: {image_path}")

        if not os.path.exists(image_path):
            print(f"[3算法找图] 图片文件不存在: {image_path}")
            return None

        # 读取模板图片
        template = cv2.imread(image_path)
        if template is None:
            print(f"[3算法找图] 无法读取图片: {image_path}")
            return None

        h, w = template.shape[:2]
        print(f"[3算法找图] 模板图片尺寸: {w}x{h}")

        # 定义3种算法
        algorithms = [
            (cv2.TM_CCOEFF_NORMED, "TemplateMatching"),
            (cv2.TM_CCORR_NORMED, "CCORR_NORMED"),
            (cv2.TM_SQDIFF_NORMED, "SQDIFF_NORMED"),
        ]
        confidences = [0.9, 0.8, 0.7]

        # 截取屏幕
        screenshot = pyautogui.screenshot()
        screen_np = np.array(screenshot)
        screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)

        # 尝试不同算法和相似度
        attempt_count = 0
        found = False
        coords = None

        for algo_idx, (algo, algo_name) in enumerate(algorithms):
            for conf_idx, conf_val in enumerate(confidences):
                try:
                    # 检查停止标志
                    if stop_check_fn and stop_check_fn():
                        print(f"[3算法找图] 检测到停止信号，中止找图")
                        return None

                    attempt_count += 1
                    print(f"[3算法找图] 第{attempt_count}次尝试：算法 {algo_name}, 相似度 {conf_val}")

                    # 模板匹配
                    result = cv2.matchTemplate(screen_cv2, template, algo)

                    # 根据不同算法类型获取最佳匹配位置
                    if algo in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                        # 平方差算法：值越小越匹配
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        match_val = 1.0 - min_val  # 转换为相似度（越大越匹配）
                        match_loc = min_loc
                    else:
                        # 其他算法：值越大越匹配
                        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                        match_val = max_val
                        match_loc = max_loc

                    print(f"[3算法找图] 相似度: {match_val:.3f}")

                    if match_val >= conf_val:
                        # 计算中心坐标
                        center_x = match_loc[0] + w // 2
                        center_y = match_loc[1] + h // 2
                        print(f"[3算法找图] 找到图片！算法: {algo_name}, 相似度: {match_val:.3f}, 坐标: ({int(center_x)}, {int(center_y)})")

                        # 找到后随机等待300-400ms
                        wait_before_click = random.uniform(0.3, 0.4)
                        print(f"[3算法找图] 等待 {wait_before_click*1000:.0f}ms 后进行点击...")

                        # 分段等待，每50ms检查一次停止标志
                        elapsed = 0
                        while elapsed < wait_before_click:
                            if stop_check_fn and stop_check_fn():
                                print(f"[3算法找图] 检测到停止信号，中止点击前等待")
                                return None
                            time.sleep(0.05)  # 每50ms检查一次
                            elapsed += 0.05

                        print(f"[3算法找图] 点击前等待完成，准备点击坐标: ({int(center_x)}, {int(center_y)})")

                        # 点击（使用ExecutionEngine的click方法，确保可靠性）
                        print(f"[3算法找图] 开始点击坐标: ({int(center_x)}, {int(center_y)})")
                        print(f"[3算法找图] execution_engine 是否存在: {hasattr(self, 'execution_engine') and self.execution_engine is not None}")

                        try:
                            if hasattr(self, 'execution_engine') and self.execution_engine is not None:
                                self.execution_engine.click(int(center_x), int(center_y))
                                print(f"[3算法找图] 点击成功，已完成点击操作")
                            else:
                                print(f"[3算法找图] 错误：execution_engine 不存在或为 None！")
                                # 尝试直接使用 pyautogui 点击
                                pyautogui.click(int(center_x), int(center_y))
                                print(f"[3算法找图] 使用 pyautogui 直接点击成功")
                        except Exception as e:
                            print(f"[3算法找图] 点击失败: {e}")
                            import traceback
                            traceback.print_exc()

                        # 点击后随机等待1400-1600ms
                        wait_after_click = random.uniform(1.4, 1.6)
                        print(f"[3算法找图] 等待 {wait_after_click*1000:.0f}ms，本条找图工作结束")

                        # 分段等待，每100ms检查一次停止标志
                        elapsed = 0
                        while elapsed < wait_after_click:
                            if stop_check_fn and stop_check_fn():
                                print(f"[3算法找图] 检测到停止信号，中止点击后等待")
                                return None
                            time.sleep(0.1)  # 每100ms检查一次
                            elapsed += 0.1

                        print(f"[3算法找图] 点击后等待完成，本条找图工作完成")
                        coords = (int(center_x), int(center_y))
                        found = True
                        break
                    else:
                        # 延时400ms后尝试下一个相似度（分段等待）
                        if conf_idx < len(confidences) - 1:
                            print(f"[3算法找图] 相似度不足，延时400ms后尝试更低相似度")
                            # 分段等待，每100ms检查一次停止标志
                            elapsed = 0
                            while elapsed < 0.4:
                                if stop_check_fn and stop_check_fn():
                                    print(f"[3算法找图] 检测到停止信号，中止相似度切换等待")
                                    return None
                                time.sleep(0.1)  # 每100ms检查一次
                                elapsed += 0.1
                        # 如果是最后一个相似度，延时400ms后尝试下一个算法
                        else:
                            print(f"[3算法找图] 当前算法和相似度未找到，延时400ms后尝试下一个算法")
                            # 分段等待，每100ms检查一次停止标志
                            elapsed = 0
                            while elapsed < 0.4:
                                if stop_check_fn and stop_check_fn():
                                    print(f"[3算法找图] 检测到停止信号，中止算法切换等待")
                                    return None
                                time.sleep(0.1)  # 每100ms检查一次
                                elapsed += 0.1

                except Exception as e:
                    print(f"[3算法找图] 算法 {algo_name} 出错: {e}")
                    continue

            if found:
                break

        if found:
            print(f"[3算法找图] 找图成功！")
            return coords

        print(f"[3算法找图] 3种算法和相似度轮换均未找到图片: {image_path}，本条工作流结束")
        return None

    def save_tasks_to_file(self, file_path: str):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=2)
            
    def load_tasks_from_file(self, file_path: str):
        with open(file_path, 'r', encoding='utf-8') as f:
            self.tasks = json.load(f)
        self.save_tasks()


class ProjectManager:
    """项目管理器"""
    def __init__(self, config):
        self.config = config
        os.makedirs(config.projects_directory, exist_ok=True)
        self.projects_file = os.path.join(config.projects_directory, 'projects.json')
        self.current_project = 'default'
        self.projects = self.load_projects()
        # 加载上次的当前项目
        self._load_current_project_config()

    def get_project_dir(self, project_name: str) -> str:
        """获取项目目录"""
        if project_name == 'default':
            return self.config.working_directory
        # 使用安全的get方法查找项目
        project = next((p for p in self.projects if p.get('name') == project_name), None)
        if project:
            project_path = project.get('path', '')
            if project_path:
                return os.path.join(self.config.projects_directory, project_path)
        return self.config.working_directory

    def load_projects(self) -> List[Dict]:
        """加载项目列表"""
        if os.path.exists(self.projects_file):
            try:
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    self.projects = json.load(f)
                    # 为缺少pic_dir字段的项目补充字段
                    for project in self.projects:
                        if 'pic_dir' not in project and 'pic_directory' not in project:
                            project_path = project.get('path', '')
                            if project_path == 'default':
                                project['pic_dir'] = self.config.pic_directory
                            else:
                                project['pic_dir'] = os.path.join(project_path, 'pic')
            except Exception as e:
                print(f"加载项目列表失败: {e}")
                self.projects = []
        else:
            self.projects = []

        # 检查default项目是否存在，不存在则创建
        default_exists = False
        for project in self.projects:
            if project.get('name') == 'default':
                default_exists = True
                # 确保default项目有pic_dir字段
                if 'pic_dir' not in project and 'pic_directory' not in project:
                    project['pic_dir'] = self.config.pic_directory
                break

        if not default_exists:
            self.projects.append({
                'name': 'default',
                'path': 'default',
                'pic_dir': self.config.pic_directory,
                'version': '1.0.0',
                'program': '',
                'resolution': '1920*1080',
                'notes': '',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            self.save_projects()

        return self.projects

    def save_projects(self):
        with open(self.projects_file, 'w', encoding='utf-8') as f:
            json.dump(self.projects, f, ensure_ascii=False, indent=2)

    def create_project(self, name: str, path: str, version: str = '1.0.0',
                       program: str = '', resolution: str = '1920*1080',
                       notes: str = '') -> bool:
        """创建新项目
        Args:
            name: 项目名称（中英文）
            path: 项目目录路径（非中文）
            version: 项目版本
            program: 对应程序
            resolution: 屏幕分辨率
            notes: 备注
        """
        # 使用安全的get方法检查项目是否已存在
        if any(p.get('name') == name for p in self.projects):
            return False

        # 验证路径是否包含中文字符
        if any('\u4e00' <= c <= '\u9fff' for c in path):
            return False

        try:
            # 创建项目目录
            os.makedirs(path, exist_ok=True)
            
            # 创建pic目录
            pic_dir = os.path.join(path, 'pic')
            os.makedirs(pic_dir, exist_ok=True)
            
            # 创建records目录
            records_dir = os.path.join(path, 'records')
            os.makedirs(records_dir, exist_ok=True)
            
            # 创建必备的JSON文件
            json_files = {
                'answer_tasks.json': [],
                'daily_tasks.json': [],
                'discovery_tasks.json': [],
                'tasks.json': [],
                'workflows.json': [],
                'keywords.json': []
            }
            
            for filename, default_content in json_files.items():
                file_path = os.path.join(path, filename)
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_content, f, ensure_ascii=False, indent=2)
                    print(f"[创建项目] 已创建文件: {file_path}")

            self.projects.append({
                'name': name,
                'path': path,
                'pic_dir': pic_dir,
                'records_dir': records_dir,
                'version': version,
                'program': program,
                'resolution': resolution,
                'notes': notes,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            self.save_projects()
            
            # 设置项目目录为当前工作目录
            self.config.projects_directory = path
            self.config.working_directory = path
            self.config.pic_directory = pic_dir
            
            print(f"[创建项目] 项目创建成功: {name}")
            print(f"[创建项目] 项目目录: {path}")
            print(f"[创建项目] 图片目录: {pic_dir}")
            print(f"[创建项目] 记录目录: {records_dir}")
            
            return True
        except Exception as e:
            print(f"创建项目失败: {e}")
            return False

    def switch_project(self, name: str) -> Dict:
        """切换项目并返回项目配置
        Args:
            name: 项目名称
        Returns:
            项目配置字典
        """
        project = next((p for p in self.projects if p['name'] == name), None)
        if project:
            self.current_project = name
            project_path = project.get('path', '')
            
            # 设置项目目录为当前工作目录
            self.config.projects_directory = project_path
            self.config.working_directory = project_path
            
            # 更新配置中的图片目录为项目pic目录
            pic_dir = project.get('pic_dir') or os.path.join(project_path, 'pic')
            self.config.pic_directory = pic_dir
            # 确保pic目录存在
            os.makedirs(pic_dir, exist_ok=True)
            
            # 确保records目录存在
            records_dir = project.get('records_dir') or os.path.join(project_path, 'records')
            os.makedirs(records_dir, exist_ok=True)
            # 更新项目配置中的records_dir
            if 'records_dir' not in project:
                project['records_dir'] = records_dir
            
            # 确保必备的JSON文件存在
            json_files = {
                'answer_tasks.json': [],
                'daily_tasks.json': [],
                'discovery_tasks.json': [],
                'tasks.json': [],
                'workflows.json': [],
                'keywords.json': []
            }
            
            for filename, default_content in json_files.items():
                file_path = os.path.join(project_path, filename)
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(default_content, f, ensure_ascii=False, indent=2)
                    print(f"[切换项目] 已创建文件: {file_path}")
            
            # 保存当前项目到配置文件
            self._save_current_project_config()
            
            print(f"[切换项目] 项目: {name}")
            print(f"[切换项目] 项目目录: {project_path}")
            print(f"[切换项目] 图片目录: {pic_dir}")
            print(f"[切换项目] 记录目录: {records_dir}")
            
            return project
        return None
    
    def edit_project(self, name: str, version: str = None, program: str = None,
                    resolution: str = None, notes: str = None) -> bool:
        """编辑项目信息
        Args:
            name: 项目名称
            version: 新版本号
            program: 新对应程序
            resolution: 新屏幕分辨率
            notes: 新备注
        Returns:
            是否成功
        """
        # 使用安全的get方法查找项目
        project = next((p for p in self.projects if p.get('name') == name), None)
        if not project:
            return False

        if version is not None:
            project['version'] = version
        if program is not None:
            project['program'] = program
        if resolution is not None:
            project['resolution'] = resolution
        if notes is not None:
            project['notes'] = notes

        self.save_projects()
        return True

    def get_current_project(self) -> str:
        return self.current_project

    def get_all_projects(self) -> List[Dict]:
        return self.projects

    def pack_project(self, name: str, output_path: str = None) -> bool:
        """打包项目
        Args:
            name: 项目名称
            output_path: 输出zip文件路径（可选，默认使用项目目录名）
        Returns:
            是否成功
        """
        print(f"开始打包项目: {name}")

        # 使用安全的get方法查找项目
        project = next((p for p in self.projects if p.get('name') == name), None)
        if not project:
            print(f"项目不存在: {name}")
            return False

        # 获取实际的项目目录
        if name == 'default':
            # default项目使用projects目录
            project_dir = self.config.projects_directory
            print(f"default项目，使用projects目录: {project_dir}")
        else:
            project_dir = project.get('path', '')
            print(f"项目目录: {project_dir}")

        if not project_dir or not os.path.exists(project_dir):
            print(f"项目目录不存在: {project_dir}")
            return False

        # 如果未指定输出路径，使用项目目录名作为zip文件名
        if not output_path:
            project_basename = os.path.basename(project_dir)
            output_path = os.path.join(os.path.dirname(project_dir), f"{project_basename}.zip")
            print(f"未指定输出路径，使用默认路径: {output_path}")

        try:
            print(f"创建zip文件: {output_path}")
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # 打包完整的项目配置（包含所有新字段）
                project_config = {
                    'project_name': project.get('name', name),
                    'project_path': project.get('path', ''),
                    'pic_directory': project.get('pic_dir', os.path.join(project.get('path', ''), 'pic')),
                    'version': project.get('version', '1.0.0'),
                    'program': project.get('program', ''),
                    'resolution': project.get('resolution', '1920*1080'),
                    'notes': project.get('notes', ''),
                    'created_at': project.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'packed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                zf.writestr('project_config.json', json.dumps(project_config, ensure_ascii=False, indent=2))
                print("已添加项目配置")

                # 打包项目目录下的所有文件
                print("开始打包文件...")
                file_count = 0

                # 直接从项目目录开始打包，不包含父目录层级
                for root, dirs, files in os.walk(project_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # 计算相对于项目目录的路径
                        arcname = os.path.relpath(file_path, os.path.dirname(project_dir))
                        zf.write(file_path, arcname)
                        file_count += 1
                        if file_count % 10 == 0:
                            print(f"已打包 {file_count} 个文件...")

                print(f"打包完成，共 {file_count} 个文件")

            return True
        except Exception as e:
            print(f"打包失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def unpack_project(self, zip_path: str) -> Dict:
        """解压项目包
        Args:
            zip_path: zip文件路径
        Returns:
            解压后的项目配置
        """
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # 读取项目配置
                try:
                    config_data = json.loads(zf.read('project_config.json'))
                    project_name = config_data['project_name']
                    project_path = config_data['project_path']
                except Exception as e:
                    print(f"读取项目配置失败: {e}")
                    return None

                # 自动使用项目目录名作为目标解压目录
                # 获取项目目录的父目录（与其他项目同级）
                parent_dir = os.path.dirname(self.config.projects_directory)
                if not parent_dir:
                    parent_dir = os.getcwd()
                
                # 目标解压目录：父目录 + 项目目录名
                project_basename = os.path.basename(project_path)
                target_path = os.path.join(parent_dir, project_basename)
                
                print(f"自动解压到目录: {target_path}")

                # 确保目标目录存在
                os.makedirs(target_path, exist_ok=True)

                # 创建临时目录用于解压
                import tempfile
                with tempfile.TemporaryDirectory() as temp_dir:
                    print(f"创建临时目录: {temp_dir}")
                    
                    # 解压所有文件到临时目录
                    print(f"开始解压文件到临时目录")
                    zf.extractall(temp_dir)
                    print(f"解压到临时目录完成")

                    # 列出临时目录中的所有内容
                    temp_contents = os.listdir(temp_dir)
                    print(f"临时目录内容: {temp_contents}")

                    # 查找项目子目录（包含 project_config.json 或 tasks.json 的目录）
                    project_subdir = None
                    for item in temp_contents:
                        item_path = os.path.join(temp_dir, item)
                        if os.path.isdir(item_path):
                            item_contents = os.listdir(item_path)
                            if 'project_config.json' in item_contents or 'tasks.json' in item_contents:
                                project_subdir = item_path
                                break

                    # 如果找到了项目子目录，将其内容（而不是子目录本身）移动到目标目录
                    if project_subdir:
                        print(f"找到项目子目录: {project_subdir}")
                        print(f"开始将文件从临时子目录移动到目标目录: {target_path}")

                        # 直接移动项目子目录中的所有文件和目录
                        for item in os.listdir(project_subdir):
                            src_item = os.path.join(project_subdir, item)
                            dst_item = os.path.join(target_path, item)

                            if os.path.isdir(src_item):
                                # 如果目标目录已存在，合并内容
                                if os.path.exists(dst_item):
                                    # 递归移动子目录内容
                                    for sub_item in os.listdir(src_item):
                                        src_sub = os.path.join(src_item, sub_item)
                                        dst_sub = os.path.join(dst_item, sub_item)
                                        if os.path.isdir(src_sub):
                                            if os.path.exists(dst_sub):
                                                shutil.rmtree(dst_sub)
                                            shutil.move(src_sub, dst_sub)
                                        else:
                                            if os.path.exists(dst_sub):
                                                os.remove(dst_sub)
                                            shutil.move(src_sub, dst_sub)
                                else:
                                    shutil.move(src_item, dst_item)
                                print(f"已移动目录: {src_item} -> {dst_item}")
                            else:
                                # 移动文件（覆盖原有文件）
                                if os.path.exists(dst_item):
                                    os.remove(dst_item)
                                shutil.move(src_item, dst_item)
                                print(f"已移动文件: {src_item} -> {dst_item}")
                    else:
                        # 如果没有找到项目子目录，直接将临时目录中的文件移动到目标目录
                        print(f"未找到项目子目录，直接将临时目录中的文件移动到目标目录")
                        
                        for item in os.listdir(temp_dir):
                            if item == 'project_config.json':
                                continue
                            
                            src_item = os.path.join(temp_dir, item)
                            dst_item = os.path.join(target_path, item)
                            
                            if os.path.isdir(src_item):
                                # 如果目标目录已存在，先删除它
                                if os.path.exists(dst_item):
                                    shutil.rmtree(dst_item)
                                shutil.move(src_item, dst_item)
                                print(f"已移动目录: {src_item} -> {dst_item}")
                            else:
                                # 如果目标文件已存在，先删除它
                                if os.path.exists(dst_item):
                                    os.remove(dst_item)
                                shutil.move(src_item, dst_item)
                                print(f"已移动文件: {src_item} -> {dst_item}")
                
                print(f"解压完成，文件已覆盖到目标目录")

                # 创建项目配置
                new_project_dir = target_path
                # 修复图片目录路径
                new_pic_dir = os.path.join(target_path, 'pic')

                # 确保图片目录和记录目录存在
                os.makedirs(new_pic_dir, exist_ok=True)
                new_records_dir = os.path.join(target_path, 'records')
                os.makedirs(new_records_dir, exist_ok=True)

                # 检查项目是否已存在
                existing_project_index = -1
                for i, p in enumerate(self.projects):
                    if p['name'] == project_name:
                        existing_project_index = i
                        break

                # 替换配置中的路径为实际路径，并恢复所有项目信息
                new_config = {
                    'name': project_name,
                    'path': new_project_dir,
                    'pic_dir': new_pic_dir,
                    'records_dir': new_records_dir,
                    'version': config_data.get('version', '1.0.0'),
                    'program': config_data.get('program', ''),
                    'resolution': config_data.get('resolution', '1920*1080'),
                    'notes': config_data.get('notes', ''),
                    'created_at': config_data.get('created_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                    'unpacked_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

                # 如果项目已存在，更新它；否则，添加新项目
                if existing_project_index >= 0:
                    self.projects[existing_project_index] = new_config
                    print(f"项目已更新: {project_name}")
                else:
                    self.projects.append(new_config)
                    print(f"新项目已添加: {project_name}")

                self.save_projects()
                print(f"项目配置已保存")

                # 验证7个JSON文件是否存在
                json_files = ['answer_tasks.json', 'daily_tasks.json', 'discovery_tasks.json', 'keywords.json', 'projects.json', 'tasks.json', 'workflows.json']
                for json_file in json_files:
                    json_path = os.path.join(new_project_dir, json_file)
                    if os.path.exists(json_path):
                        print(f"✓ {json_file} 存在")
                    else:
                        print(f"✗ {json_file} 不存在")

                return new_config

        except Exception as e:
            print(f"解压失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _save_current_project_config(self):
        """保存当前项目到配置文件"""
        try:
            config_file = 'config.json'
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # 保存当前项目名称
            old_project = config.get('current_project', '未设置')
            config['current_project'] = self.current_project
            
            # 保存到文件
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"已保存当前项目到配置文件: {self.current_project} (旧值: {old_project})")
            
            # 验证文件是否写入成功
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    verify_config = json.load(f)
                    saved_value = verify_config.get('current_project', '读取失败')
                    print(f"验证文件写入: current_project = {saved_value}")
        except Exception as e:
            print(f"保存当前项目配置失败: {e}")
            import traceback
            traceback.print_exc()

    def _load_current_project_config(self):
        """从配置文件加载当前项目"""
        try:
            config_file = 'config.json'
            print(f"[加载项目配置] 尝试加载配置文件: {config_file}")
            print(f"[加载项目配置] 当前项目列表: {[p.get('name') for p in self.projects]}")
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                current_project = config.get('current_project', 'default')
                print(f"[加载项目配置] 从配置文件读取到: current_project = {current_project}")

                # 验证项目是否存在
                project_names = [p.get('name') for p in self.projects]
                print(f"[加载项目配置] 可用的项目名称: {project_names}")
                
                if any(p.get('name') == current_project for p in self.projects):
                    self.current_project = current_project
                    print(f"[加载项目配置] 成功加载项目: {current_project}")
                    
                    # 更新配置中的图片目录（使用安全的get方法）
                    project = next((p for p in self.projects if p.get('name') == current_project), None)
                    if project:
                        pic_dir = project.get('pic_dir') or project.get('pic_directory')
                        if pic_dir:
                            self.config.pic_directory = pic_dir
                        else:
                            # 如果项目没有pic_dir字段，生成默认路径
                            project_path = project.get('path', '')
                            self.config.pic_directory = os.path.join(project_path, 'pic') if project_path else self.config.pic_directory
                    return current_project
                else:
                    print(f"[加载项目配置] 警告：配置中的项目 '{current_project}' 不存在于项目列表中，使用default")
                    self.current_project = 'default'
                    return 'default'
            else:
                print("[加载项目配置] 配置文件不存在，使用default项目")
                self.current_project = 'default'
                return 'default'
        except Exception as e:
            print(f"[加载项目配置] 错误：加载配置失败: {e}，使用default项目")
            import traceback
            traceback.print_exc()
            self.current_project = 'default'
            return 'default'
