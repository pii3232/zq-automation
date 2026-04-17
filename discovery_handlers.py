"""
发现即点标签页处理函数 - Tkinter版本
本文件包含发现即点标签页的所有处理函数
"""

import os
import json
from datetime import datetime
import threading
import time

from tkinter import messagebox, filedialog

# 导入消息框函数
from tabs import msg_warning, msg_information, msg_critical, msg_question


def on_discovery_tasks_main_switch_changed(self):
    """发现即点总开关变化"""
    self.save_discovery_tasks_global_settings()


def on_discovery_loop_all_changed(self):
    """发现即点循环执行开关变化"""
    self.save_discovery_tasks_global_settings()


def on_discovery_repeat_count_changed(self):
    """发现即点执行遍数变化"""
    self.save_discovery_tasks_global_settings()


def on_discovery_time_mode_changed(self):
    """发现即点时间模式变化"""
    self.save_discovery_tasks_global_settings()


def on_discovery_schedule_time_changed(self, datetime):
    """发现即点定时执行时间变化"""
    self.save_discovery_tasks_global_settings()


def on_discovery_delay_minutes_changed(self):
    """发现即点延时执行分钟数变化"""
    self.save_discovery_tasks_global_settings()


def save_discovery_tasks_global_settings(self):
    """保存发现即点全局设置"""
    try:
        # 保存总开关状态
        if hasattr(self, 'discovery_tasks_main_switch_var'):
            self.config.discovery_tasks_main_switch_enabled = self.discovery_tasks_main_switch_var.get()
        
        # 保存循环执行状态
        if hasattr(self, 'discovery_loop_all_var'):
            self.config.discovery_tasks_loop_enabled = self.discovery_loop_all_var.get()
        
        # 保存执行遍数
        if hasattr(self, 'discovery_repeat_count_var'):
            self.config.discovery_tasks_repeat_count = self.discovery_repeat_count_var.get()
        
        # 保存时间模式
        if hasattr(self, 'discovery_time_mode_var'):
            self.config.discovery_tasks_time_mode = self.discovery_time_mode_var.get()
        
        self.config.save()
        
    except Exception as e:
        print(f"保存发现即点全局设置失败: {e}")


def load_discovery_tasks_global_settings(self):
    """加载发现即点全局设置"""
    try:
        # 加载总开关
        if hasattr(self, 'discovery_tasks_main_switch_var'):
            self.discovery_tasks_main_switch_var.set(
                getattr(self.config, 'discovery_tasks_main_switch_enabled', True)
            )
        
        # 加载循环执行
        if hasattr(self, 'discovery_loop_all_var'):
            self.discovery_loop_all_var.set(
                getattr(self.config, 'discovery_tasks_loop_enabled', False)
            )
        
        # 加载执行遍数
        if hasattr(self, 'discovery_repeat_count_var'):
            self.discovery_repeat_count_var.set(
                getattr(self.config, 'discovery_tasks_repeat_count', 1)
            )
        
        # 加载时间模式
        if hasattr(self, 'discovery_time_mode_var'):
            time_mode = getattr(self.config, 'discovery_tasks_time_mode', 'none')
            self.discovery_time_mode_var.set(time_mode)
        
    except Exception as e:
        print(f"加载发现即点全局设置失败: {e}")


def add_discovery_task(self):
    """添加发现即点任务"""
    try:
        if not hasattr(self, 'workflow_manager'):
            msg_warning(self, "警告", "工作流管理器未初始化")
            return
        
        workflows = self.workflow_manager.get_all_workflows()
        if not workflows:
            msg_warning(self, "警告", "没有可用的工作流,请先创建工作流")
            return
        
        from tabs import DiscoveryTaskEditDialog
        dialog = DiscoveryTaskEditDialog(workflows=workflows, parent=self)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            if not hasattr(self, 'discovery_tasks'):
                self.discovery_tasks = []
            
            # 生成唯一ID
            task_id = f"discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.discovery_tasks)}"
            dialog.result['id'] = task_id
            dialog.result['status'] = '待执行'
            
            self.discovery_tasks.append(dialog.result)
            self.save_discovery_tasks()
            self.load_discovery_tasks_list()
            
            workflow_text = dialog.result.get('workflow', '未知工作流')
            self.add_status_message(f"添加发现即点任务: {workflow_text}")
            
    except Exception as e:
        print(f"添加发现即点任务失败: {e}")
        import traceback
        traceback.print_exc()
        msg_critical(self, "错误", f"添加发现即点任务失败: {e}")


