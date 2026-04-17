"""
权限引导界面 - 首次运行时引导用户开启必要权限
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.app import App


class PermissionItem(BoxLayout):
    """单个权限项"""
    
    def __init__(self, title, description, granted=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(60)
        self.padding = dp(10)
        self.spacing = dp(10)
        
        # 左侧信息
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.7)
        
        title_label = Label(
            text=title,
            font_size='16sp',
            halign='left',
            valign='middle',
            size_hint_y=0.6
        )
        title_label.bind(size=title_label.setter('text_size'))
        
        desc_label = Label(
            text=description,
            font_size='12sp',
            halign='left',
            valign='middle',
            color=(0.7, 0.7, 0.7, 1),
            size_hint_y=0.4
        )
        desc_label.bind(size=desc_label.setter('text_size'))
        
        info_layout.add_widget(title_label)
        info_layout.add_widget(desc_label)
        
        # 右侧状态/按钮
        self.status_btn = Button(
            text='已授权' if granted else '去设置',
            size_hint_x=0.3,
            font_size='14sp',
            background_color=(0.3, 0.8, 0.3, 1) if granted else (0.2, 0.6, 0.9, 1),
            disabled=granted
        )
        
        self.add_widget(info_layout)
        self.add_widget(self.status_btn)


class PermissionScreen(Screen):
    """权限引导界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'permission'
        self.permissions = {
            'accessibility': {'title': '无障碍服务', 'desc': '用于执行自动点击和滑动操作', 'granted': False},
            'overlay': {'title': '悬浮窗权限', 'desc': '用于显示悬浮控制按钮', 'granted': False},
            'storage': {'title': '存储权限', 'desc': '用于保存截图和日志', 'granted': False},
            'camera': {'title': '相机权限', 'desc': '用于截图功能', 'granted': False}
        }
        self.build_ui()
    
    def build_ui(self):
        """构建界面"""
        main_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        # 标题
        title = Label(
            text='权限设置',
            font_size='24sp',
            size_hint_y=0.1,
            bold=True
        )
        
        # 说明
        desc = Label(
            text='应用需要以下权限才能正常工作，请依次授权：',
            font_size='14sp',
            size_hint_y=0.1,
            halign='left',
            color=(0.7, 0.7, 0.7, 1)
        )
        desc.bind(size=desc.setter('text_size'))
        
        # 权限列表
        scroll = ScrollView(size_hint_y=0.6)
        self.permission_list = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None)
        self.permission_list.bind(minimum_height=self.permission_list.setter('height'))
        
        for perm_id, perm_info in self.permissions.items():
            item = PermissionItem(
                perm_info['title'],
                perm_info['desc'],
                perm_info['granted']
            )
            item.status_btn.bind(on_press=lambda btn, pid=perm_id: self.request_permission(pid))
            self.permission_list.add_widget(item)
        
        scroll.add_widget(self.permission_list)
        
        # 按钮
        btn_layout = BoxLayout(size_hint_y=0.2, spacing=dp(10))
        
        self.refresh_btn = Button(
            text='刷新状态',
            font_size='16sp',
            background_color=(0.2, 0.6, 0.9, 1)
        )
        self.refresh_btn.bind(on_press=self.refresh_status)
        
        self.continue_btn = Button(
            text='继续使用',
            font_size='16sp',
            background_color=(0.3, 0.8, 0.3, 1),
            disabled=True
        )
        self.continue_btn.bind(on_press=self.on_continue)
        
        btn_layout.add_widget(self.refresh_btn)
        btn_layout.add_widget(self.continue_btn)
        
        main_layout.add_widget(title)
        main_layout.add_widget(desc)
        main_layout.add_widget(scroll)
        main_layout.add_widget(btn_layout)
        
        self.add_widget(main_layout)
    
    def request_permission(self, perm_id):
        """请求权限"""
        app = App.get_running_app()
        
        if perm_id == 'accessibility':
            # 打开无障碍设置
            if app.android_bridge:
                app.android_bridge.open_accessibility_settings()
        
        elif perm_id == 'overlay':
            # 打开悬浮窗设置
            if app.android_bridge:
                app.android_bridge.open_overlay_settings()
        
        elif perm_id == 'storage':
            # 请求存储权限
            if app.android_bridge:
                app.android_bridge.request_storage_permission()
        
        elif perm_id == 'camera':
            # 请求相机权限
            if app.android_bridge:
                app.android_bridge.request_camera_permission()
    
    def refresh_status(self, instance):
        """刷新权限状态"""
        app = App.get_running_app()
        
        if app.android_bridge:
            # 检查各项权限
            self.permissions['accessibility']['granted'] = app.android_bridge.is_accessibility_enabled()
            self.permissions['overlay']['granted'] = app.android_bridge.has_overlay_permission()
            self.permissions['storage']['granted'] = app.android_bridge.has_storage_permission()
            self.permissions['camera']['granted'] = app.android_bridge.has_camera_permission()
            
            # 更新界面
            self.permission_list.clear_widgets()
            for perm_id, perm_info in self.permissions.items():
                item = PermissionItem(
                    perm_info['title'],
                    perm_info['desc'],
                    perm_info['granted']
                )
                item.status_btn.bind(on_press=lambda btn, pid=perm_id: self.request_permission(pid))
                self.permission_list.add_widget(item)
            
            # 检查是否全部授权
            all_granted = all(p['granted'] for p in self.permissions.values())
            self.continue_btn.disabled = not all_granted
    
    def on_continue(self, instance):
        """继续使用"""
        app = App.get_running_app()
        app.root.current = 'main'
    
    def on_enter(self):
        """进入界面时刷新状态"""
        self.refresh_status(None)
