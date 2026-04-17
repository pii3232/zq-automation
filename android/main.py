"""
ZQ-自动化任务系统 Android客户端
基于 Kivy + Buildozer + Pyjnius 开发
"""
import os
import sys
import json
import time
from datetime import datetime
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.logger import Logger

# 导入自定义模块
from lib.config import Config
from lib.image_recognition import ImageRecognition
from lib.android_bridge import AndroidBridge
from lib.network import NetworkManager
from lib.activation import ActivationManager
from lib.workgroup import WorkgroupManager

# 设置日志
Logger.setLevel('DEBUG')


class MainScreen(Screen):
    """主界面"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.orientation = 'horizontal'  # 默认横屏
        
        # 创建主布局
        self.layout = BoxLayout(orientation='vertical')
        self.add_widget(self.layout)
        
        # 创建顶部状态栏
        self.create_status_bar()
        
        # 创建内容区域（使用ScreenManager）
        self.content_manager = ScreenManager()
        self.layout.add_widget(self.content_manager)
        
        # 创建底部导航栏
        self.create_bottom_nav()
        
        # 初始化各个屏幕
        self.init_screens()
        
        # 绑定窗口大小变化事件
        Window.bind(on_resize=self.on_window_resize)
        
        # 初始化权限请求
        Clock.schedule_once(self.request_permissions, 1)
        
    def create_status_bar(self):
        """创建顶部状态栏"""
        status_bar = BoxLayout(size_hint_y=None, height=dp(40), padding=dp(5))
        
        # 激活状态
        self.activation_status_label = Label(
            text='未登录',
            font_size=dp(14),
            size_hint_x=0.3,
            halign='left',
            valign='middle'
        )
        status_bar.add_widget(self.activation_status_label)
        
        # 用户名
        self.username_label = Label(
            text='',
            font_size=dp(14),
            size_hint_x=0.3,
            halign='center',
            valign='middle'
        )
        status_bar.add_widget(self.username_label)
        
        # 剩余时间
        self.remaining_time_label = Label(
            text='剩余: --',
            font_size=dp(14),
            size_hint_x=0.3,
            halign='right',
            valign='middle'
        )
        status_bar.add_widget(self.remaining_time_label)
        
        self.layout.add_widget(status_bar)
        
    def create_bottom_nav(self):
        """创建底部导航栏"""
        nav_bar = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5), padding=dp(5))
        
        # 指挥按钮
        self.command_btn = Button(
            text='指挥',
            font_size=dp(16),
            on_press=lambda x: self.switch_screen('command')
        )
        nav_bar.add_widget(self.command_btn)
        
        # 激活按钮
        self.activation_btn = Button(
            text='激活',
            font_size=dp(16),
            on_press=lambda x: self.switch_screen('activation')
        )
        nav_bar.add_widget(self.activation_btn)
        
        # 悬窗模式按钮
        self.float_btn = ToggleButton(
            text='悬窗',
            font_size=dp(16),
            on_press=self.toggle_float_mode
        )
        nav_bar.add_widget(self.float_btn)
        
        # 设置按钮
        self.settings_btn = Button(
            text='设置',
            font_size=dp(16),
            on_press=lambda x: self.switch_screen('settings')
        )
        nav_bar.add_widget(self.settings_btn)
        
        self.layout.add_widget(nav_bar)
        
    def init_screens(self):
        """初始化各个屏幕"""
        from ui.command_screen import CommandScreen
        from ui.activation_screen import ActivationScreen
        from ui.settings_screen import SettingsScreen
        
        self.command_screen = CommandScreen(name='command')
        self.activation_screen = ActivationScreen(name='activation')
        self.settings_screen = SettingsScreen(name='settings')
        
        self.content_manager.add_widget(self.command_screen)
        self.content_manager.add_widget(self.activation_screen)
        self.content_manager.add_widget(self.settings_screen)
        
    def switch_screen(self, screen_name):
        """切换屏幕"""
        self.content_manager.current = screen_name
        
    def toggle_float_mode(self, instance):
        """切换悬窗模式"""
        if instance.state == 'down':
            self.app.enter_float_mode()
        else:
            self.app.exit_float_mode()
            
    def on_window_resize(self, instance, width, height):
        """窗口大小变化时调整布局"""
        # 判断横屏还是竖屏
        if width > height:
            self.orientation = 'horizontal'
        else:
            self.orientation = 'vertical'
            
        # 更新各个屏幕的布局
        if hasattr(self, 'command_screen'):
            self.command_screen.update_layout(self.orientation)
            
    def request_permissions(self, dt):
        """请求Android权限"""
        if self.app.android_bridge:
            self.app.android_bridge.request_permissions()
            
    def update_status(self):
        """更新状态栏"""
        if self.app.activation_manager:
            if self.app.activation_manager.is_activated():
                self.activation_status_label.text = '已激活'
                self.activation_status_label.color = (0, 1, 0, 1)
                self.username_label.text = self.app.activation_manager.username
                if self.app.activation_manager.expires_at:
                    remaining = self.app.activation_manager.days_remaining
                    self.remaining_time_label.text = f'剩余: {remaining}天'
            else:
                self.activation_status_label.text = '未激活'
                self.activation_status_label.color = (1, 0.5, 0, 1)
                self.username_label.text = self.app.activation_manager.username or '未登录'
                self.remaining_time_label.text = '剩余: 0天'
        else:
            self.activation_status_label.text = '未登录'
            self.activation_status_label.color = (1, 0, 0, 1)
            self.username_label.text = ''
            self.remaining_time_label.text = '剩余: --'


class ZQAutomationApp(App):
    """主应用"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 初始化各个管理器
        self.config = None
        self.android_bridge = None
        self.network_manager = None
        self.activation_manager = None
        self.workgroup_manager = None
        self.image_recognition = None
        
        # 悬窗模式
        self.float_mode = False
        
        # 执行状态
        self.cmd_running = False
        self.cmd_paused = False
        
    def build(self):
        """构建应用"""
        # 初始化配置
        self.init_config()
        
        # 初始化Android桥接
        self.init_android_bridge()
        
        # 初始化网络管理器
        self.init_network_manager()
        
        # 初始化激活管理器
        self.init_activation_manager()
        
        # 初始化工作组管理器
        self.init_workgroup_manager()
        
        # 初始化图像识别
        self.init_image_recognition()
        
        # 创建主屏幕
        self.main_screen = MainScreen(name='main')
        
        # 设置窗口属性
        Window.softinput_mode = 'below_target'
        
        return self.main_screen
        
    def init_config(self):
        """初始化配置"""
        try:
            self.config = Config()
            Logger.info('App: 配置加载成功')
        except Exception as e:
            Logger.error(f'App: 配置加载失败 - {e}')
            self.config = Config.create_default()
            
    def init_android_bridge(self):
        """初始化Android桥接"""
        try:
            from lib.android_bridge import AndroidBridge
            self.android_bridge = AndroidBridge()
            Logger.info('App: Android桥接初始化成功')
        except Exception as e:
            Logger.error(f'App: Android桥接初始化失败 - {e}')
            self.android_bridge = None
            
    def init_network_manager(self):
        """初始化网络管理器"""
        try:
            self.network_manager = NetworkManager(self.config)
            Logger.info('App: 网络管理器初始化成功')
        except Exception as e:
            Logger.error(f'App: 网络管理器初始化失败 - {e}')
            
    def init_activation_manager(self):
        """初始化激活管理器"""
        try:
            self.activation_manager = ActivationManager(self.config, self.network_manager)
            self.activation_manager.load_from_local()
            Logger.info('App: 激活管理器初始化成功')
        except Exception as e:
            Logger.error(f'App: 激活管理器初始化失败 - {e}')
            
    def init_workgroup_manager(self):
        """初始化工作组管理器"""
        try:
            self.workgroup_manager = WorkgroupManager(self.config, self.network_manager)
            self.workgroup_manager.load_from_local()
            Logger.info('App: 工作组管理器初始化成功')
        except Exception as e:
            Logger.error(f'App: 工作组管理器初始化失败 - {e}')
            
    def init_image_recognition(self):
        """初始化图像识别"""
        try:
            self.image_recognition = ImageRecognition(self.config)
            Logger.info('App: 图像识别初始化成功')
        except Exception as e:
            Logger.error(f'App: 图像识别初始化失败 - {e}')
            
    def enter_float_mode(self):
        """进入悬窗模式"""
        if self.android_bridge:
            self.float_mode = True
            self.android_bridge.start_float_window()
            Logger.info('App: 进入悬窗模式')
            
    def exit_float_mode(self):
        """退出悬窗模式"""
        if self.android_bridge:
            self.float_mode = False
            self.android_bridge.stop_float_window()
            Logger.info('App: 退出悬窗模式')
            
    def on_pause(self):
        """应用暂停"""
        # 保存状态
        if self.activation_manager:
            self.activation_manager.save_to_local()
        if self.workgroup_manager:
            self.workgroup_manager.save_to_local()
        return True
        
    def on_resume(self):
        """应用恢复"""
        # 恢复状态
        if self.activation_manager:
            self.activation_manager.sync_from_server()
        self.main_screen.update_status()


if __name__ == '__main__':
    app = ZQAutomationApp()
    app.run()
