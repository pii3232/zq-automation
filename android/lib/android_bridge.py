"""
Android API桥接模块
使用Pyjnius调用Android原生API
"""
import os
from kivy.logger import Logger

try:
    from jnius import autoclass, cast
    ANDROID_AVAILABLE = True
except ImportError:
    ANDROID_AVAILABLE = False
    Logger.warning('AndroidBridge: Pyjnius不可用，Android功能将受限')


class AndroidBridge:
    """Android API桥接类"""
    
    def __init__(self):
        if not ANDROID_AVAILABLE:
            self.available = False
            return
            
        try:
            # 导入Android类
            self.PythonActivity = autoclass('org.kivy.android.PythonActivity')
            self.Intent = autoclass('android.content.Intent')
            self.Settings = autoclass('android.provider.Settings')
            self.Uri = autoclass('android.net.Uri')
            self.Build = autoclass('android.os.Build')
            self.Environment = autoclass('android.os.Environment')
            self.MediaStore = autoclass('android.provider.MediaStore')
            self.ContentValues = autoclass('android.content.ContentValues')
            self.Bitmap = autoclass('android.graphics.Bitmap')
            self.Canvas = autoclass('android.graphics.Canvas')
            self.Rect = autoclass('android.graphics.Rect')
            self.PackageManager = autoclass('android.content.pm.PackageManager')
            self.PermissionChecker = autoclass('android.content.pm.PermissionChecker')
            
            # 获取Activity和Context
            self.activity = self.PythonActivity.mActivity
            self.context = self.activity.getApplicationContext()
            
            # 悬窗服务相关
            self.float_service = None
            self.float_service_intent = None
            
            # Accessibility服务
            self.accessibility_service = None
            
            self.available = True
            Logger.info('AndroidBridge: 初始化成功')
            
        except Exception as e:
            self.available = False
            Logger.error(f'AndroidBridge: 初始化失败 - {e}')
            
    def request_permissions(self):
        """请求必要的权限"""
        if not self.available:
            return False
            
        try:
            # 需要请求的权限列表
            permissions = [
                'android.permission.READ_EXTERNAL_STORAGE',
                'android.permission.WRITE_EXTERNAL_STORAGE',
                'android.permission.CAMERA',
                'android.permission.SYSTEM_ALERT_WINDOW',
                'android.permission.INTERNET',
                'android.permission.ACCESS_NETWORK_STATE'
            ]
            
            # 检查并请求权限
            if self.Build.VERSION.SDK_INT >= 23:
                not_granted = []
                for perm in permissions:
                    if self.context.checkSelfPermission(perm) != self.PermissionChecker.PERMISSION_GRANTED:
                        not_granted.append(perm)
                        
                if not_granted:
                    self.activity.requestPermissions(not_granted, 1)
                    Logger.info(f'AndroidBridge: 请求权限 - {not_granted}')
                    
            # 请求悬浮窗权限
            if self.Build.VERSION.SDK_INT >= 23:
                if not self.Settings.canDrawOverlays(self.activity):
                    intent = self.Intent(
                        self.Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        self.Uri.parse('package:' + self.activity.getPackageName())
                    )
                    self.activity.startActivityForResult(intent, 2)
                    Logger.info('AndroidBridge: 请求悬浮窗权限')
                    
            # 请求Accessibility服务
            self._request_accessibility_permission()
            
            return True
            
        except Exception as e:
            Logger.error(f'AndroidBridge: 请求权限失败 - {e}')
            return False
            
    def _request_accessibility_permission(self):
        """请求Accessibility服务权限"""
        try:
            if not self._is_accessibility_enabled():
                intent = self.Intent(self.Settings.ACTION_ACCESSIBILITY_SETTINGS)
                self.activity.startActivity(intent)
                Logger.info('AndroidBridge: 请手动开启Accessibility服务')
        except Exception as e:
            Logger.error(f'AndroidBridge: 请求Accessibility权限失败 - {e}')
            
    def _is_accessibility_enabled(self):
        """检查Accessibility服务是否已启用"""
        try:
            expected_service = f'{self.activity.getPackageName()}/.service.AutomationAccessibilityService'
            enabled_services = self.Settings.Secure.getString(
                self.activity.getContentResolver(),
                self.Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
            )
            return expected_service in (enabled_services or '')
        except:
            return False
            
    def take_screenshot(self):
        """截取屏幕"""
        if not self.available:
            return None
            
        try:
            # 方法1: 使用MediaProjection API (需要用户授权)
            # 方法2: 使用Accessibility服务的截图功能
            # 方法3: 使用adb shell screencap (需要root)
            
            # 这里使用Accessibility服务的截图功能
            if self.accessibility_service and self.accessibility_service.takeScreenshot():
                # 等待截图完成
                import time
                time.sleep(0.5)
                # 返回截图文件路径
                screenshot_path = os.path.join(
                    self.context.getExternalFilesDir(None).getAbsolutePath(),
                    'screenshot.png'
                )
                if os.path.exists(screenshot_path):
                    return screenshot_path
                    
            Logger.warning('AndroidBridge: 截图失败，Accessibility服务未就绪')
            return None
            
        except Exception as e:
            Logger.error(f'AndroidBridge: 截图失败 - {e}')
            return None
            
    def tap(self, x, y):
        """模拟点击"""
        if not self.available:
            return False
            
        try:
            if self.accessibility_service:
                return self.accessibility_service.performClick(int(x), int(y))
            else:
                Logger.warning('AndroidBridge: 点击失败，Accessibility服务未就绪')
                return False
        except Exception as e:
            Logger.error(f'AndroidBridge: 点击失败 - {e}')
            return False
            
    def swipe(self, start_x, start_y, end_x, end_y, duration=300):
        """模拟滑动"""
        if not self.available:
            return False
            
        try:
            if self.accessibility_service:
                return self.accessibility_service.performSwipe(
                    int(start_x), int(start_y), int(end_x), int(end_y), duration
                )
            else:
                Logger.warning('AndroidBridge: 滑动失败，Accessibility服务未就绪')
                return False
        except Exception as e:
            Logger.error(f'AndroidBridge: 滑动失败 - {e}')
            return False
            
    def input_text(self, text):
        """输入文本"""
        if not self.available:
            return False
            
        try:
            if self.accessibility_service:
                return self.accessibility_service.inputText(text)
            else:
                Logger.warning('AndroidBridge: 输入失败，Accessibility服务未就绪')
                return False
        except Exception as e:
            Logger.error(f'AndroidBridge: 输入失败 - {e}')
            return False
            
    def start_float_window(self):
        """启动悬浮窗"""
        if not self.available:
            return False
            
        try:
            # 启动悬浮窗服务
            FloatService = autoclass('org.zq.zqautomation.service.FloatWindowService')
            self.float_service_intent = self.Intent(self.context, FloatService)
            
            if self.Build.VERSION.SDK_INT >= 26:
                self.context.startForegroundService(self.float_service_intent)
            else:
                self.context.startService(self.float_service_intent)
                
            Logger.info('AndroidBridge: 悬浮窗服务已启动')
            return True
            
        except Exception as e:
            Logger.error(f'AndroidBridge: 启动悬浮窗失败 - {e}')
            return False
            
    def stop_float_window(self):
        """停止悬浮窗"""
        if not self.available or not self.float_service_intent:
            return False
            
        try:
            self.context.stopService(self.float_service_intent)
            Logger.info('AndroidBridge: 悬浮窗服务已停止')
            return True
        except Exception as e:
            Logger.error(f'AndroidBridge: 停止悬浮窗失败 - {e}')
            return False
            
    def update_float_window_status(self, status, color):
        """更新悬浮窗状态"""
        if not self.available:
            return False
            
        try:
            if self.float_service:
                self.float_service.updateStatus(status, color)
                return True
        except Exception as e:
            Logger.error(f'AndroidBridge: 更新悬浮窗状态失败 - {e}')
            return False
            
    def get_screen_size(self):
        """获取屏幕尺寸"""
        if not self.available:
            return (1080, 1920)
            
        try:
            display = self.activity.getWindowManager().getDefaultDisplay()
            point = autoclass('android.graphics.Point')()
            display.getRealSize(point)
            return (point.x, point.y)
        except Exception as e:
            Logger.error(f'AndroidBridge: 获取屏幕尺寸失败 - {e}')
            return (1080, 1920)
            
    def vibrate(self, duration=100):
        """振动"""
        if not self.available:
            return False
            
        try:
            vibrator = self.context.getSystemService(self.context.VIBRATOR_SERVICE)
            if vibrator.hasVibrator():
                vibrator.vibrate(duration)
            return True
        except Exception as e:
            Logger.error(f'AndroidBridge: 振动失败 - {e}')
            return False
            
    def show_toast(self, message):
        """显示Toast消息"""
        if not self.available:
            return False
            
        try:
            Toast = autoclass('android.widget.Toast')
            Toast.makeText(self.context, message, Toast.LENGTH_SHORT).show()
            return True
        except Exception as e:
            Logger.error(f'AndroidBridge: 显示Toast失败 - {e}')
            return False
