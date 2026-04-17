"""
配置管理模块
"""
import os
import json
from kivy.logger import Logger


class Config:
    """配置管理类"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.data_dir = self._get_data_dir()
        self.config_path = os.path.join(self.data_dir, config_file)
        
        # 默认配置
        self.defaults = {
            'server_url': 'https://9793tg1lo456.vicp.fun',
            'local_server_ip': '192.168.1.100',
            'local_server_port': '5000',
            'peanut_shell_domain': '9793tg1lo456.vicp.fun',
            'connection_priority': 'peanut_direct,local_direct,peanut_domain',
            'pic_directory': 'pic',
            'workgroup_directory': 'workgroups',
            'global_similarity': 80,
            'float_window_size': 25,
            'auto_float_before_exec': True,
            'auto_float_seconds': 10
        }
        
        # 加载配置
        self.config = self._load_config()
        
        # 应用配置到属性
        self._apply_config()
        
    def _get_data_dir(self):
        """获取数据目录"""
        # Android: /data/data/org.zq.zqautomation/files/
        # PC: 当前目录/data/
        if 'ANDROID_ARGUMENT' in os.environ:
            # Android环境
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            return PythonActivity.mActivity.getFilesDir().getAbsolutePath()
        else:
            # PC环境
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            return data_dir
            
    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    Logger.info(f'Config: 配置加载成功 - {self.config_path}')
                    return config
            except Exception as e:
                Logger.error(f'Config: 配置加载失败 - {e}')
                return self.defaults.copy()
        else:
            Logger.info('Config: 配置文件不存在，使用默认配置')
            return self.defaults.copy()
            
    def _apply_config(self):
        """应用配置到属性"""
        self.server_url = self.config.get('server_url', self.defaults['server_url'])
        self.local_server_ip = self.config.get('local_server_ip', self.defaults['local_server_ip'])
        self.local_server_port = self.config.get('local_server_port', self.defaults['local_server_port'])
        self.peanut_shell_domain = self.config.get('peanut_shell_domain', self.defaults['peanut_shell_domain'])
        self.connection_priority = self.config.get('connection_priority', self.defaults['connection_priority']).split(',')
        self.pic_directory = os.path.join(self.data_dir, self.config.get('pic_directory', self.defaults['pic_directory']))
        self.workgroup_directory = os.path.join(self.data_dir, self.config.get('workgroup_directory', self.defaults['workgroup_directory']))
        self.global_similarity = self.config.get('global_similarity', self.defaults['global_similarity'])
        self.float_window_size = self.config.get('float_window_size', self.defaults['float_window_size'])
        self.auto_float_before_exec = self.config.get('auto_float_before_exec', self.defaults['auto_float_before_exec'])
        self.auto_float_seconds = self.config.get('auto_float_seconds', self.defaults['auto_float_seconds'])
        
        # 确保目录存在
        if not os.path.exists(self.pic_directory):
            os.makedirs(self.pic_directory)
        if not os.path.exists(self.workgroup_directory):
            os.makedirs(self.workgroup_directory)
            
    def save(self):
        """保存配置"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            Logger.info('Config: 配置保存成功')
        except Exception as e:
            Logger.error(f'Config: 配置保存失败 - {e}')
            
    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """设置配置项"""
        self.config[key] = value
        self._apply_config()
        
    @staticmethod
    def create_default():
        """创建默认配置"""
        return Config()
