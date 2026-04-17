"""
工作组管理模块
移植PC端的工作组功能
"""
import os
import json
import shutil
from datetime import datetime
from kivy.logger import Logger


class WorkgroupManager:
    """工作组管理类"""
    
    def __init__(self, config, network_manager):
        self.config = config
        self.network = network_manager
        
        # 工作组信息
        self.workgroup_id = None
        self.workgroup_name = None
        self.role = None  # 'admin', 'member'
        self.sync_dir = None
        self.last_sync = None
        
        # 暂断状态
        self.disabled = False
        self.paused_until = None
        
        # 命令列表
        self.cmd_list = []
        
        # 命令模板（从PC端移植）
        self.cmd_templates = {}
        
        # 数据文件路径
        self.data_file = os.path.join(self.config.data_dir, 'workgroup_state.json')
        
        # 加载命令模板
        self._load_cmd_templates()
        
        Logger.info('WorkgroupManager: 初始化成功')
        
    def _load_cmd_templates(self):
        """加载命令模板（从PC端workgroup_state.json移植）"""
        # 这里只定义模板结构，具体Python代码在执行时从模板文件加载
        self.cmd_templates = {
            '调动': {
                'type': 'python_script',
                'description': '调动：执行Python脚本完成操作',
                'has_multi_coords': False,
                'has_auto_input': True,
                'is_python_template': True
            },
            '走到': {
                'type': 'python_script',
                'description': '走到：按新流程执行图片查找点击和文本参数输入',
                'has_multi_coords': False,
                'has_auto_input': True,
                'is_python_template': True
            },
            '预约': {
                'type': 'python_script',
                'description': '预约：点击指定坐标并执行工作流',
                'has_multi_coords': False,
                'has_auto_input': False,
                'is_python_template': True
            },
            '集结': {
                'type': 'python_script',
                'description': '集结：点击指定坐标并执行工作流',
                'has_multi_coords': False,
                'has_auto_input': False,
                'is_python_template': True
            },
            '集火': {
                'type': 'python_script',
                'description': '集火：点击坐标并自动输入坐标参数',
                'has_multi_coords': False,
                'has_auto_input': True,
                'is_python_template': True
            }
        }
        
    def load_from_local(self):
        """从本地加载工作组状态"""
        if not os.path.exists(self.data_file):
            return False
            
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 工作组信息
            wg_info = data.get('wg_info', {})
            self.workgroup_id = wg_info.get('id')
            self.workgroup_name = wg_info.get('name')
            self.role = wg_info.get('role')
            self.sync_dir = wg_info.get('sync_dir')
            
            last_sync_str = wg_info.get('last_sync')
            if last_sync_str:
                self.last_sync = datetime.fromisoformat(last_sync_str)
                
            self.disabled = wg_info.get('disabled', False)
            
            paused_until_str = wg_info.get('paused_until')
            if paused_until_str:
                self.paused_until = datetime.fromisoformat(paused_until_str)
                
            # 命令列表
            self.cmd_list = data.get('cmd_list', [])
            
            # 命令模板（合并）
            cmd_templates = data.get('cmd_templates', {})
            self.cmd_templates.update(cmd_templates)
            
            Logger.info('WorkgroupManager: 本地状态加载成功')
            return True
            
        except Exception as e:
            Logger.error(f'WorkgroupManager: 本地状态加载失败 - {e}')
            return False
            
    def save_to_local(self):
        """保存工作组状态到本地"""
        try:
            data = {
                'wg_info': {
                    'id': self.workgroup_id,
                    'name': self.workgroup_name,
                    'role': self.role,
                    'sync_dir': self.sync_dir,
                    'last_sync': self.last_sync.isoformat() if self.last_sync else None,
                    'disabled': self.disabled,
                    'paused_until': self.paused_until.isoformat() if self.paused_until else None
                },
                'cmd_list': self.cmd_list,
                'cmd_templates': self.cmd_templates
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            Logger.info('WorkgroupManager: 本地状态保存成功')
            return True
            
        except Exception as e:
            Logger.error(f'WorkgroupManager: 本地状态保存失败 - {e}')
            return False
            
    def join(self, workgroup_id, password=None):
        """加入工作组"""
        result = self.network.join_workgroup(workgroup_id, password)
        
        if not result:
            return False, '加入工作组失败'
            
        if result.get('success'):
            wg_data = result.get('workgroup', {})
            
            self.workgroup_id = workgroup_id
            self.workgroup_name = wg_data.get('name')
            self.role = wg_data.get('role', 'member')
            
            # 设置同步目录
            self.sync_dir = os.path.join(
                self.config.workgroup_directory,
                str(workgroup_id)
            )
            if not os.path.exists(self.sync_dir):
                os.makedirs(self.sync_dir)
                
            # 同步数据
            self.sync()
            
            self.save_to_local()
            
            Logger.info(f'WorkgroupManager: 加入工作组成功 - {self.workgroup_name}')
            return True, f'已加入工作组：{self.workgroup_name}'
        else:
            return False, result.get('message', '加入失败')
            
    def leave(self):
        """退出工作组"""
        if not self.workgroup_id:
            return False, '未加入任何工作组'
            
        result = self.network.leave_workgroup(self.workgroup_id)
        
        # 无论服务器是否成功，都清除本地状态
        self.workgroup_id = None
        self.workgroup_name = None
        self.role = None
        self.sync_dir = None
        self.cmd_list = []
        self.disabled = False
        self.paused_until = None
        
        self.save_to_local()
        
        Logger.info('WorkgroupManager: 已退出工作组')
        return True, '已退出工作组'
        
    def sync(self):
        """同步工作组数据"""
        if not self.workgroup_id:
            return False, '未加入工作组'
            
        # 从服务器同步命令列表
        result = self.network.get_workgroup_commands(self.workgroup_id)
        
        if result and result.get('success'):
            self.cmd_list = result.get('commands', [])
            
            # 同步图片文件
            self._sync_images()
            
            self.last_sync = datetime.now()
            self.save_to_local()
            
            Logger.info('WorkgroupManager: 同步成功')
            return True, '同步成功'
        else:
            Logger.error('WorkgroupManager: 同步失败')
            return False, '同步失败'
            
    def _sync_images(self):
        """同步图片文件"""
        if not self.sync_dir:
            return
            
        # 创建图片目录
        pic_dir = os.path.join(self.sync_dir, 'pic')
        if not os.path.exists(pic_dir):
            os.makedirs(pic_dir)
            
        # TODO: 从服务器下载图片文件
        # 这里需要实现图片同步逻辑
        
    def pause(self, hours=3):
        """暂断工作组"""
        from datetime import timedelta
        self.paused_until = datetime.now() + timedelta(hours=hours)
        self.disabled = True
        self.save_to_local()
        
        Logger.info(f'WorkgroupManager: 暂断{hours}小时')
        return True, f'已暂断{hours}小时'
        
    def cancel_pause(self):
        """取消暂断"""
        self.paused_until = None
        self.disabled = False
        self.save_to_local()
        
        Logger.info('WorkgroupManager: 已取消暂断')
        return True, '已取消暂断'
        
    def is_paused(self):
        """检查是否处于暂断状态"""
        if not self.paused_until:
            return False
            
        if datetime.now() >= self.paused_until:
            self.paused_until = None
            self.disabled = False
            self.save_to_local()
            return False
            
        return True
        
    def is_joined(self):
        """检查是否已加入工作组"""
        return self.workgroup_id is not None
        
    def get_cmd_list(self):
        """获取命令列表"""
        if self.is_joined():
            # 加入工作组，使用服务端命令列表
            return self.cmd_list
        else:
            # 未加入工作组，使用本地命令列表
            local_file = os.path.join(self.config.data_dir, 'local_commands.json')
            if os.path.exists(local_file):
                try:
                    with open(local_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except:
                    pass
            return []
            
    def add_command(self, command):
        """添加命令到列表"""
        self.cmd_list.append(command)
        self.save_to_local()
        
    def remove_command(self, index):
        """从列表移除命令"""
        if 0 <= index < len(self.cmd_list):
            self.cmd_list.pop(index)
            self.save_to_local()
            
    def clear_commands(self):
        """清空命令列表"""
        self.cmd_list = []
        self.save_to_local()
        
    def get_template(self, template_name):
        """获取命令模板"""
        return self.cmd_templates.get(template_name)
        
    def get_template_names(self):
        """获取所有模板名称"""
        return list(self.cmd_templates.keys())
