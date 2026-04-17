"""
激活标签页界面
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.logger import Logger


class ActivationScreen(Screen):
    """激活标签页"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.orientation = 'horizontal'
        
        # 创建布局
        self.layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        self.add_widget(self.layout)
        
        # 初始化界面
        self.create_ui()
        
    def create_ui(self):
        """创建界面"""
        self.layout.clear_widgets()
        
        # 获取App实例
        self.app = self._get_app()
        
        # 标题
        title = Label(
            text='激活管理',
            font_size=dp(24),
            size_hint_y=None,
            height=dp(60),
            halign='center'
        )
        self.layout.add_widget(title)
        
        # 登录/注册区域
        self.create_login_section()
        
        # 激活状态区域
        self.create_status_section()
        
        # 激活操作区域
        self.create_action_section()
        
    def create_login_section(self):
        """创建登录区域"""
        login_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(250), spacing=dp(10))
        
        # 用户名
        username_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        username_label = Label(text='用户名:', size_hint_x=0.3, font_size=dp(14), halign='right')
        self.username_input = TextInput(
            hint_text='请输入用户名',
            size_hint_x=0.7,
            font_size=dp(16),
            multiline=False
        )
        username_layout.add_widget(username_label)
        username_layout.add_widget(self.username_input)
        login_box.add_widget(username_layout)
        
        # 密码
        password_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        password_label = Label(text='密码:', size_hint_x=0.3, font_size=dp(14), halign='right')
        self.password_input = TextInput(
            hint_text='请输入密码',
            password=True,
            size_hint_x=0.7,
            font_size=dp(16),
            multiline=False
        )
        password_layout.add_widget(password_label)
        password_layout.add_widget(self.password_input)
        login_box.add_widget(password_layout)
        
        # 保存密码选项
        save_password_layout = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(10))
        self.save_password_checkbox = CheckBox(size_hint_x=0.1)
        save_password_label = Label(text='保存密码', size_hint_x=0.9, font_size=dp(14), halign='left')
        save_password_layout.add_widget(self.save_password_checkbox)
        save_password_layout.add_widget(save_password_label)
        login_box.add_widget(save_password_layout)
        
        # 登录/注册按钮
        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        self.login_btn = Button(
            text='登录',
            font_size=dp(16),
            on_press=self.on_login
        )
        btn_layout.add_widget(self.login_btn)
        
        self.register_btn = Button(
            text='注册',
            font_size=dp(16),
            on_press=self.on_register
        )
        btn_layout.add_widget(self.register_btn)
        
        self.logout_btn = Button(
            text='退出登录',
            font_size=dp(16),
            on_press=self.on_logout,
            disabled=True
        )
        btn_layout.add_widget(self.logout_btn)
        
        login_box.add_widget(btn_layout)
        self.layout.add_widget(login_box)
        
    def create_status_section(self):
        """创建状态区域"""
        status_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150), spacing=dp(10), padding=dp(10))
        
        # 状态标题
        status_title = Label(
            text='激活状态',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(40),
            halign='center'
        )
        status_box.add_widget(status_title)
        
        # 状态信息
        info_layout = BoxLayout(orientation='vertical', spacing=dp(5))
        
        # 用户名显示
        self.status_username = Label(
            text='用户: 未登录',
            font_size=dp(14),
            halign='left',
            size_hint_y=None,
            height=dp(30)
        )
        info_layout.add_widget(self.status_username)
        
        # 激活状态
        self.status_activation = Label(
            text='状态: 未激活',
            font_size=dp(14),
            halign='left',
            size_hint_y=None,
            height=dp(30)
        )
        info_layout.add_widget(self.status_activation)
        
        # 剩余时间
        self.status_remaining = Label(
            text='剩余: --天',
            font_size=dp(14),
            halign='left',
            size_hint_y=None,
            height=dp(30)
        )
        info_layout.add_widget(self.status_remaining)
        
        status_box.add_widget(info_layout)
        self.layout.add_widget(status_box)
        
    def create_action_section(self):
        """创建操作区域"""
        action_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(200), spacing=dp(10))
        
        # 激活码输入
        code_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        code_label = Label(text='激活码:', size_hint_x=0.3, font_size=dp(14), halign='right')
        self.activation_code_input = TextInput(
            hint_text='请输入激活码',
            size_hint_x=0.7,
            font_size=dp(16),
            multiline=False
        )
        code_layout.add_widget(code_label)
        code_layout.add_widget(self.activation_code_input)
        action_box.add_widget(code_layout)
        
        # 激活按钮
        activate_btn = Button(
            text='激活',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(50),
            on_press=self.on_activate
        )
        action_box.add_widget(activate_btn)
        
        # 同步按钮
        sync_btn = Button(
            text='同步状态',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(50),
            on_press=self.on_sync
        )
        action_box.add_widget(sync_btn)
        
        self.layout.add_widget(action_box)
        
    def update_layout(self, orientation):
        """更新布局"""
        self.orientation = orientation
        self.create_ui()
        
    def update_status(self):
        """更新状态显示"""
        if not self.app:
            self.app = self._get_app()
            
        if not self.app or not self.app.activation_manager:
            return
            
        act_manager = self.app.activation_manager
        
        # 更新用户名
        if act_manager.username:
            self.status_username.text = f'用户: {act_manager.username}'
            self.username_input.text = act_manager.username
            
            # 如果保存了密码，自动填充
            if act_manager.save_password and act_manager.password:
                self.password_input.text = act_manager.password
                self.save_password_checkbox.active = True
                
            # 更新按钮状态
            self.login_btn.disabled = True
            self.register_btn.disabled = True
            self.logout_btn.disabled = False
        else:
            self.status_username.text = '用户: 未登录'
            self.login_btn.disabled = False
            self.register_btn.disabled = False
            self.logout_btn.disabled = True
            
        # 更新激活状态
        if act_manager.is_activated():
            self.status_activation.text = '状态: 已激活'
            self.status_activation.color = (0, 1, 0, 1)  # 绿色
        else:
            self.status_activation.text = '状态: 未激活'
            self.status_activation.color = (1, 0.5, 0, 1)  # 橙色
            
        # 更新剩余时间
        if act_manager.expires_at:
            self.status_remaining.text = f'剩余: {act_manager.days_remaining}天'
        else:
            self.status_remaining.text = '剩余: --天'
            
    def on_login(self, instance):
        """登录"""
        if not self.app:
            self.app = self._get_app()
            
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        save_password = self.save_password_checkbox.active
        
        if not username or not password:
            self.show_message('错误', '请输入用户名和密码')
            return
            
        success, message = self.app.activation_manager.login(username, password, save_password)
        
        if success:
            self.show_message('成功', message)
            self.update_status()
            # 更新主界面状态
            if hasattr(self.app, 'main_screen'):
                self.app.main_screen.update_status()
        else:
            self.show_message('错误', message)
            
    def on_register(self, instance):
        """注册"""
        self.show_register_dialog()
        
    def show_register_dialog(self):
        """显示注册对话框"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # 用户名
        username_input = TextInput(
            hint_text='用户名',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16)
        )
        content.add_widget(username_input)
        
        # 密码
        password_input = TextInput(
            hint_text='密码',
            password=True,
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16)
        )
        content.add_widget(password_input)
        
        # 确认密码
        confirm_input = TextInput(
            hint_text='确认密码',
            password=True,
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16)
        )
        content.add_widget(confirm_input)
        
        # 邀请码（可选）
        invite_input = TextInput(
            hint_text='邀请码（可选）',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16)
        )
        content.add_widget(invite_input)
        
        # 按钮
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        cancel_btn = Button(text='取消', on_press=lambda x: popup.dismiss())
        buttons.add_widget(cancel_btn)
        
        register_btn = Button(text='注册')
        buttons.add_widget(register_btn)
        
        content.add_widget(buttons)
        
        popup = Popup(
            title='用户注册',
            content=content,
            size_hint=(0.8, 0.7)
        )
        
        def do_register(instance):
            username = username_input.text.strip()
            password = password_input.text.strip()
            confirm = confirm_input.text.strip()
            invite = invite_input.text.strip()
            
            if not username or not password:
                self.show_message('错误', '请输入用户名和密码')
                return
                
            if password != confirm:
                self.show_message('错误', '两次密码不一致')
                return
                
            success, message = self.app.activation_manager.register(
                username, password, invite if invite else None
            )
            
            if success:
                popup.dismiss()
                self.show_message('成功', message)
            else:
                self.show_message('错误', message)
                
        register_btn.bind(on_press=do_register)
        popup.open()
        
    def on_logout(self, instance):
        """退出登录"""
        if not self.app:
            self.app = self._get_app()
            
        self.app.activation_manager.logout()
        self.update_status()
        
        # 清空输入框
        self.username_input.text = ''
        self.password_input.text = ''
        self.save_password_checkbox.active = False
        
        # 更新主界面状态
        if hasattr(self.app, 'main_screen'):
            self.app.main_screen.update_status()
            
        self.show_message('成功', '已退出登录')
        
    def on_activate(self, instance):
        """激活"""
        if not self.app:
            self.app = self._get_app()
            
        if not self.app.activation_manager.username:
            self.show_message('错误', '请先登录')
            return
            
        code = self.activation_code_input.text.strip()
        
        if not code:
            self.show_message('错误', '请输入激活码')
            return
            
        success, message = self.app.activation_manager.activate(code)
        
        if success:
            self.show_message('成功', message)
            self.update_status()
            self.activation_code_input.text = ''
            
            # 更新主界面状态
            if hasattr(self.app, 'main_screen'):
                self.app.main_screen.update_status()
        else:
            self.show_message('错误', message)
            
    def on_sync(self, instance):
        """同步状态"""
        if not self.app:
            self.app = self._get_app()
            
        if not self.app.activation_manager.username:
            self.show_message('错误', '请先登录')
            return
            
        success = self.app.activation_manager.sync_from_server()
        
        if success:
            self.show_message('成功', '同步成功')
            self.update_status()
            
            # 更新主界面状态
            if hasattr(self.app, 'main_screen'):
                self.app.main_screen.update_status()
        else:
            self.show_message('错误', '同步失败')
            
    def show_message(self, title, message):
        """显示消息对话框"""
        content = BoxLayout(orientation='vertical', padding=dp(20))
        
        label = Label(text=message, font_size=dp(16))
        content.add_widget(label)
        
        btn = Button(
            text='确定',
            size_hint_y=None,
            height=dp(50),
            on_press=lambda x: popup.dismiss()
        )
        content.add_widget(btn)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.7, 0.4)
        )
        popup.open()
        
    def _get_app(self):
        """获取App实例"""
        from kivy.app import App
        return App.get_running_app()