def edit_discovery_task(self):
    """编辑发现即点任务"""
    try:
        selection = self.discovery_task_table.selection()
        if not selection:
            msg_warning(self, "警告", "请先选择一个任务")
            return
        
        item = selection[0]
        index = self.discovery_task_table.index(item)
        
        if not hasattr(self, 'discovery_tasks') or index >= len(self.discovery_tasks):
            return
        
        task = self.discovery_tasks[index]
        workflows = self.workflow_manager.get_all_workflows() if hasattr(self, 'workflow_manager') else []
        
        from tabs import DiscoveryTaskEditDialog
        dialog = DiscoveryTaskEditDialog(task=task, workflows=workflows, parent=self)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            # 保留原有ID
            dialog.result['id'] = task.get('id')
            self.discovery_tasks[index] = dialog.result
            self.save_discovery_tasks()
            self.load_discovery_tasks_list()
            
            workflow_text = dialog.result.get('workflow', '未知工作流')
            self.add_status_message(f"编辑发现即点任务: {workflow_text}")
            
    except Exception as e:
        print(f"编辑发现即点任务失败: {e}")
        msg_critical(self, "错误", f"编辑发现即点任务失败: {e}")


def delete_discovery_task(self):
    """删除发现即点任务"""
    try:
        selection = self.discovery_task_table.selection()
        if not selection:
            msg_warning(self, "警告", "请先选择一个任务")
            return
        
        if msg_question(self, "确认删除", "确定要删除选中的发现即点任务吗?"):
            item = selection[0]
            index = self.discovery_task_table.index(item)
            
            if hasattr(self, 'discovery_tasks') and index < len(self.discovery_tasks):
                task = self.discovery_tasks.pop(index)
                self.save_discovery_tasks()
                self.load_discovery_tasks_list()
                self.add_status_message(f"删除发现即点任务: {task.get('workflow', '未知')}")
                
    except Exception as e:
        print(f"删除发现即点任务失败: {e}")
        msg_critical(self, "错误", f"删除发现即点任务失败: {e}")


def move_discovery_task_up(self):
    """发现即点任务上移"""
    try:
        selection = self.discovery_task_table.selection()
        if not selection:
            return
        
        item = selection[0]
        row = self.discovery_task_table.index(item)
        
        if row > 0 and hasattr(self, 'discovery_tasks'):
            self.discovery_tasks[row], self.discovery_tasks[row-1] = \
                self.discovery_tasks[row-1], self.discovery_tasks[row]
            self.save_discovery_tasks()
            self.load_discovery_tasks_list()
            
    except Exception as e:
        print(f"发现即点任务上移失败: {e}")


def move_discovery_task_down(self):
    """发现即点任务下移"""
    try:
        selection = self.discovery_task_table.selection()
        if not selection:
            return
        
        item = selection[0]
        row = self.discovery_task_table.index(item)
        
        if hasattr(self, 'discovery_tasks') and row < len(self.discovery_tasks) - 1:
            self.discovery_tasks[row], self.discovery_tasks[row+1] = \
                self.discovery_tasks[row+1], self.discovery_tasks[row]
            self.save_discovery_tasks()
            self.load_discovery_tasks_list()
            
    except Exception as e:
        print(f"发现即点任务下移失败: {e}")


def execute_discovery_tasks_now(self):
    """立即执行发现即点任务"""
    try:
        if not hasattr(self, 'discovery_tasks') or not self.discovery_tasks:
            msg_warning(self, "警告", "没有可执行的发现即点任务")
            return
        
        # 检查是否有启用的任务
        enabled_tasks = [t for t in self.discovery_tasks if t.get('enabled', True)]
        if not enabled_tasks:
            msg_warning(self, "警告", "没有启用的发现即点任务")
            return
        
        # 延迟3秒后执行
        self.root.after(3000, self._execute_discovery_tasks_sequence)
        
    except Exception as e:
        print(f"执行发现即点任务失败: {e}")
        import traceback
        traceback.print_exc()
        msg_critical(self, "错误", f"执行发现即点任务失败: {e}")


