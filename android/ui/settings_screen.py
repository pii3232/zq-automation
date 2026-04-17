"""
设置标签页界面
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.metrics import dp
from kivy.logger import Logger


class SettingsScreen(Screen):
    """设置标签页"""
    
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
            text='设置',
            font_size=dp(24),
            size_hint_y=None,
            height=dp(60),
            halign='center'
        )
        self.layout.add_widget(title)
        
        # 网络设置
        self.create_network_section()
        
        # 显示设置
        self.create_display_section()
        
        # 识别设置
        self.create_recognition_section()
        
        # 关于信息
        self.create_about_section()
        
    def create_network_section(self):
        """创建网络设置区域"""
        network_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(200), spacing=dp(10))
        
        # 标题
        section_title = Label(
            text='网络设置',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(40),
            halign='left'
        )
        network_box.add_widget(section_title)
        
        # 服务器地址
        server_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        server_label = Label(text='服务器:', size_hint_x=0.3, font_size=dp(14), halign='right')
        self.server_input = TextInput(
            hint_text='服务器地址',
            size_hint_x=0.7,
            font_size=dp(14),
            multiline=False
        )
        if self.app and self.app.config:
            self.server_input.text = self.app.config.server_url
        server_layout.add_widget(server_label)
        server_layout.add_widget(self.server_input)
        network_box.add_widget(server_layout)
        
        # 局域网IP
        local_ip_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        local_ip_label = Label(text='局域网IP:', size_hint_x=0.3, font_size=dp(14), halign='right')
        self.local_ip_input = TextInput(
            hint_text='局域网IP地址',
            size_hint_x=0.7,
            font_size=dp(14),
            multiline=False
        )
        if self.app and self.app.config:
            self.local_ip_input.text = self.app.config.local_server_ip
        local_ip_layout.add_widget(local_ip_label)
        local_ip_layout.add_widget(self.local_ip_input)
        network_box.add_widget(local_ip_layout)
        
        # 局域网端口
        local_port_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        local_port_label = Label(text='端口:', size_hint_x=0.3, font_size=dp(14), halign='right')
        self.local_port_input = TextInput(
            hint_text='端口号',
            size_hint_x=0.7,
            font_size=dp(14),
            multiline=False
        )
        if self.app and self.app.config:
            self.local_port_input.text = self.app.config.local_server_port
        local_port_layout.add_widget(local_port_label)
        local_port_layout.add_widget(self.local_port_input)
        network_box.add_widget(local_port_layout)
        
        self.layout.add_widget(network_box)
        
    def create_display_section(self):
        """创建显示设置区域"""
        display_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150), spacing=dp(10))
        
        # 标题
        section_title = Label(
            text='显示设置',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(40),
            halign='left'
        )
        display_box.add_widget(section_title)
        
        # 悬窗大小
        float_size_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        float_size_label = Label(text='悬窗大小(DPI):', size_hint_x=0.3, font_size=dp(14), halign='right')
        self.float_size_input = TextInput(
            hint_text='悬窗直径',
            size_hint_x=0.7,
            font_size=dp(14),
            multiline=False,
            input_filter='int'
        )
        if self.app and self.app.config:
            self.float_size_input.text = str(self.app.config.float_window_size)
        float_size_layout.add_widget(float_size_label)
        float_size_layout.add_widget(self.float_size_input)
        display_box.add_widget(float_size_layout)
        
        # 自动悬窗
        auto_float_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        auto_float_label = Label(text='执行前自动悬窗:', size_hint_x=0.3, font_size=dp(14), halign='right')
        self.auto_float_spinner = Spinner(
            text='是',
            values=['是', '否'],
            size_hint_x=0.7,
            font_size=dp(14)
        )
        auto_float_layout.add_widget(auto_float_label)
        auto_float_layout.add_widget(self.auto_float_spinner)
        display_box.add_widget(auto_float_layout)
        
        self.layout.add_widget(display_box)
        
    def create_recognition_section(self):
        """创建识别设置区域"""
        recognition_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(100), spacing=dp(10))
        
        # 标题
        section_title = Label(
            text='识别设置',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(40),
            halign='left'
        )
        recognition_box.add_widget(section_title)
        
        # 相似度阈值
        similarity_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        similarity_label = Label(text='相似度(%):', size_hint_x=0.3, font_size=dp(14), halign='right')
        self.similarity_input = TextInput(
            hint_text='相似度阈值',
            size_hint_x=0.7,
            font_size=dp(14),
            multiline=False,
            input_filter='int'
        )
        if self.app and self.app.config:
            self.similarity_input.text = str(self.app.config.global_similarity)
        similarity_layout.add_widget(similarity_label)
        similarity_layout.add_widget(self.similarity_input)
        recognition_box.add_widget(similarity_layout)
        
        self.layout.add_widget(recognition_box)
        
    def create_about_section(self):
        """创建关于区域"""
        about_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(150), spacing=dp(10))
        
        # 标题
        section_title = Label(
            text='关于',
            font_size=dp(18),
            size_hint_y=None,
            height=dp(40),
            halign='left'
        )
        about_box.add_widget(section_title)
        
        # 应用信息
        info_label = Label(
            text='ZQ-自动化任务系统 Android版\n版本: 1.0.0\n基于 Kivy + Buildozer 开发',
            font_size=dp(14),
            halign='center'
        )
        about_box.add_widget(info_label)
        
        self.layout.add_widget(about_box)
        
        # 保存按钮
        save_btn = Button(
            text='保存设置',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(50),
            on_press=self.on_save
        )
        self.layout.add_widget(save_btn)
        
    def update_layout(self, orientation):
        """更新布局"""
        self.orientation = orientation
        self.create_ui()
        
    def on_save(self, instance):
        """保存设置"""
        if not self.app:
            self.app = self._get_app()
            
        if not self.app or not self.app.config:
            return
            
        # 保存网络设置
        self.app.config.set('server_url', self.server_input.text.strip())
        self.app.config.set('local_server_ip', self.local_ip_input.text.strip())
        self.app.config.set('local_server_port', self.local_port_input.text.strip())
        
        # 保存显示设置
        try:
            float_size = int(self.float_size_input.text.strip())
            self.app.config.set('float_window_size', float_size)
        except:
            pass
            
        auto_float = self.auto_float_spinner.text == '是'
        self.app.config.set('auto_float_before_exec', auto_float)
        
        # 保存识别设置
        try:
            similarity = int(self.similarity_input.text.strip())
            self.app.config.set('global_similarity', similarity)
        except:
            pass
            
        # 保存到文件
        self.app.config.save()
        
        # 显示成功消息
        self.show_message('成功', '设置已保存')
        
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
