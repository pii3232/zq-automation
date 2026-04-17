"""
指挥标签页界面
"""
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import dp
from kivy.logger import Logger


class CommandScreen(Screen):
    """指挥标签页"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = None
        self.orientation = 'horizontal'
        
        # 创建布局
        self.layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        self.add_widget(self.layout)
        
        # 初始化界面
        self.create_ui()
        
    def create_ui(self):
        """创建界面"""
        self.layout.clear_widgets()
        
        # 顶部：工作组状态
        self.create_workgroup_section()
        
        # 中间：主内容区域（左右分栏）
        content_layout = BoxLayout(orientation='horizontal', spacing=dp(10))
        
        # 左侧：模板按钮区
        left_panel = self.create_template_panel()
        content_layout.add_widget(left_panel)
        
        # 右侧：命令列表和执行控制
        right_panel = self.create_command_panel()
        content_layout.add_widget(right_panel)
        
        self.layout.add_widget(content_layout)
        
        # 底部：执行日志和状态
        self.create_log_section()
        
    def create_workgroup_section(self):
        """创建工作组状态区域"""
        wg_layout = BoxLayout(size_hint_y=None, height=dp(80), spacing=dp(10))
        
        # 工作组名称
        self.wg_name_label = Label(
            text='未加入工作组',
            font_size=dp(16),
            size_hint_x=0.3,
            halign='left',
            valign='middle'
        )
        wg_layout.add_widget(self.wg_name_label)
        
        # 加入/退出工作组按钮
        self.wg_join_btn = Button(
            text='加入工作组',
            font_size=dp(14),
            size_hint_x=0.2,
            on_press=self.on_join_workgroup
        )
        wg_layout.add_widget(self.wg_join_btn)
        
        # 暂断按钮
        self.wg_pause_btn = Button(
            text='暂断3小时',
            font_size=dp(14),
            size_hint_x=0.2,
            on_press=self.on_pause_workgroup,
            disabled=True
        )
        wg_layout.add_widget(self.wg_pause_btn)
        
        # 同步按钮
        self.wg_sync_btn = Button(
            text='同步',
            font_size=dp(14),
            size_hint_x=0.15,
            on_press=self.on_sync_workgroup,
            disabled=True
        )
        wg_layout.add_widget(self.wg_sync_btn)
        
        # 执行模式
        self.exec_mode_spinner = Spinner(
            text='本地模式',
            values=['本地模式', '工作组模式'],
            size_hint_x=0.15,
            font_size=dp(14)
        )
        wg_layout.add_widget(self.exec_mode_spinner)
        
        self.layout.add_widget(wg_layout)
        
    def create_template_panel(self):
        """创建模板按钮面板"""
        panel = BoxLayout(orientation='vertical', size_hint_x=0.3, spacing=dp(5))
        
        # 标题
        title = Label(
            text='命令模板',
            font_size=dp(16),
            size_hint_y=None,
            height=dp(40),
            halign='center'
        )
        panel.add_widget(title)
        
        # 模板按钮列表
        template_layout = GridLayout(cols=2, spacing=dp(5), size_hint_y=None)
        template_layout.bind(minimum_height=template_layout.setter('height'))
        
        # 获取模板名称
        self.app = self._get_app()
        if self.app and self.app.workgroup_manager:
            template_names = self.app.workgroup_manager.get_template_names()
        else:
            template_names = ['调动', '走到', '预约', '集结', '集火']
            
        for name in template_names:
            btn = Button(
                text=name,
                font_size=dp(14),
                size_hint_y=None,
                height=dp(50),
                on_press=lambda x, n=name: self.on_template_selected(n)
            )
            template_layout.add_widget(btn)
            
        # 添加到滚动视图
        scroll = ScrollView()
        scroll.add_widget(template_layout)
        panel.add_widget(scroll)
        
        # 模板管理按钮
        manage_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
        
        edit_btn = Button(
            text='编辑模板',
            font_size=dp(12),
            on_press=self.on_edit_template
        )
        manage_layout.add_widget(edit_btn)
        
        panel.add_widget(manage_layout)
        
        return panel
        
    def create_command_panel(self):
        """创建命令列表面板"""
        panel = BoxLayout(orientation='vertical', size_hint_x=0.7, spacing=dp(5))
        
        # 标题和操作按钮
        header = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(5))
        
        title = Label(text='命令列表', font_size=dp(16), size_hint_x=0.3)
        header.add_widget(title)
        
        add_btn = Button(text='添加', font_size=dp(12), size_hint_x=0.15, on_press=self.on_add_command)
        header.add_widget(add_btn)
        
        remove_btn = Button(text='删除', font_size=dp(12), size_hint_x=0.15, on_press=self.on_remove_command)
        header.add_widget(remove_btn)
        
        clear_btn = Button(text='清空', font_size=dp(12), size_hint_x=0.15, on_press=self.on_clear_commands)
        header.add_widget(clear_btn)
        
        edit_btn = Button(text='编辑', font_size=dp(12), size_hint_x=0.15, on_press=self.on_edit_command)
        header.add_widget(edit_btn)
        
        panel.add_widget(header)
        
        # 命令列表
        self.cmd_list_layout = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        self.cmd_list_layout.bind(minimum_height=self.cmd_list_layout.setter('height'))
        
        scroll = ScrollView()
        scroll.add_widget(self.cmd_list_layout)
        panel.add_widget(scroll)
        
        # 执行控制
        control_layout = BoxLayout(size_hint_y=None, height=dp(60), spacing=dp(5))
        
        self.exec_btn = Button(
            text='执行',
            font_size=dp(16),
            size_hint_x=0.3,
            on_press=self.on_execute
        )
        control_layout.add_widget(self.exec_btn)
        
        self.pause_btn = Button(
            text='暂停',
            font_size=dp(16),
            size_hint_x=0.2,
            on_press=self.on_pause,
            disabled=True
        )
        control_layout.add_widget(self.pause_btn)
        
        self.stop_btn = Button(
            text='停止',
            font_size=dp(16),
            size_hint_x=0.2,
            on_press=self.on_stop,
            disabled=True
        )
        control_layout.add_widget(self.stop_btn)
        
        panel.add_widget(control_layout)
        
        return panel
        
    def create_log_section(self):
        """创建日志区域"""
        log_layout = BoxLayout(size_hint_y=None, height=dp(150), orientation='vertical', spacing=dp(5))
        
        # 标题
        title = Label(
            text='执行日志',
            font_size=dp(14),
            size_hint_y=None,
            height=dp(30),
            halign='left'
        )
        log_layout.add_widget(title)
        
        # 日志显示
        self.log_label = Label(
            text='等待执行...',
            font_size=dp(12),
            halign='left',
            valign='top',
            text_size=(None, None)
        )
        
        scroll = ScrollView()
        scroll.add_widget(self.log_label)
        log_layout.add_widget(scroll)
        
        # 状态显示
        self.status_label = Label(
            text='状态: 就绪',
            font_size=dp(12),
            size_hint_y=None,
            height=dp(30),
            halign='left'
        )
        log_layout.add_widget(self.status_label)
        
        self.layout.add_widget(log_layout)
        
    def update_layout(self, orientation):
        """更新布局（横竖屏切换）"""
        self.orientation = orientation
        self.create_ui()
        
    def update_workgroup_status(self):
        """更新工作组状态"""
        if not self.app:
            self.app = self._get_app()
            
        if not self.app or not self.app.workgroup_manager:
            return
            
        wg_manager = self.app.workgroup_manager
        
        if wg_manager.is_joined():
            self.wg_name_label.text = f'工作组: {wg_manager.workgroup_name}'
            self.wg_join_btn.text = '退出工作组'
            self.wg_pause_btn.disabled = False
            self.wg_sync_btn.disabled = False
            
            if wg_manager.is_paused():
                self.wg_pause_btn.text = '取消暂断'
            else:
                self.wg_pause_btn.text = '暂断3小时'
        else:
            self.wg_name_label.text = '未加入工作组'
            self.wg_join_btn.text = '加入工作组'
            self.wg_pause_btn.disabled = True
            self.wg_sync_btn.disabled = True
            
    def refresh_command_list(self):
        """刷新命令列表"""
        self.cmd_list_layout.clear_widgets()
        
        if not self.app:
            self.app = self._get_app()
            
        if not self.app:
            return
            
        # 获取命令列表
        commands = self.app.workgroup_manager.get_cmd_list()
        
        for i, cmd in enumerate(commands):
            item = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(5))
            
            # 序号
            index_label = Label(text=str(i+1), size_hint_x=0.1, font_size=dp(12))
            item.add_widget(index_label)
            
            # 命令名称
            name_label = Label(text=cmd.get('name', ''), size_hint_x=0.4, font_size=dp(12), halign='left')
            item.add_widget(name_label)
            
            # 模板
            template_label = Label(text=cmd.get('template', ''), size_hint_x=0.3, font_size=dp(12))
            item.add_widget(template_label)
            
            # 状态
            status = cmd.get('status', 'pending')
            status_label = Label(text=status, size_hint_x=0.2, font_size=dp(12))
            item.add_widget(status_label)
            
            self.cmd_list_layout.add_widget(item)
            
    def on_join_workgroup(self, instance):
        """加入/退出工作组"""
        if not self.app:
            self.app = self._get_app()
            
        if not self.app:
            return
            
        wg_manager = self.app.workgroup_manager
        
        if wg_manager.is_joined():
            # 退出工作组
            wg_manager.leave()
            self.update_workgroup_status()
        else:
            # 显示加入工作组对话框
            self.show_join_workgroup_dialog()
            
    def show_join_workgroup_dialog(self):
        """显示加入工作组对话框"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # 工作组ID
        id_input = TextInput(
            hint_text='工作组ID',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16)
        )
        content.add_widget(id_input)
        
        # 密码（可选）
        password_input = TextInput(
            hint_text='密码（可选）',
            password=True,
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16)
        )
        content.add_widget(password_input)
        
        # 按钮
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        cancel_btn = Button(text='取消', on_press=lambda x: popup.dismiss())
        buttons.add_widget(cancel_btn)
        
        join_btn = Button(text='加入')
        buttons.add_widget(join_btn)
        
        content.add_widget(buttons)
        
        popup = Popup(
            title='加入工作组',
            content=content,
            size_hint=(0.8, 0.5)
        )
        
        def do_join(instance):
            wg_id = id_input.text.strip()
            password = password_input.text.strip()
            
            if not wg_id:
                return
                
            success, message = self.app.workgroup_manager.join(wg_id, password if password else None)
            
            if success:
                popup.dismiss()
                self.update_workgroup_status()
                self.refresh_command_list()
            else:
                # 显示错误
                Logger.error(f'CommandScreen: 加入失败 - {message}')
                
        join_btn.bind(on_press=do_join)
        popup.open()
        
    def on_pause_workgroup(self, instance):
        """暂断/取消暂断"""
        if not self.app:
            self.app = self._get_app()
            
        wg_manager = self.app.workgroup_manager
        
        if wg_manager.is_paused():
            wg_manager.cancel_pause()
        else:
            wg_manager.pause(3)
            
        self.update_workgroup_status()
        
    def on_sync_workgroup(self, instance):
        """同步工作组"""
        if not self.app:
            self.app = self._get_app()
            
        success, message = self.app.workgroup_manager.sync()
        if success:
            self.refresh_command_list()
            
    def on_template_selected(self, template_name):
        """模板被选中"""
        self.selected_template = template_name
        Logger.info(f'CommandScreen: 选择模板 - {template_name}')
        
    def on_add_command(self, instance):
        """添加命令"""
        if not hasattr(self, 'selected_template'):
            return
            
        # 显示添加命令对话框
        self.show_add_command_dialog(self.selected_template)
        
    def show_add_command_dialog(self, template_name):
        """显示添加命令对话框"""
        if not self.app:
            self.app = self._get_app()
            
        template = self.app.workgroup_manager.get_template(template_name)
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        # 命令名称
        name_input = TextInput(
            hint_text='命令名称',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16)
        )
        content.add_widget(name_input)
        
        # 参数输入
        params_input = TextInput(
            hint_text='参数',
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16)
        )
        content.add_widget(params_input)
        
        # 按钮
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        cancel_btn = Button(text='取消', on_press=lambda x: popup.dismiss())
        buttons.add_widget(cancel_btn)
        
        add_btn = Button(text='添加')
        buttons.add_widget(add_btn)
        
        content.add_widget(buttons)
        
        popup = Popup(
            title=f'添加命令 - {template_name}',
            content=content,
            size_hint=(0.8, 0.5)
        )
        
        def do_add(instance):
            name = name_input.text.strip()
            params = params_input.text.strip()
            
            if not name:
                return
                
            cmd = {
                'name': name,
                'template': template_name,
                'params': {'coord_params': params},
                'status': 'pending'
            }
            
            self.app.workgroup_manager.add_command(cmd)
            popup.dismiss()
            self.refresh_command_list()
            
        add_btn.bind(on_press=do_add)
        popup.open()
        
    def on_remove_command(self, instance):
        """删除命令"""
        # TODO: 实现删除选中命令
        pass
        
    def on_clear_commands(self, instance):
        """清空命令列表"""
        if not self.app:
            self.app = self._get_app()
            
        self.app.workgroup_manager.clear_commands()
        self.refresh_command_list()
        
    def on_edit_command(self, instance):
        """编辑命令"""
        # TODO: 实现编辑命令
        pass
        
    def on_edit_template(self, instance):
        """编辑模板"""
        # TODO: 实现编辑模板
        pass
        
    def on_execute(self, instance):
        """执行命令列表"""
        if not self.app:
            self.app = self._get_app()
            
        commands = self.app.workgroup_manager.get_cmd_list()
        
        if not commands:
            return
            
        # 创建执行器
        from lib.command_executor import CommandExecutor
        if not hasattr(self, 'executor'):
            self.executor = CommandExecutor(self.app)
            
        # 开始执行
        success, message = self.executor.execute_command_list(
            commands,
            log_callback=self.on_log,
            status_callback=self.on_status
        )
        
        if success:
            self.exec_btn.disabled = True
            self.pause_btn.disabled = False
            self.stop_btn.disabled = False
            
    def on_pause(self, instance):
        """暂停/恢复执行"""
        if hasattr(self, 'executor'):
            if self.executor.is_paused():
                self.executor.resume()
                self.pause_btn.text = '暂停'
            else:
                self.executor.pause()
                self.pause_btn.text = '恢复'
                
    def on_stop(self, instance):
        """停止执行"""
        if hasattr(self, 'executor'):
            self.executor.stop()
            self.exec_btn.disabled = False
            self.pause_btn.disabled = True
            self.stop_btn.disabled = True
            self.pause_btn.text = '暂停'
            
    def on_log(self, message):
        """日志回调"""
        current_text = self.log_label.text
        self.log_label.text = current_text + '\n' + message
        
    def on_status(self, status):
        """状态回调"""
        self.status_label.text = f'状态: {status}'
        
    def _get_app(self):
        """获取App实例"""
        from kivy.app import App
        return App.get_running_app()