def _execute_discovery_tasks_sequence(self):
    """执行发现即点任务序列(内部) - 持续循环执行"""
    try:
        if not hasattr(self, 'discovery_tasks') or not self.discovery_tasks:
            return
        
        # 获取启用的任务
        enabled_tasks = [t for t in self.discovery_tasks if t.get('enabled', True)]
        if not enabled_tasks:
            self.add_status_message("没有启用的发现即点任务")
            return
        
        # 设置循环标志
        self.discovery_tasks_running = True
        self.add_status_message("发现即点系统开始持续循环执行...")
        
        # 在新线程中执行
        def run_tasks():
            # 持续循环执行,直到被停止
            loop_count = 0
            while self.discovery_tasks_running:
                loop_count += 1
                if loop_count > 1:
                    self.add_status_message(f"开始第 {loop_count} 轮循环执行...")
                
                # 按顺序执行每个启用的任务
                for i, task in enumerate(enabled_tasks):
                    if not self.discovery_tasks_running:
                        break
                        
                    workflow_name = task.get('workflow', '')
                    repeat = task.get('repeat_count', 1)
                    
                    # 更新状态为"正在执行"
                    task['status'] = '正在执行'
                    self.root.after(0, self.load_discovery_tasks_list)
                    
                    # 在状态栏显示正在执行的任务名称
                    self.add_status_message(f"【发现即点】正在执行 {i+1}/{len(enabled_tasks)}: {workflow_name}")
                    
                    # 快速执行工作流
                    for r in range(repeat):
                        if not self.discovery_tasks_running:
                            break
                        
                        # 执行工作流,传递停止检查函数
                        if hasattr(self, 'task_manager'):
                            self.task_manager._execute_workflow(
                                workflow_name,
                                stop_check_fn=lambda: not self.discovery_tasks_running
                            )
                    
                    # 执行完毕后更新状态为"待执行"
                    task['status'] = '待执行'
                    self.root.after(0, self.load_discovery_tasks_list)
                    
                    # 更新最后执行时间
                    task['last_executed'] = datetime.now().isoformat()
                    
                    # 显示完成
                    self.add_status_message(f"【发现即点】已完成: {workflow_name}")
                
                # 保存任务状态
                self.save_discovery_tasks()
            
            # 停止后重置所有任务状态
            for task in enabled_tasks:
                task['status'] = '待执行'
            self.root.after(0, self.load_discovery_tasks_list)
            self.save_discovery_tasks()
            
            self.add_status_message("发现即点系统循环执行已停止")
        
        thread = threading.Thread(target=run_tasks, daemon=True)
        thread.start()
        
    except Exception as e:
        print(f"执行发现即点任务序列失败: {e}")
        import traceback
        traceback.print_exc()
        self.add_status_message(f"执行发现即点系统失败: {e}")
    finally:
        if hasattr(self, 'discovery_tasks_running'):
            pass


def stop_all_discovery_tasks(self):
    """停止所有发现即点任务"""
    try:
        self.discovery_tasks_running = False
        self.add_status_message("发现即点系统已停止")
    except Exception as e:
        print(f"停止发现即点系统失败: {e}")


def save_discovery_tasks(self):
    """保存发现即点任务"""
    try:
        if hasattr(self, 'discovery_tasks'):
            tasks_file = os.path.join(self.config.projects_directory, 'discovery_tasks.json')
            with open(tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self.discovery_tasks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存发现即点任务失败: {e}")


def load_discovery_tasks_list(self):
    """加载发现即点任务列表显示"""
    try:
        # 清空表格
        for item in self.discovery_task_table.get_children():
            self.discovery_task_table.delete(item)
        
        # 尝试从文件加载
        tasks_file = os.path.join(self.config.projects_directory, 'discovery_tasks.json')
        if os.path.exists(tasks_file):
            with open(tasks_file, 'r', encoding='utf-8') as f:
                self.discovery_tasks = json.load(f)
        elif not hasattr(self, 'discovery_tasks'):
            self.discovery_tasks = []
        
        for task in self.discovery_tasks:
            enabled = '是' if task.get('enabled', True) else '否'
            workflow = task.get('workflow', '未知工作流')
            repeat_count = task.get('repeat_count', 1)
            status = task.get('status', '待执行')
            
            self.discovery_task_table.insert('', tk.END, values=(enabled, workflow, repeat_count, status))
            
    except Exception as e:
        print(f"加载发现即点任务列表失败: {e}")


def on_discovery_task_item_changed(self, item):
    """发现即点任务项复选框变化处理"""
    try:
        # Tkinter版本使用不同的方式处理
        pass
    except Exception as e:
        print(f"发现即点任务项变化处理失败: {e}")


def save_discovery_tasks_to_file(self):
    """保存发现即点任务列表到文件"""
    try:
        if not hasattr(self, 'discovery_tasks'):
            msg_warning(self, "警告", "没有可保存的发现即点任务")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension='.json',
            filetypes=[('JSON文件', '*.json')],
            parent=self.root
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.discovery_tasks, f, ensure_ascii=False, indent=2)
            msg_information(self, "成功", "发现即点任务列表保存成功")
            
    except Exception as e:
        msg_critical(self, "错误", f"保存发现即点任务列表失败: {e}")


def load_discovery_tasks_from_file(self):
    """从文件加载发现即点任务列表"""
    try:
        filename = filedialog.askopenfilename(
            filetypes=[('JSON文件', '*.json')],
            parent=self.root
        )
        if filename:
            with open(filename, 'r', encoding='utf-8') as f:
                self.discovery_tasks = json.load(f)
            self.save_discovery_tasks()
            self.load_discovery_tasks_list()
            msg_information(self, "成功", "发现即点任务列表加载成功")
            
    except Exception as e:
        msg_critical(self, "错误", f"加载发现即点任务列表失败: {e}")


def clear_all_discovery_tasks(self):
    """清空所有发现即点任务"""
    try:
        if msg_question(self, "确认清空", "确定要清空所有发现即点任务吗?"):
            if hasattr(self, 'discovery_tasks'):
                self.discovery_tasks.clear()
                self.save_discovery_tasks()
                self.load_discovery_tasks_list()
                msg_information(self, "成功", "发现即点任务已清空")
                
    except Exception as e:
        msg_critical(self, "错误", f"清空发现即点任务失败: {e}")


# 需要导入tkinter
import tkinter as tk
