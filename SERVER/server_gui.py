#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激活系统服务端管理界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from models import db, ActivationCode
from config import Config
from datetime import datetime
import secrets
import string
import os
import json


def _get_server_url():
    """获取服务端地址"""
    return 'https://9793tg1lo456.vicp.fun'


CLOUD_SERVER_URL = _get_server_url()


class ServerManagerGUI:
    """服务端管理GUI"""

    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.root.title("激活系统服务端管理")
        self.root.geometry("1000x700")

        # 创建主容器
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建标签页
        self.create_activation_code_tab()
        self.create_user_management_tab()
        self.create_reports_tab()
        self.create_activation_codes_list_tab()
        self.create_backup_tab()
        self.create_workgroup_tab()

    def create_activation_code_tab(self):
        """创建激活码生成标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='生成激活码')

        # 主框架
        main_frame = tk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        tk.Label(main_frame, text="生成激活码", font=('Arial', 24, 'bold')).pack(pady=20)

        # 数量设置
        quantity_frame = tk.Frame(main_frame)
        quantity_frame.pack(pady=20)

        tk.Label(quantity_frame, text="生成数量：", font=('Arial', 12)).pack(side=tk.LEFT, padx=5)
        self.quantity_var = tk.StringVar(value="1")
        tk.Entry(quantity_frame, textvariable=self.quantity_var, width=15).pack(side=tk.LEFT, padx=5)
        tk.Label(quantity_frame, text="（范围：1-9999）", font=('Arial', 10), fg='gray').pack(side=tk.LEFT, padx=5)

        # 生成按钮
        tk.Button(
            quantity_frame,
            text="生成激活码",
            command=self.generate_activation_codes,
            bg='#28a745', fg='white', width=20, height=2
        ).pack(side=tk.LEFT, padx=20)

        # 激活码显示区域
        result_frame = tk.LabelFrame(main_frame, text="生成的激活码", font=('Arial', 12, 'bold'))
        result_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        self.codes_text = scrolledtext.ScrolledText(result_frame, width=80, height=20, font=('Courier New', 11))
        self.codes_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 按钮框架
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="复制全部",
            command=self.copy_all_codes,
            bg='#007bff', fg='white', width=15
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="清空",
            command=self.clear_codes,
            bg='#6c757d', fg='white', width=15
        ).pack(side=tk.LEFT, padx=5)

        # 统计信息
        self.stats_label = tk.Label(main_frame, text="已生成：0 个", font=('Arial', 11), fg='#666')
        self.stats_label.pack(pady=10)

        self.generated_codes = []

    def create_user_management_tab(self):
        """创建用户管理标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='用户管理')

        # 主框架
        main_frame = tk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        tk.Label(main_frame, text="用户管理", font=('Arial', 24, 'bold')).pack(pady=20)

        # 统计信息
        self.user_stats_label = tk.Label(
            main_frame,
            text="总用户: 0 | 正常: 0 | 禁用: 0",
            font=('Arial', 12, 'bold'),
            fg='#007bff'
        )
        self.user_stats_label.pack(pady=10)

        # 表格框架
        table_frame = tk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 创建Treeview
        columns = ('ID', '用户名', '邮箱', '状态', '剩余天数', '注册时间')
        self.user_tree = ttk.Treeview(table_frame, columns=columns, show='headings')

        # 设置列标题和宽度
        self.user_tree.heading('ID', text='ID')
        self.user_tree.column('ID', width=60, anchor='center')

        self.user_tree.heading('用户名', text='用户名')
        self.user_tree.column('用户名', width=120, anchor='center')

        self.user_tree.heading('邮箱', text='邮箱')
        self.user_tree.column('邮箱', width=200, anchor='center')

        self.user_tree.heading('状态', text='状态')
        self.user_tree.column('状态', width=80, anchor='center')

        self.user_tree.heading('剩余天数', text='剩余天数')
        self.user_tree.column('剩余天数', width=80, anchor='center')

        self.user_tree.heading('注册时间', text='注册时间')
        self.user_tree.column('注册时间', width=180, anchor='center')

        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.user_tree.yview)
        self.user_tree.configure(yscroll=scrollbar.set)

        # 布局
        self.user_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 按钮框架
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame,
            text="刷新列表",
            command=self.load_users,
            bg='#007bff', fg='white', width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="禁用/启用",
            command=self.toggle_user_status,
            bg='#ffc107', fg='black', width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            button_frame,
            text="删除用户",
            command=self.delete_user,
            bg='#dc3545', fg='white', width=12
        ).pack(side=tk.LEFT, padx=5)

        # 加载数据
        self.load_users()

    def create_reports_tab(self):
        """创建报表标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='报表系统')

        # 主框架
        main_frame = tk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        tk.Label(main_frame, text="报表系统", font=('Arial', 24, 'bold')).pack(pady=20)

        # 说明文字
        info_text = "点击下方按钮生成相应报表，报表将以PDF格式下载。"
        tk.Label(main_frame, text=info_text, font=('Arial', 12), fg='#666').pack(pady=10)

        # 按钮网格
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(pady=30)

        buttons = [
            ("用户注册报告", '#007bff', 'generate_user_report'),
            ("支付报告", '#28a745', 'generate_order_report'),
            ("激活码统计报告", '#ffc107', 'generate_code_report'),
            ("报障表报告", '#dc3545', 'generate_ticket_report')
        ]

        for i, (text, color, command) in enumerate(buttons):
            row = i // 2
            col = i % 2

            tk.Button(
                buttons_frame,
                text=text,
                command=lambda cmd=command: self.generate_report(cmd),
                bg=color, fg='white', width=20, height=2
            ).grid(row=row, column=col, padx=20, pady=20)

        # 一键生成所有报告
        tk.Button(
            main_frame,
            text="一键生成所有报告（ZIP）",
            command=lambda: self.generate_report('generate_all_reports'),
            bg='#6610f2', fg='white', width=30, height=2
        ).pack(pady=20)

        # 状态显示
        self.report_status_label = tk.Label(main_frame, text="", font=('Arial', 11), fg='#666')
        self.report_status_label.pack(pady=10)

    def create_activation_codes_list_tab(self):
        """创建激活码列表标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='激活码列表')

        # 主框架
        main_frame = tk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        tk.Label(main_frame, text="激活码列表", font=('Arial', 24, 'bold')).pack(pady=20)

        # 统计信息
        stats_frame = tk.Frame(main_frame)
        stats_frame.pack(pady=10)

        with self.app.app_context():
            total_codes = ActivationCode.query.count()
            unused_codes = ActivationCode.query.filter_by(status='unused').count()
            used_codes = ActivationCode.query.filter_by(status='used').count()

        tk.Label(stats_frame, text=f"总计：{total_codes} 个  |  未使用：{unused_codes} 个  |  已使用：{used_codes} 个",
                font=('Arial', 12, 'bold'), fg='#007bff').pack()

        # 表格
        table_frame = tk.Frame(main_frame)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 创建Treeview
        columns = ('ID', '激活码', '状态', '创建时间', '关联订单')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')

        # 设置列标题和宽度
        self.tree.heading('ID', text='ID')
        self.tree.column('ID', width=60, anchor='center')

        self.tree.heading('激活码', text='激活码')
        self.tree.column('激活码', width=200, anchor='center')

        self.tree.heading('状态', text='状态')
        self.tree.column('状态', width=100, anchor='center')

        self.tree.heading('创建时间', text='创建时间')
        self.tree.column('创建时间', width=180, anchor='center')

        self.tree.heading('关联订单', text='关联订单')
        self.tree.column('关联订单', width=150, anchor='center')

        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        # 布局
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 刷新按钮
        tk.Button(
            main_frame,
            text="刷新列表",
            command=self.load_activation_codes,
            bg='#007bff', fg='white', width=15
        ).pack(pady=10)

    def generate_activation_codes(self):
        """生成激活码 - 通过云端API"""
        try:
            quantity = int(self.quantity_var.get())
            if quantity < 1 or quantity > 9999:
                messagebox.showerror("错误", "生成数量必须在1-9999之间")
                return
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数量")
            return

        if not messagebox.askyesno("确认", f"确定要生成 {quantity} 个激活码吗？"):
            return

        try:
            import requests
            
            # 创建session以保持cookie
            session = requests.Session()
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # 先尝试访问健康检查接口
            try:
                health_url = f"{CLOUD_SERVER_URL}/api/health"
                session.get(health_url, headers=headers, timeout=10)
            except:
                pass
            
            url = f"{CLOUD_SERVER_URL}/api/admin/codes/generate"
            response = session.post(url, json={'quantity': quantity}, headers=headers, timeout=30)
            
            # 尝试解析JSON
            try:
                result = response.json()
            except ValueError:
                messagebox.showerror("错误", f"服务器返回非JSON响应，可能是CloudBase安全中间页拦截。\n\n请在浏览器中先访问以下地址并确认安全：\n{CLOUD_SERVER_URL}/api/health")
                return

            if result.get('success'):
                new_codes = result.get('data', {}).get('codes', [])
                # 显示生成的激活码
                self.generated_codes.extend(new_codes)
                self.display_codes(new_codes)
                messagebox.showinfo("成功", f"成功生成 {len(new_codes)} 个激活码！\n\n激活码已保存到云端数据库。")
            else:
                messagebox.showerror("错误", result.get('message', '生成失败'))

        except Exception as e:
            messagebox.showerror("错误", f"生成激活码失败：{str(e)}")

    def display_codes(self, codes):
        """显示激活码"""
        for code in codes:
            self.codes_text.insert(tk.END, code + "\n")
        self.codes_text.see(tk.END)
        self.stats_label.config(text=f"本次已生成：{len(self.generated_codes)} 个")

    def copy_all_codes(self):
        """复制所有生成的激活码"""
        if not self.generated_codes:
            messagebox.showinfo("提示", "还没有生成任何激活码")
            return

        all_codes = "\n".join(self.generated_codes)
        self.root.clipboard_clear()
        self.root.clipboard_append(all_codes)
        messagebox.showinfo("成功", f"已复制 {len(self.generated_codes)} 个激活码到剪贴板！")

    def clear_codes(self):
        """清空显示的激活码"""
        self.codes_text.delete("1.0", tk.END)
        self.generated_codes = []
        self.stats_label.config(text="已生成：0 个")

    def load_users(self):
        """加载用户列表"""
        try:
            import requests
            url = f"{CLOUD_SERVER_URL}/api/admin/users"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    users = result.get('data', {}).get('users', [])

                    # 清空现有数据
                    for item in self.user_tree.get_children():
                        self.user_tree.delete(item)

                    # 更新统计信息
                    total_users = len(users)
                    active_users = sum(1 for u in users if u['is_active'])
                    disabled_users = total_users - active_users

                    self.user_stats_label.config(
                        text=f"总用户: {total_users} | 正常: {active_users} | 禁用: {disabled_users}"
                    )

                    # 加载用户数据
                    for user in users:
                        status = "正常" if user['is_active'] else "禁用"
                        status_color = "#28a745" if user['is_active'] else "#dc3545"

                        # 格式化时间
                        created_at = user.get('created_at', '')
                        if created_at:
                            from datetime import datetime
                            try:
                                dt = datetime.fromisoformat(created_at)
                                created_at = dt.strftime('%Y-%m-%d %H:%M')
                            except:
                                created_at = created_at[:10]

                        self.user_tree.insert('', tk.END, values=(
                            user['id'],
                            user['username'],
                            user['email'],
                            status,
                            user['days_remaining'],
                            created_at
                        ))

                    # 设置状态列的颜色标签
                    self.user_tree.tag_configure('active', foreground='#28a745')
                    self.user_tree.tag_configure('disabled', foreground='#dc3545')

            else:
                messagebox.showerror("错误", f"加载用户列表失败：HTTP {response.status_code}")

        except Exception as e:
            messagebox.showerror("错误", f"加载用户列表失败：{str(e)}")

    def toggle_user_status(self):
        """禁用/启用用户"""
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个用户")
            return

        if len(selection) > 1:
            messagebox.showwarning("提示", "请只选择一个用户")
            return

        item = self.user_tree.item(selection[0])
        values = item['values']
        user_id = values[0]
        username = values[1]
        current_status = values[3]

        if not messagebox.askyesno(
            "确认",
            f"确定要{current_status}用户 '{username}' 吗？\n\n禁用后该用户将无法登录和使用激活功能。"
        ):
            return

        try:
            import requests
            url = f"{CLOUD_SERVER_URL}/api/admin/user/toggle"

            response = requests.post(url, json={'user_id': user_id}, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    messagebox.showinfo("成功", result.get('message', '操作成功'))
                    self.load_users()
                else:
                    messagebox.showerror("错误", result.get('message', '操作失败'))
            else:
                messagebox.showerror("错误", f"操作失败：HTTP {response.status_code}")

        except Exception as e:
            messagebox.showerror("错误", f"操作失败：{str(e)}")

    def delete_user(self):
        """删除用户"""
        selection = self.user_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个用户")
            return

        if len(selection) > 1:
            messagebox.showwarning("提示", "请只选择一个用户")
            return

        item = self.user_tree.item(selection[0])
        values = item['values']
        user_id = values[0]
        username = values[1]

        if not messagebox.askyesno(
            "确认删除",
            f"确定要删除用户 '{username}' 吗？\n\n此操作不可恢复，将同时删除该用户的所有数据！"
        ):
            return

        try:
            import requests
            url = f"{CLOUD_SERVER_URL}/api/admin/user/delete"

            response = requests.post(url, json={'user_id': user_id}, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    messagebox.showinfo("成功", result.get('message', '删除成功'))
                    self.load_users()
                else:
                    messagebox.showerror("错误", result.get('message', '删除失败'))
            else:
                messagebox.showerror("错误", f"删除失败：HTTP {response.status_code}")

        except Exception as e:
            messagebox.showerror("错误", f"删除失败：{str(e)}")

    def generate_report(self, report_type):
        """生成报表"""
        self.report_status_label.config(text="正在生成报表...", fg='#007bff')
        self.root.update()

        try:
            import requests
            base_url = CLOUD_SERVER_URL

            report_urls = {
                'generate_user_report': '/reports/report/users',
                'generate_order_report': '/reports/report/orders',
                'generate_code_report': '/reports/report/codes',
                'generate_ticket_report': '/reports/report/tickets',
                'generate_all_reports': '/reports/report/all'
            }

            url = base_url + report_urls.get(report_type, '')

            if not url:
                messagebox.showerror("错误", "无效的报表类型")
                return

            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                # 保存文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"report_{report_type}_{timestamp}.pdf" if 'all' not in report_type else f"all_reports_{timestamp}.zip"

                with open(filename, 'wb') as f:
                    f.write(response.content)

                self.report_status_label.config(text=f"报表已生成：{filename}", fg='#28a745')
                messagebox.showinfo("成功", f"报表已生成并保存：\n{filename}")
            else:
                self.report_status_label.config(text="报表生成失败", fg='#dc3545')
                messagebox.showerror("错误", f"报表生成失败：HTTP {response.status_code}")

        except Exception as e:
            self.report_status_label.config(text="报表生成失败", fg='#dc3545')
            messagebox.showerror("错误", f"报表生成失败：{str(e)}")

    def load_activation_codes(self):
        """加载激活码列表 - 通过云端API"""
        # 清空现有数据
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            import requests
            
            # 创建session以保持cookie
            session = requests.Session()
            url = f"{CLOUD_SERVER_URL}/api/admin/codes/list?per_page=1000"
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # 先尝试访问健康检查接口，获取可能的cookie
            try:
                health_url = f"{CLOUD_SERVER_URL}/api/health"
                session.get(health_url, headers=headers, timeout=10)
            except:
                pass
            
            # 再请求实际API
            response = session.get(url, headers=headers, timeout=15)
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"加载激活码列表失败: HTTP {response.status_code}")
                return
            
            # 尝试解析JSON
            try:
                result = response.json()
            except ValueError:
                # 如果不是JSON，可能是安全中间页，尝试从HTML中提取或跳过
                if 'text/html' in response.headers.get('Content-Type', ''):
                    print("提示: 遇到CloudBase安全中间页，请尝试:")
                    print("1. 在浏览器中先访问该地址并确认安全")
                    print("2. 或在CloudBase控制台绑定自定义域名")
                    print(f"URL: {url}")
                else:
                    print(f"响应不是JSON格式: {response.text[:200]}")
                return

            if result.get('success'):
                codes = result.get('data', {}).get('codes', [])

                status_map = {
                    'unused': '未使用',
                    'used': '已使用',
                    'expired': '已过期'
                }

                for code in codes:
                    order_no = code.get('order_no', '无') or '无'
                    self.tree.insert('', tk.END, values=(
                        code.get('id'),
                        code.get('code'),
                        status_map.get(code.get('status'), code.get('status')),
                        code.get('created_at'),
                        order_no
                    ))
                print(f"成功加载 {len(codes)} 个激活码")
            else:
                print(f"加载激活码列表失败: {result.get('message')}")

        except Exception as e:
            print(f"加载激活码列表失败: {str(e)}")

    def create_backup_tab(self):
        """创建自动备份标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='自动备份')

        # 主框架
        main_frame = tk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 标题
        tk.Label(main_frame, text="数据库备份管理", font=('Arial', 24, 'bold')).pack(pady=20)

        # 说明文字
        info_text = "系统每天凌晨4点自动备份数据库，您也可以手动进行备份和恢复操作。"
        tk.Label(main_frame, text=info_text, font=('Arial', 12), fg='#666').pack(pady=10)

        # 按钮框架
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=20)

        tk.Button(
            button_frame,
            text="立即备份",
            command=self.manual_backup,
            bg='#28a745', fg='white', width=15, height=2
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            button_frame,
            text="恢复数据库",
            command=self.restore_database,
            bg='#007bff', fg='white', width=15, height=2
        ).pack(side=tk.LEFT, padx=10)

        # 备份文件列表
        list_frame = tk.LabelFrame(main_frame, text="备份文件列表", font=('Arial', 12, 'bold'))
        list_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        # 创建Treeview
        columns = ('文件名', '大小', '创建时间')
        self.backup_tree = ttk.Treeview(list_frame, columns=columns, show='headings')

        # 设置列标题和宽度
        self.backup_tree.heading('文件名', text='文件名')
        self.backup_tree.column('文件名', width=300, anchor='w')

        self.backup_tree.heading('大小', text='大小')
        self.backup_tree.column('大小', width=120, anchor='center')

        self.backup_tree.heading('创建时间', text='创建时间')
        self.backup_tree.column('创建时间', width=180, anchor='center')

        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.backup_tree.yview)
        self.backup_tree.configure(yscroll=scrollbar.set)

        # 布局
        self.backup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 操作按钮
        ops_frame = tk.Frame(main_frame)
        ops_frame.pack(pady=10)

        tk.Button(
            ops_frame,
            text="刷新列表",
            command=self.load_backup_files,
            bg='#007bff', fg='white', width=12
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            ops_frame,
            text="删除备份",
            command=self.delete_backup,
            bg='#dc3545', fg='white', width=12
        ).pack(side=tk.LEFT, padx=5)

        # 加载备份文件列表
        self.load_backup_files()

        # 启动自动备份定时任务
        self.start_auto_backup()

    def get_backup_dir(self):
        """获取备份目录"""
        backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backups')
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        return backup_dir

    def get_db_path(self):
        """获取数据库路径"""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'activation.db')

    def manual_backup(self):
        """手动备份"""
        if not messagebox.askyesno("确认", "确定要立即备份数据库吗？"):
            return

        try:
            import requests
            url = f"{CLOUD_SERVER_URL}/api/backup/manual"

            response = requests.post(url, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    messagebox.showinfo("成功", result.get('message', '备份成功'))
                    self.load_backup_files()
                else:
                    messagebox.showerror("错误", result.get('message', '备份失败'))
            else:
                messagebox.showerror("错误", f"备份失败：HTTP {response.status_code}")

        except Exception as e:
            messagebox.showerror("错误", f"备份失败：{str(e)}")

    def restore_database(self):
        """恢复数据库"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个备份文件")
            return

        if len(selection) > 1:
            messagebox.showwarning("提示", "请只选择一个备份文件")
            return

        item = self.backup_tree.item(selection[0])
        values = item['values']
        filename = values[0]

        if not messagebox.askyesno(
            "确认恢复",
            f"确定要恢复备份文件 '{filename}' 吗？\n\n"
            f"⚠️ 警告：当前数据库将被备份，然后替换为选定的备份文件！\n\n"
            f"此操作不可撤销，请谨慎操作！"
        ):
            return

        try:
            import requests
            url = f"{CLOUD_SERVER_URL}/api/backup/restore"

            response = requests.post(url, json={'filename': filename}, timeout=60)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    messagebox.showinfo("成功", result.get('message', '恢复成功') + "\n\n请重启服务以使更改生效！")
                    self.load_backup_files()
                else:
                    messagebox.showerror("错误", result.get('message', '恢复失败'))
            else:
                messagebox.showerror("错误", f"恢复失败：HTTP {response.status_code}")

        except Exception as e:
            messagebox.showerror("错误", f"恢复失败：{str(e)}")

    def load_backup_files(self):
        """加载备份文件列表"""
        try:
            import requests
            url = f"{CLOUD_SERVER_URL}/api/backup/list"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    backups = result.get('data', {}).get('backups', [])

                    # 清空现有数据
                    for item in self.backup_tree.get_children():
                        self.backup_tree.delete(item)

                    # 加载备份文件
                    for backup in backups:
                        self.backup_tree.insert('', tk.END, values=(
                            backup['filename'],
                            backup['size'],
                            backup['created_time']
                        ))
                else:
                    messagebox.showerror("错误", result.get('message', '加载备份列表失败'))
            else:
                messagebox.showerror("错误", f"加载备份列表失败：HTTP {response.status_code}")

        except Exception as e:
            messagebox.showerror("错误", f"加载备份列表失败：{str(e)}")

    def delete_backup(self):
        """删除备份文件"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个备份文件")
            return

        if len(selection) > 1:
            messagebox.showwarning("提示", "请只选择一个备份文件")
            return

        item = self.backup_tree.item(selection[0])
        values = item['values']
        filename = values[0]

        if not messagebox.askyesno(
            "确认删除",
            f"确定要删除备份文件 '{filename}' 吗？\n\n此操作不可恢复！"
        ):
            return

        try:
            import requests
            url = f"{CLOUD_SERVER_URL}/api/backup/delete"

            response = requests.post(url, json={'filename': filename}, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    messagebox.showinfo("成功", result.get('message', '删除成功'))
                    self.load_backup_files()
                else:
                    messagebox.showerror("错误", result.get('message', '删除失败'))
            else:
                messagebox.showerror("错误", f"删除失败：HTTP {response.status_code}")

        except Exception as e:
            messagebox.showerror("错误", f"删除失败：{str(e)}")

    def start_auto_backup(self):
        """启动自动备份定时任务"""
        from datetime import datetime, timedelta
        import time

        def auto_backup_worker():
            """自动备份工作线程"""
            while True:
                try:
                    now = datetime.now()
                    # 计算距离凌晨4点的秒数
                    target_time = now.replace(hour=4, minute=0, second=0, microsecond=0)
                    if now > target_time:
                        target_time += timedelta(days=1)

                    wait_seconds = (target_time - now).total_seconds()
                    print(f"[自动备份] 下次备份时间: {target_time.strftime('%Y-%m-%d %H:%M:%S')}, 等待 {wait_seconds} 秒")

                    time.sleep(wait_seconds)

                    # 执行备份
                    print(f"[自动备份] 开始执行自动备份...")
                    import requests
                    url = f"{CLOUD_SERVER_URL}/api/backup/manual"

                    response = requests.post(url, timeout=60)
                    print(f"[自动备份] 备份完成: {response.text}")

                except Exception as e:
                    print(f"[自动备份] 错误: {str(e)}")

        # 启动自动备份线程
        import threading
        backup_thread = threading.Thread(target=auto_backup_worker, daemon=True)
        backup_thread.start()
        print("[自动备份] 自动备份定时任务已启动，每天凌晨4点执行")


    def create_workgroup_tab(self):
        """创建工作组管理标签页"""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text='工作组')

        main_frame = tk.Frame(tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        tk.Label(main_frame, text="工作组管理", font=('Arial', 24, 'bold')).pack(pady=20)

        # 刷新按钮
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='刷新列表', command=self.load_workgroups,
                  font=('Arial', 12), width=15).pack(side=tk.LEFT, padx=5)

        # Treeview
        columns = ('id', 'name', 'password', 'creator', 'member_count', 'sync_dir', 'created_at', 'status')
        self.wg_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)
        self.wg_tree.heading('id', text='ID')
        self.wg_tree.heading('name', text='工作组名称')
        self.wg_tree.heading('password', text='进入口令')
        self.wg_tree.heading('creator', text='创建者')
        self.wg_tree.heading('member_count', text='人数')
        self.wg_tree.heading('sync_dir', text='同步目录')
        self.wg_tree.heading('created_at', text='创建时间')
        self.wg_tree.heading('status', text='状态')

        self.wg_tree.column('id', width=50)
        self.wg_tree.column('name', width=120)
        self.wg_tree.column('password', width=120)
        self.wg_tree.column('creator', width=100)
        self.wg_tree.column('member_count', width=60)
        self.wg_tree.column('sync_dir', width=250)
        self.wg_tree.column('created_at', width=160)
        self.wg_tree.column('status', width=80)

        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.wg_tree.yview)
        self.wg_tree.configure(yscrollcommand=scrollbar.set)
        self.wg_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def load_workgroups(self):
        """加载工作组列表"""
        try:
            import requests
            resp = requests.get(f'{CLOUD_SERVER_URL}/api/admin/workgroups', timeout=10)
            print(f"工作组请求状态码: {resp.status_code}")
            if resp.status_code != 200:
                print(f"加载工作组列表失败: HTTP {resp.status_code} - {resp.text[:200]}")
                return
            try:
                result = resp.json()
            except Exception:
                print(f"加载工作组列表失败: 服务器返回非JSON - {resp.text[:200]}")
                return
            if result.get('success'):
                # 清空
                for item in self.wg_tree.get_children():
                    self.wg_tree.delete(item)
                for wg in result.get('data', {}).get('workgroups', []):
                    status = '启用' if wg.get('is_active') else '禁用'
                    self.wg_tree.insert('', tk.END, values=(
                        wg.get('id'),
                        wg.get('name'),
                        wg.get('password'),
                        wg.get('creator'),
                        wg.get('member_count', 0),
                        wg.get('sync_dir', ''),
                        wg.get('created_at', ''),
                        status
                    ))
                print(f"成功加载 {len(result.get('data', {}).get('workgroups', []))} 个工作组")
            else:
                print(f"加载工作组列表失败: {result.get('message')}")
        except Exception as e:
            print(f"加载工作组列表失败: {str(e)}")


def main():
    """主函数"""
    from app import create_app
    import time

    # 创建Flask应用
    app = create_app()

    # 在后台线程运行Flask服务器
    def run_flask():
        app.run(host=Config.SERVER_HOST, port=Config.SERVER_PORT, debug=False, use_reloader=False)

    import threading
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print(f"Flask服务器已启动在 {CLOUD_SERVER_URL}")
    print(f"本地监听地址: http://{Config.SERVER_HOST}:{Config.SERVER_PORT}")
    
    # 等待Flask服务就绪
    import requests
    max_retries = 10
    for i in range(max_retries):
        try:
            r = requests.get("http://127.0.0.1:5000/api/health", timeout=2)
            if r.status_code == 200:
                print("Flask服务已就绪")
                break
        except:
            pass
        time.sleep(0.5)
    else:
        print("警告: Flask服务启动超时，继续启动GUI...")

    # 创建主窗口
    root = tk.Tk()
    gui = ServerManagerGUI(root, app)

    print("GUI管理界面已启动")
    
    # 延迟加载激活码列表（等待所有服务就绪）
    def delayed_load():
        try:
            gui.load_activation_codes()
            print("激活码列表加载完成")
        except Exception as e:
            print(f"激活码列表加载失败: {e}")
    
    root.after(1000, delayed_load)

    # 运行GUI
    root.mainloop()


if __name__ == '__main__':
    main()
