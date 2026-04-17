"""
激活管理模块
移植PC端的激活功能
"""
import os
import json
from datetime import datetime, timedelta
from kivy.logger import Logger
from kivy.clock import Clock


class ActivationManager:
    """激活管理类"""
    
    def __init__(self, config, network_manager):
        self.config = config
        self.network = network_manager
        
        # 用户信息
        self.username = None
        self.password = None
        self.save_password = False
        
        # 激活信息
        self.is_active = False
        self.expires_at = None
        self.days_remaining = 0
        
        # 每日试用
        self.daily_trial_date = None
        self.daily_trial_used = False
        self.daily_trial_minutes = 60  # 每天1小时试用
        
        # 暂断功能
        self.paused_until = None
        
        # 数据文件路径
        self.data_file = os.path.join(self.config.data_dir, 'activation.json')
        
        # 自动同步定时器
        self.auto_sync_event = None
        
        Logger.info('ActivationManager: 初始化成功')
        
    def load_from_local(self):
        """从本地加载激活配置"""
        if not os.path.exists(self.data_file):
            return False
            
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.username = data.get('username')
            self.password = data.get('password') if data.get('save_password') else None
            self.save_password = data.get('save_password', False)
            self.is_active = data.get('is_active', False)
            
            expires_at_str = data.get('expires_at')
            if expires_at_str:
                self.expires_at = datetime.fromisoformat(expires_at_str)
                
            self.daily_trial_date = data.get('daily_trial_date')
            self.daily_trial_used = data.get('daily_trial_used', False)
            
            paused_until_str = data.get('paused_until')
            if paused_until_str:
                self.paused_until = datetime.fromisoformat(paused_until_str)
                
            self._update_days_remaining()
            
            Logger.info('ActivationManager: 本地配置加载成功')
            return True
            
        except Exception as e:
            Logger.error(f'ActivationManager: 本地配置加载失败 - {e}')
            return False
            
    def save_to_local(self):
        """保存激活配置到本地"""
        try:
            data = {
                'username': self.username,
                'password': self.password if self.save_password else None,
                'save_password': self.save_password,
                'is_active': self.is_active,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
                'daily_trial_date': self.daily_trial_date,
                'daily_trial_used': self.daily_trial_used,
                'paused_until': self.paused_until.isoformat() if self.paused_until else None
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            Logger.info('ActivationManager: 本地配置保存成功')
            return True
            
        except Exception as e:
            Logger.error(f'ActivationManager: 本地配置保存失败 - {e}')
            return False
            
    def register(self, username, password, invite_code=None):
        """用户注册"""
        data = {
            'username': username,
            'password': password
        }
        if invite_code:
            data['invite_code'] = invite_code
            
        result, error = self.network.post('/api/register', data)
        
        if error:
            return False, error
            
        if result and result.get('success'):
            Logger.info(f'ActivationManager: 注册成功 - {username}')
            return True, '注册成功'
        else:
            return False, result.get('message', '注册失败') if result else '注册失败'
            
    def login(self, username, password, save_password=False):
        """用户登录"""
        data = {
            'username': username,
            'password': password
        }
        
        result, error = self.network.post('/api/login', data)
        
        if error:
            return False, error
            
        if result and result.get('success'):
            self.username = username
            self.password = password if save_password else None
            self.save_password = save_password
            
            # 同步激活状态
            self.sync_from_server()
            
            # 保存到本地
            self.save_to_local()
            
            # 启动自动同步
            self.start_auto_sync()
            
            Logger.info(f'ActivationManager: 登录成功 - {username}')
            return True, '登录成功'
        else:
            return False, result.get('message', '登录失败') if result else '登录失败'
            
    def logout(self):
        """退出登录"""
        self.username = None
        self.password = None
        self.save_password = False
        self.is_active = False
        self.expires_at = None
        self.days_remaining = 0
        
        # 停止自动同步
        self.stop_auto_sync()
        
        # 清空本地配置
        self.save_to_local()
        
        Logger.info('ActivationManager: 已退出登录')
        
    def sync_from_server(self):
        """从服务器同步激活状态"""
        if not self.username:
            return False
            
        data = {'username': self.username}
        result, error = self.network.post('/api/activation/sync', data)
        
        if error:
            Logger.error(f'ActivationManager: 同步失败 - {error}')
            return False
            
        if result and result.get('success'):
            activation_data = result.get('data', {})
            
            self.is_active = activation_data.get('active', False)
            
            expires_at_str = activation_data.get('expires_at')
            if expires_at_str:
                self.expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                
            self._update_days_remaining()
            
            # 更新每日试用状态
            today = datetime.now().strftime('%Y-%m-%d')
            if self.daily_trial_date != today:
                self.daily_trial_date = today
                self.daily_trial_used = False
                
            self.save_to_local()
            
            Logger.info('ActivationManager: 同步成功')
            return True
        else:
            Logger.error(f'ActivationManager: 同步失败 - {result.get("message") if result else "未知错误"}')
            return False
            
    def activate(self, code, invite_code=None):
        """使用激活码激活"""
        if not self.username:
            return False, '请先登录'
            
        data = {
            'username': self.username,
            'code': code
        }
        if invite_code:
            data['invite_code'] = invite_code
            
        result, error = self.network.post('/api/activation/activate', data)
        
        if error:
            return False, error
            
        if result and result.get('success'):
            # 更新激活状态
            expires_at_str = result.get('expires_at')
            if expires_at_str:
                self.expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                
            self.days_remaining = result.get('days_remaining', 0)
            self.is_active = True
            
            self.save_to_local()
            
            Logger.info(f'ActivationManager: 激活成功，剩余{self.days_remaining}天')
            return True, f'激活成功！剩余{self.days_remaining}天'
        else:
            return False, result.get('message', '激活失败') if result else '激活失败'
            
    def is_activated(self):
        """检查是否已激活"""
        if not self.is_active or not self.expires_at:
            return False
            
        # 检查是否过期
        if datetime.now() > self.expires_at:
            self.is_active = False
            return False
            
        # 检查是否被暂断
        if self.paused_until and datetime.now() < self.paused_until:
            return False
            
        return True
        
    def can_use_daily_trial(self):
        """检查是否可以使用每日试用"""
        # 已激活用户不需要试用
        if self.is_activated():
            return False
            
        # 检查今天是否已使用试用
        today = datetime.now().strftime('%Y-%m-%d')
        if self.daily_trial_date == today and self.daily_trial_used:
            return False
            
        return True
        
    def start_daily_trial(self):
        """开始每日试用"""
        if not self.can_use_daily_trial():
            return False, '今日试用已用完'
            
        today = datetime.now().strftime('%Y-%m-%d')
        self.daily_trial_date = today
        self.daily_trial_used = True
        self.save_to_local()
        
        Logger.info('ActivationManager: 开始每日试用')
        return True, '试用已开始'
        
    def pause(self, hours=3):
        """暂断功能"""
        self.paused_until = datetime.now() + timedelta(hours=hours)
        self.save_to_local()
        
        Logger.info(f'ActivationManager: 暂断{hours}小时')
        return True
        
    def cancel_pause(self):
        """取消暂断"""
        self.paused_until = None
        self.save_to_local()
        
        Logger.info('ActivationManager: 已取消暂断')
        return True
        
    def is_paused(self):
        """检查是否处于暂断状态"""
        if not self.paused_until:
            return False
            
        if datetime.now() >= self.paused_until:
            self.paused_until = None
            self.save_to_local()
            return False
            
        return True
        
    def get_pause_remaining(self):
        """获取暂断剩余时间"""
        if not self.is_paused():
            return None
            
        remaining = self.paused_until - datetime.now()
        return remaining
        
    def _update_days_remaining(self):
        """更新剩余天数"""
        if self.expires_at:
            delta = self.expires_at - datetime.now()
            self.days_remaining = max(0, delta.days)
        else:
            self.days_remaining = 0
            
    def start_auto_sync(self):
        """启动自动同步（每24小时）"""
        if self.auto_sync_event:
            self.auto_sync_event.cancel()
            
        # 每24小时同步一次
        self.auto_sync_event = Clock.schedule_interval(
            lambda dt: self.sync_from_server(),
            24 * 60 * 60
        )
        
        Logger.info('ActivationManager: 自动同步已启动')
        
    def stop_auto_sync(self):
        """停止自动同步"""
        if self.auto_sync_event:
            self.auto_sync_event.cancel()
            self.auto_sync_event = None
            
        Logger.info('ActivationManager: 自动同步已停止')
