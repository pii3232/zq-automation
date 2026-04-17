"""
命令执行模块
执行指挥标签的命令模板
"""
import os
import time
import threading
from kivy.logger import Logger
from kivy.clock import Clock


class CommandExecutor:
    """命令执行器"""
    
    def __init__(self, app):
        self.app = app
        self.running = False
        self.paused = False
        self.stop_flag = False
        self.current_command = None
        self.current_index = 0
        
        # 执行日志
        self.log_callback = None
        self.status_callback = None
        
        # 执行线程
        self.thread = None
        
    def execute_command_list(self, commands, log_callback=None, status_callback=None):
        """执行命令列表"""
        if self.running:
            return False, '已有命令在执行中'
            
        self.running = True
        self.paused = False
        self.stop_flag = False
        self.log_callback = log_callback
        self.status_callback = status_callback
        
        # 启动执行线程
        self.thread = threading.Thread(
            target=self._execute_thread,
            args=(commands,),
            daemon=True
        )
        self.thread.start()
        
        return True, '开始执行'
        
    def _execute_thread(self, commands):
        """执行线程"""
        try:
            total = len(commands)
            
            for i, cmd in enumerate(commands):
                if self.stop_flag:
                    self._log('执行已停止')
                    break
                    
                while self.paused:
                    time.sleep(0.5)
                    if self.stop_flag:
                        break
                        
                if self.stop_flag:
                    break
                    
                self.current_command = cmd
                self.current_index = i
                
                # 更新状态
                if self.status_callback:
                    Clock.schedule_once(
                        lambda dt: self.status_callback(f'执行中 ({i+1}/{total})'),
                        0
                    )
                    
                # 检查是否需要在执行前自动进入悬窗模式
                if self.app.config.auto_float_before_exec:
                    # 获取下一个命令的执行时间
                    next_exec_time = self._get_command_exec_time(cmd)
                    if next_exec_time and next_exec_time <= self.app.config.auto_float_seconds:
                        Clock.schedule_once(lambda dt: self.app.enter_float_mode(), 0)
                        
                # 执行命令
                success, message = self._execute_command(cmd)
                
                if success:
                    self._log(f'[{i+1}/{total}] {cmd.get("name", "命令")} 执行成功')
                else:
                    self._log(f'[{i+1}/{total}] {cmd.get("name", "命令")} 执行失败: {message}')
                    
            # 执行完成
            self.running = False
            self.current_command = None
            
            if self.status_callback:
                Clock.schedule_once(lambda dt: self.status_callback('执行完成'), 0)
                
        except Exception as e:
            Logger.error(f'CommandExecutor: 执行出错 - {e}')
            self.running = False
            if self.status_callback:
                Clock.schedule_once(lambda dt: self.status_callback(f'执行出错: {e}'), 0)
                
    def _execute_command(self, cmd):
        """执行单个命令"""
        template_name = cmd.get('template')
        params = cmd.get('params', {})
        
        # 获取模板
        template = self.app.workgroup_manager.get_template(template_name)
        if not template:
            return False, f'模板不存在: {template_name}'
            
        # 检查是否是Python脚本模板
        if template.get('is_python_template'):
            return self._execute_python_template(template, params)
        else:
            return False, '不支持的模板类型'
            
    def _execute_python_template(self, template, params):
        """执行Python脚本模板"""
        python_code = template.get('python_code', '')
        
        if not python_code:
            return False, '模板代码为空'
            
        # 替换参数
        workgroup_id = self.app.workgroup_manager.workgroup_id or 'local'
        coord_params = params.get('coord_params', '0.0')
        
        python_code = python_code.replace('{{workgroup_id}}', str(workgroup_id))
        python_code = python_code.replace('{{coord_params}}', coord_params)
        
        # 准备执行环境
        exec_globals = {
            'os': os,
            'time': time,
            'pyautogui': self._get_pyautogui_bridge(),
            'cv2': self._get_cv2_bridge(),
            'np': __import__('numpy'),
            'workgroup_id': workgroup_id,
            'coord_params': coord_params
        }
        
        try:
            # 执行代码
            exec(python_code, exec_globals)
            return True, '执行成功'
        except Exception as e:
            Logger.error(f'CommandExecutor: Python执行出错 - {e}')
            return False, str(e)
            
    def _get_pyautogui_bridge(self):
        """获取pyautogui桥接对象"""
        class PyAutoGUIBridge:
            """PyAutoGUI桥接类，模拟PC端pyautogui接口"""
            
            def __init__(self, executor):
                self.executor = executor
                self.app = executor.app
                
            def screenshot(self):
                """截图"""
                # 返回PIL Image对象
                if self.app.android_bridge:
                    path = self.app.android_bridge.take_screenshot()
                    if path:
                        from PIL import Image
                        return Image.open(path)
                return None
                
            def click(self, x, y):
                """点击"""
                if self.app.android_bridge:
                    return self.app.android_bridge.tap(x, y)
                return False
                
            def moveTo(self, x, y):
                """移动鼠标（Android不支持）"""
                pass
                
            def dragTo(self, x, y):
                """拖拽"""
                # TODO: 实现拖拽
                pass
                
        return PyAutoGUIBridge(self)
        
    def _get_cv2_bridge(self):
        """获取cv2桥接"""
        # 直接使用OpenCV
        return __import__('cv2')
        
    def _get_command_exec_time(self, cmd):
        """获取命令预计执行时间（秒）"""
        # 简单估算，实际可以根据命令类型计算
        return 10  # 默认10秒
        
    def _log(self, message):
        """记录日志"""
        Logger.info(f'CommandExecutor: {message}')
        if self.log_callback:
            Clock.schedule_once(lambda dt: self.log_callback(message), 0)
            
    def pause(self):
        """暂停执行"""
        self.paused = True
        self._log('执行已暂停')
        
    def resume(self):
        """恢复执行"""
        self.paused = False
        self._log('执行已恢复')
        
    def stop(self):
        """停止执行"""
        self.stop_flag = True
        self.paused = False
        self._log('正在停止执行...')
        
    def is_running(self):
        """检查是否正在执行"""
        return self.running
        
    def is_paused(self):
        """检查是否暂停"""
        return self.paused
