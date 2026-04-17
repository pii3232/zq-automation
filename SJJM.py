"""
手机镜像 - 安卓设备屏幕投影工具 (PyQt5版本)
通过ADB TCP连接安卓设备，实时显示设备屏幕
"""
import sys
import os
import subprocess
import threading
import time
import re
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QGroupBox, QFrame,
    QScrollArea, QComboBox, QFileDialog
)
from PyQt5.QtGui import QPixmap, QImage, QIcon, QGuiApplication, QPainter, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QPoint, QRect

from PIL import Image
import io
import cv2
import numpy as np

# ADB路径
ADB_PATH = r'E:\platform-tools\adb.exe'

# 截图保存目录
PIC_DIRECTORY = r'E:\5-ZDZS-TXA5\3MCWB\pic'


class ScreenshotLabel(QLabel):
    """支持框选截图和测试找图的Label"""
    
    selection_finished = pyqtSignal(int, int, int, int)  # x, y, w, h
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        self.screenshot_mode = False
        self.setMouseTracking(True)
        
        # 测试找图结果
        self.test_results = []  # [(x, y, w, h, similarity), ...]
    
    def start_screenshot_mode(self):
        """进入截图模式"""
        self.screenshot_mode = True
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        self.setCursor(Qt.CrossCursor)
        self.grabKeyboard()
        self.update()
    
    def stop_screenshot_mode(self):
        """退出截图模式"""
        self.screenshot_mode = False
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        self.setCursor(Qt.ArrowCursor)
        self.releaseKeyboard()
        self.update()
    
    def set_test_results(self, results):
        """设置测试找图结果"""
        self.test_results = results
        self.update()
    
    def clear_test_results(self):
        """清除测试结果"""
        self.test_results = []
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        
        # 绘制测试找图结果（绿色框）
        if self.test_results:
            for result in self.test_results:
                x, y, w, h, similarity = result
                # 绿色边框
                pen = QPen(QColor(0, 255, 0), 3)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(x, y, w, h)
                
                # 显示坐标和相似度
                painter.setPen(QColor(0, 255, 0))
                font = QFont()
                font.setPointSize(12)
                font.setBold(True)
                painter.setFont(font)
                label_text = f'({x},{y}) {similarity:.2f}'
                painter.drawText(x + 5, y - 5, label_text)
        
        # 绘制框选区域（截图模式）- 只显示边框，透明
        if self.screenshot_mode and self.start_pos and self.end_pos:
            x = min(self.start_pos.x(), self.end_pos.x())
            y = min(self.start_pos.y(), self.end_pos.y())
            w = abs(self.end_pos.x() - self.start_pos.x())
            h = abs(self.end_pos.y() - self.start_pos.y())
            
            # 只显示红色边框，不填充遮罩
            pen = QPen(Qt.red, 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(x, y, w, h)
            
            # 显示尺寸
            painter.setPen(Qt.white)
            font = QFont()
            font.setPointSize(10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(x + 5, y + 18, f'{w} x {h}')
    
    def mousePressEvent(self, event):
        if self.screenshot_mode and event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.is_selecting = True
            self.update()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.screenshot_mode and self.is_selecting:
            self.end_pos = event.pos()
            self.update()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if self.screenshot_mode and event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            
            if self.start_pos and self.end_pos:
                x = min(self.start_pos.x(), self.end_pos.x())
                y = min(self.start_pos.y(), self.end_pos.y())
                w = abs(self.end_pos.x() - self.start_pos.x())
                h = abs(self.end_pos.y() - self.start_pos.y())
                
                if w > 5 and h > 5:
                    self.selection_finished.emit(x, y, w, h)
                    return
            
            self.stop_screenshot_mode()
        else:
            super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        if self.screenshot_mode and event.key() == Qt.Key_Escape:
            self.stop_screenshot_mode()
        else:
            super().keyPressEvent(event)


class WorkerSignals(QObject):
    """工作线程信号"""
    log = pyqtSignal(str)
    image_ready = pyqtSignal(bytes)


class PhoneMirrorApp(QMainWindow):
    """手机镜像应用主类"""
    
    def __init__(self):
        super().__init__()
        
        # 设备相关
        self.device_ip = '192.168.3.21'
        self.device_port = '5555'
        self.connected = False
        self.device_name = ''
        self.screen_width = 2248
        self.screen_height = 1080
        
        # 投影相关
        self.projection_running = False
        self.projection_thread = None
        
        # 当前截图
        self.current_pixmap = None
        self.current_cv_image = None  # OpenCV格式的图像
        
        # 信号
        self.signals = WorkerSignals()
        self.signals.log.connect(self.append_log)
        self.signals.image_ready.connect(self.update_display)
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle('手机镜像 - SJJM (PyQt5)')
        
        # 左侧面板宽度
        left_panel_width = 450
        # 右侧显示区尺寸（横屏：2248x1080）
        display_width = 2248
        display_height = 1080
        
        # 设置窗口大小
        window_width = left_panel_width + display_width + 20
        window_height = display_height + 50
        self.setFixedSize(window_width, window_height)
        
        try:
            self.setWindowIcon(QIcon('ZQ.bmp'))
        except:
            pass
        
        # 主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # ===== 左侧控制面板 =====
        left_panel = QWidget()
        left_panel.setFixedWidth(left_panel_width)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 设备连接区域
        connect_group = QGroupBox('设备连接')
        connect_layout = QVBoxLayout(connect_group)
        
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel('IP地址:'))
        self.ip_edit = QLineEdit(self.device_ip)
        ip_layout.addWidget(self.ip_edit)
        connect_layout.addLayout(ip_layout)
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel('端口:'))
        self.port_edit = QLineEdit(self.device_port)
        port_layout.addWidget(self.port_edit)
        connect_layout.addLayout(port_layout)
        
        btn_layout = QHBoxLayout()
        self.btn_connect = QPushButton('连接设备')
        self.btn_connect.clicked.connect(self.connect_device)
        btn_layout.addWidget(self.btn_connect)
        
        self.btn_disconnect = QPushButton('断开连接')
        self.btn_disconnect.clicked.connect(self.disconnect_device)
        self.btn_disconnect.setEnabled(False)
        btn_layout.addWidget(self.btn_disconnect)
        connect_layout.addLayout(btn_layout)
        
        # 状态显示（简化）
        self.lbl_status = QLabel('状态: 未连接')
        self.lbl_status.setStyleSheet('color: red;')
        connect_layout.addWidget(self.lbl_status)
        
        left_layout.addWidget(connect_group)
        
        # 投影控制区域（往上挪，去掉设备信息区域）
        projection_group = QGroupBox('投影控制')
        projection_layout = QVBoxLayout(projection_group)
        
        # 开始/停止投影按钮排成一排，缩小
        proj_btn_layout = QHBoxLayout()
        self.btn_start = QPushButton('开始投影')
        self.btn_start.clicked.connect(self.start_projection)
        self.btn_start.setEnabled(False)
        self.btn_start.setFixedWidth(120)
        proj_btn_layout.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton('停止投影')
        self.btn_stop.clicked.connect(self.stop_projection)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setFixedWidth(120)
        proj_btn_layout.addWidget(self.btn_stop)
        
        proj_btn_layout.addStretch()
        projection_layout.addLayout(proj_btn_layout)
        
        fps_layout = QHBoxLayout()
        fps_layout.addWidget(QLabel('刷新间隔(ms):'))
        self.fps_edit = QLineEdit('200')
        self.fps_edit.setFixedWidth(60)
        fps_layout.addWidget(self.fps_edit)
        fps_layout.addStretch()
        projection_layout.addLayout(fps_layout)
        
        left_layout.addWidget(projection_group)
        
        # ===== 测试区域（新增，在截图工具区上面）=====
        test_group = QGroupBox('测试区')
        test_layout = QVBoxLayout(test_group)
        
        # 图片路径输入
        img_path_layout = QHBoxLayout()
        img_path_layout.addWidget(QLabel('图片路径:'))
        self.test_img_edit = QLineEdit()
        self.test_img_edit.setPlaceholderText('输入图片路径或文件名')
        img_path_layout.addWidget(self.test_img_edit)
        
        self.btn_browse = QPushButton('浏览')
        self.btn_browse.setFixedWidth(60)
        self.btn_browse.clicked.connect(self.browse_test_image)
        img_path_layout.addWidget(self.btn_browse)
        test_layout.addLayout(img_path_layout)
        
        # 算法选择
        algo_layout = QHBoxLayout()
        algo_layout.addWidget(QLabel('找图算法:'))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems([
            'TM_CCOEFF_NORMED (推荐)',
            'TM_CCORR_NORMED',
            'TM_SQDIFF_NORMED',
            'TM_CCOEFF',
            'TM_CCORR',
            'TM_SQDIFF'
        ])
        algo_layout.addWidget(self.algo_combo)
        test_layout.addLayout(algo_layout)
        
        # 相似度阈值
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel('相似度阈值:'))
        self.threshold_edit = QLineEdit('0.8')
        self.threshold_edit.setFixedWidth(60)
        threshold_layout.addWidget(self.threshold_edit)
        threshold_layout.addStretch()
        test_layout.addLayout(threshold_layout)
        
        # 测试按钮
        test_btn_layout = QHBoxLayout()
        self.btn_test_find = QPushButton('测试找图')
        self.btn_test_find.clicked.connect(self.test_find_image)
        self.btn_test_find.setFixedWidth(100)
        test_btn_layout.addWidget(self.btn_test_find)
        
        self.btn_clear_test = QPushButton('清除结果')
        self.btn_clear_test.clicked.connect(self.clear_test_results)
        self.btn_clear_test.setFixedWidth(100)
        test_btn_layout.addWidget(self.btn_clear_test)
        
        test_btn_layout.addStretch()
        test_layout.addLayout(test_btn_layout)
        
        # 测试结果标签 - 显示坐标、相似度、耗时
        self.lbl_test_result = QLabel('测试结果: -')
        self.lbl_test_result.setWordWrap(True)
        self.lbl_test_result.setStyleSheet('color: green;')
        test_layout.addWidget(self.lbl_test_result)
        
        left_layout.addWidget(test_group)
        
        # 截图区域
        screenshot_group = QGroupBox('截图工具')
        screenshot_layout = QVBoxLayout(screenshot_group)
        
        self.btn_screenshot = QPushButton('截图')
        self.btn_screenshot.clicked.connect(self.take_screenshot)
        screenshot_layout.addWidget(self.btn_screenshot)
        
        self.lbl_path = QLabel(f'保存目录:\n{PIC_DIRECTORY}')
        self.lbl_path.setWordWrap(True)
        screenshot_layout.addWidget(self.lbl_path)
        
        # 截图显示区 - 自适应，保持宽高比
        self.screenshot_display = QLabel()
        self.screenshot_display.setMinimumHeight(120)
        self.screenshot_display.setMaximumHeight(200)
        self.screenshot_display.setStyleSheet('background-color: #2d2d2d; border: 1px solid #555;')
        self.screenshot_display.setAlignment(Qt.AlignCenter)
        self.screenshot_display.setText('暂无截图')
        self.screenshot_display.setScaledContents(False)  # 不拉伸，保持宽高比
        screenshot_layout.addWidget(self.screenshot_display)
        
        left_layout.addWidget(screenshot_group)
        
        # 日志区域
        log_group = QGroupBox('日志')
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        
        left_layout.addWidget(log_group)
        
        main_layout.addWidget(left_panel)
        
        # ===== 右侧投影区域 =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        display_group = QGroupBox(f'设备屏幕投影 ({display_width}x{display_height})')
        display_layout = QVBoxLayout(display_group)
        display_layout.setContentsMargins(5, 5, 5, 5)
        
        # 图像显示标签 - 支持框选截图和测试找图
        self.image_label = ScreenshotLabel()
        self.image_label.setFixedSize(display_width, display_height)
        self.image_label.setStyleSheet('background-color: #1e1e1e; border: 1px solid #333;')
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setText('请先连接设备并开始投影')
        self.image_label.selection_finished.connect(self.on_selection_finished)
        display_layout.addWidget(self.image_label, alignment=Qt.AlignCenter)
        
        # 坐标显示
        coord_layout = QHBoxLayout()
        self.lbl_coord = QLabel('坐标: (-, -)')
        self.lbl_coord.setStyleSheet('color: blue;')
        coord_layout.addWidget(self.lbl_coord)
        
        self.lbl_device_coord = QLabel('设备坐标: (-, -)')
        self.lbl_device_coord.setStyleSheet('color: green;')
        coord_layout.addWidget(self.lbl_device_coord)
        coord_layout.addStretch()
        
        display_layout.addLayout(coord_layout)
        
        right_layout.addWidget(display_group)
        
        main_layout.addWidget(right_panel)
        
        # 鼠标移动事件
        self.image_label.setMouseTracking(True)
    
    def browse_test_image(self):
        """浏览选择测试图片 - 打开资源管理器"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            '选择测试图片', 
            PIC_DIRECTORY,
            '图片文件 (*.png *.jpg *.jpeg *.bmp);;所有文件 (*.*)'
        )
        if file_path:
            self.test_img_edit.setText(file_path)
            self.log(f'已选择测试图片: {os.path.basename(file_path)}')
    
    def test_find_image(self):
        """测试找图"""
        if self.current_cv_image is None:
            self.log('当前没有设备画面，请先开始投影')
            return
        
        img_path = self.test_img_edit.text().strip()
        if not img_path:
            self.log('请输入图片路径或点击浏览选择文件')
            return
        
        # 如果只输入文件名，则在PIC_DIRECTORY中查找
        if not os.path.isabs(img_path):
            img_path = os.path.join(PIC_DIRECTORY, img_path)
        
        if not os.path.exists(img_path):
            self.log(f'图片不存在: {img_path}')
            return
        
        try:
            # 记录开始时间
            start_time = time.time()
            
            # 读取模板图片
            template = cv2.imread(img_path, cv2.IMREAD_COLOR)
            if template is None:
                self.log(f'无法读取图片: {img_path}')
                return
            
            # 获取选择的算法
            algo_index = self.algo_combo.currentIndex()
            algo_map = [
                cv2.TM_CCOEFF_NORMED,
                cv2.TM_CCORR_NORMED,
                cv2.TM_SQDIFF_NORMED,
                cv2.TM_CCOEFF,
                cv2.TM_CCORR,
                cv2.TM_SQDIFF
            ]
            method = algo_map[algo_index]
            
            # 获取相似度阈值
            try:
                threshold = float(self.threshold_edit.text())
            except:
                threshold = 0.8
            
            # 执行模板匹配
            result = cv2.matchTemplate(self.current_cv_image, template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # 计算耗时
            elapsed_time = (time.time() - start_time) * 1000  # 毫秒
            
            th, tw = template.shape[:2]
            
            # 判断是否为归一化算法（返回值范围0-1）
            is_normed = method in [cv2.TM_CCOEFF_NORMED, cv2.TM_CCORR_NORMED, cv2.TM_SQDIFF_NORMED]
            
            # 对于SQDIFF方法，值越小越好；其他方法值越大越好
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                match_val = min_val
                match_loc = min_loc
                # 对于SQDIFF_NORMED，转换为相似度（1 - 值）
                if is_normed:
                    similarity = 1 - match_val
                else:
                    similarity = None  # 非归一化算法无法计算相似度
            else:
                match_val = max_val
                match_loc = max_loc
                # 对于归一化算法，值本身就是相似度
                if is_normed:
                    similarity = match_val
                else:
                    similarity = None  # 非归一化算法无法计算相似度
            
            # 清除之前的测试结果
            self.image_label.clear_test_results()
            
            # 对于归一化算法使用阈值判断，非归一化算法直接显示最佳匹配
            if is_normed:
                if similarity >= threshold:
                    # 找到匹配
                    results = [(match_loc[0], match_loc[1], tw, th, similarity)]
                    self.image_label.set_test_results(results)
                    
                    result_text = (
                        f'找到匹配! 坐标: ({match_loc[0]}, {match_loc[1]}), '
                        f'尺寸: {tw}x{th}, 相似度: {similarity:.4f}, 耗时: {elapsed_time:.1f}ms'
                    )
                    self.lbl_test_result.setText(result_text)
                    self.lbl_test_result.setStyleSheet('color: green;')
                    self.log(f'测试找图成功: 坐标({match_loc[0]}, {match_loc[1]}), 相似度{similarity:.4f}, 耗时{elapsed_time:.1f}ms')
                else:
                    result_text = (
                        f'未找到匹配. 最高相似度: {similarity:.4f} < {threshold}, 耗时: {elapsed_time:.1f}ms'
                    )
                    self.lbl_test_result.setText(result_text)
                    self.lbl_test_result.setStyleSheet('color: red;')
                    self.log(f'测试找图失败: 最高相似度{similarity:.4f} < 阈值{threshold}, 耗时{elapsed_time:.1f}ms')
            else:
                # 非归一化算法，直接显示最佳匹配位置（不判断阈值）
                results = [(match_loc[0], match_loc[1], tw, th, 1.0)]
                self.image_label.set_test_results(results)
                
                result_text = (
                    f'最佳匹配! 坐标: ({match_loc[0]}, {match_loc[1]}), '
                    f'尺寸: {tw}x{th}, 匹配值: {match_val:.2f}, 耗时: {elapsed_time:.1f}ms (非归一化算法)'
                )
                self.lbl_test_result.setText(result_text)
                self.lbl_test_result.setStyleSheet('color: blue;')
                self.log(f'测试找图: 坐标({match_loc[0]}, {match_loc[1]}), 匹配值{match_val:.2f}, 耗时{elapsed_time:.1f}ms (非归一化算法，无法计算相似度)')
            
        except Exception as e:
            self.log(f'测试找图错误: {e}')
            self.lbl_test_result.setText(f'错误: {e}')
            self.lbl_test_result.setStyleSheet('color: red;')
    
    def clear_test_results(self):
        """清除测试结果"""
        self.image_label.clear_test_results()
        self.lbl_test_result.setText('测试结果: -')
        self.lbl_test_result.setStyleSheet('color: green;')
        self.log('已清除测试结果')
    
    def append_log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.append(f'[{timestamp}] {message}')
    
    def log(self, message):
        """线程安全日志"""
        self.signals.log.emit(message)
    
    def run_adb_command(self, command, timeout=30):
        """执行ADB命令"""
        try:
            result = subprocess.run(
                f'"{ADB_PATH}" {command}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return False, '', '命令超时'
        except Exception as e:
            return False, '', str(e)
    
    def connect_device(self):
        """连接设备"""
        ip = self.ip_edit.text().strip()
        port = self.port_edit.text().strip()
        
        if not ip:
            return
        
        address = f'{ip}:{port}'
        self.log(f'正在连接设备: {address}')
        
        success, stdout, stderr = self.run_adb_command(f'connect {address}')
        
        if success and 'connected' in stdout.lower():
            self.connected = True
            self.device_ip = ip
            self.device_port = port
            self.log(f'连接成功: {stdout}')
            
            success, stdout, stderr = self.run_adb_command(f'-s {ip}:{port} shell getprop ro.product.model')
            if success and stdout:
                self.device_name = stdout.strip()
            else:
                self.device_name = address
            
            self.get_screen_resolution()
            
            self.lbl_status.setText(f'状态: 已连接 ({self.device_name})')
            self.lbl_status.setStyleSheet('color: green;')
            
            self.btn_connect.setEnabled(False)
            self.btn_disconnect.setEnabled(True)
            self.btn_start.setEnabled(True)
            
        else:
            self.log(f'连接失败: {stderr or stdout}')
    
    def disconnect_device(self):
        """断开设备连接"""
        if self.projection_running:
            self.stop_projection()
        
        address = f'{self.device_ip}:{self.device_port}'
        self.log(f'正在断开设备: {address}')
        self.run_adb_command(f'disconnect {address}')
        
        self.connected = False
        self.device_name = ''
        
        self.lbl_status.setText('状态: 未连接')
        self.lbl_status.setStyleSheet('color: red;')
        
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(False)
        
        self.image_label.clear()
        self.image_label.setText('请先连接设备并开始投影')
        self.current_pixmap = None
        self.current_cv_image = None
        
        self.log('设备已断开')
    
    def get_screen_resolution(self):
        """获取设备屏幕分辨率"""
        ip = self.device_ip
        port = self.device_port
        
        success, stdout, stderr = self.run_adb_command(f'-s {ip}:{port} shell wm size')
        
        if success and stdout:
            match = re.search(r'(\d+)x(\d+)', stdout)
            if match:
                w = int(match.group(1))
                h = int(match.group(2))
                if w > h:
                    self.screen_width = w
                    self.screen_height = h
                else:
                    self.screen_width = h
                    self.screen_height = w
                self.log(f'屏幕分辨率: {self.screen_width}x{self.screen_height}')
                return
        
        self.screen_width = 2248
        self.screen_height = 1080
        self.log('无法获取分辨率，使用默认值: 2248x1080')
    
    def start_projection(self):
        """开始投影"""
        if not self.connected:
            return
        
        self.projection_running = True
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        self.log('开始投影...')
        
        self.projection_thread = threading.Thread(target=self.projection_loop, daemon=True)
        self.projection_thread.start()
    
    def stop_projection(self):
        """停止投影"""
        self.projection_running = False
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.log('投影已停止')
    
    def projection_loop(self):
        """投影循环"""
        while self.projection_running:
            try:
                interval = int(self.fps_edit.text()) if self.fps_edit.text().isdigit() else 200
                
                start_time = time.time()
                
                image_data = self.get_screenshot_binary()
                
                if image_data:
                    self.signals.image_ready.emit(image_data)
                
                elapsed = time.time() - start_time
                wait_time = max(0.01, (interval / 1000.0) - elapsed)
                time.sleep(wait_time)
                
            except Exception as e:
                self.log(f'投影错误: {e}')
                time.sleep(1)
    
    def get_screenshot_binary(self):
        """获取屏幕截图（二进制模式）"""
        try:
            process = subprocess.Popen(
                f'"{ADB_PATH}" -s {self.device_ip}:{self.device_port} exec-out screencap -p',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            stdout, stderr = process.communicate(timeout=10)
            
            if process.returncode == 0 and stdout:
                return stdout
            return None
                
        except subprocess.TimeoutExpired:
            process.kill()
            return None
        except Exception:
            return None
    
    def update_display(self, image_data):
        """更新显示"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            data = image.tobytes('raw', 'RGB')
            
            qimage = QImage(data, image.width, image.height, image.width * 3, QImage.Format_RGB888)
            
            pixmap = QPixmap.fromImage(qimage)
            self.current_pixmap = pixmap
            self.image_label.setPixmap(pixmap)
            
            # 同时保存OpenCV格式的图像用于测试找图
            image_cv = Image.open(io.BytesIO(image_data))
            if image_cv.mode != 'RGB':
                image_cv = image_cv.convert('RGB')
            self.current_cv_image = cv2.cvtColor(np.array(image_cv), cv2.COLOR_RGB2BGR)
            
        except Exception as e:
            pass
    
    def take_screenshot(self):
        """截图 - 进入框选模式"""
        if self.current_pixmap is None:
            self.log('当前没有设备画面，请先开始投影')
            return
        
        self.log('进入截图模式，请在右侧显示区框选截图区域（按ESC取消）')
        self.image_label.start_screenshot_mode()
    
    def on_selection_finished(self, x, y, w, h):
        """框选完成"""
        # 退出截图模式
        self.image_label.stop_screenshot_mode()
        
        if self.current_pixmap is None:
            self.log('截图失败：没有画面')
            return
        
        try:
            # 裁剪选中区域
            cropped = self.current_pixmap.copy(x, y, w, h)
            
            # 保存截图
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'screenshot_{timestamp}.png'
            filepath = os.path.join(PIC_DIRECTORY, filename)
            os.makedirs(PIC_DIRECTORY, exist_ok=True)
            cropped.save(filepath)
            
            self.log(f'截图已保存: {filename}')
            
            # 在左侧显示截图
            self.display_screenshot(cropped)
            
        except Exception as e:
            self.log(f'截图失败: {e}')
    
    def display_screenshot(self, pixmap):
        """在左侧显示截图 - 自适应，保持宽高比"""
        if pixmap:
            # 获取显示区域尺寸
            display_w = self.screenshot_display.width() - 2
            display_h = self.screenshot_display.height() - 2
            
            # 缩放显示，保持宽高比
            scaled = pixmap.scaled(
                display_w,
                display_h,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.screenshot_display.setPixmap(scaled)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.projection_running:
            self.stop_projection()
        if self.connected:
            self.disconnect_device()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PhoneMirrorApp()
    window.show()
    sys.exit(app.exec_())
