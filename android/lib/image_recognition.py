"""
图像识别模块
移植PC端的找图算法，使用OpenCV
"""
import os
import cv2
import numpy as np
from kivy.logger import Logger
from kivy.graphics.texture import Texture
from PIL import Image


class ImageRecognition:
    """图像识别引擎"""
    
    def __init__(self, config):
        self.config = config
        self.similarity = config.global_similarity / 100.0
        
        # 定义算法列表（与PC端一致）
        self.algorithms = [
            (cv2.TM_CCOEFF_NORMED, "TM_CCOEFF_NORMED"),
            (cv2.TM_CCORR_NORMED, "TM_CCORR_NORMED"),
            (cv2.TM_SQDIFF_NORMED, "TM_SQDIFF_NORMED")
        ]
        
        Logger.info('ImageRecognition: 初始化成功')
        
    def find_image(self, template_path, screenshot=None, threshold=None, mode='normal'):
        """
        查找图片
        
        Args:
            template_path: 模板图片路径
            screenshot: 屏幕截图（numpy数组），如果为None则自动截图
            threshold: 相似度阈值（0-1）
            mode: 查找模式 - 'trigger'(单次) 或 'normal'(多次尝试)
            
        Returns:
            (found, x, y) 或 (False, None, None)
        """
        if threshold is None:
            threshold = self.similarity
            
        # 检查模板文件
        if not os.path.exists(template_path):
            Logger.error(f'ImageRecognition: 模板文件不存在 - {template_path}')
            return (False, None, None)
            
        # 加载模板
        template = cv2.imread(template_path)
        if template is None:
            Logger.error(f'ImageRecognition: 无法读取模板文件 - {template_path}')
            return (False, None, None)
            
        # 获取屏幕截图
        if screenshot is None:
            screenshot = self._take_screenshot()
            if screenshot is None:
                Logger.error('ImageRecognition: 截图失败')
                return (False, None, None)
                
        # 执行模板匹配
        if mode == 'trigger':
            # 触发模式：单次查找
            return self._match_template(screenshot, template, threshold)
        else:
            # 正常模式：多种算法轮换，相似度递减
            return self._multi_match_template(screenshot, template)
            
    def _take_screenshot(self):
        """截取屏幕"""
        try:
            # 通过Android桥接截图
            app = None
            try:
                from kivy.app import App
                app = App.get_running_app()
            except:
                pass
                
            if app and hasattr(app, 'android_bridge') and app.android_bridge:
                screenshot_path = app.android_bridge.take_screenshot()
                if screenshot_path and os.path.exists(screenshot_path):
                    screenshot = cv2.imread(screenshot_path)
                    # 删除临时文件
                    try:
                        os.remove(screenshot_path)
                    except:
                        pass
                    return screenshot
                    
            Logger.warning('ImageRecognition: Android桥接不可用，无法截图')
            return None
            
        except Exception as e:
            Logger.error(f'ImageRecognition: 截图失败 - {e}')
            return None
            
    def _match_template(self, screen, template, threshold):
        """单次模板匹配"""
        try:
            result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            Logger.debug(f'ImageRecognition: 相似度 {max_val:.3f}, 阈值 {threshold}')
            
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                Logger.info(f'ImageRecognition: 找到图片，坐标 ({center_x}, {center_y})')
                return (True, center_x, center_y)
            else:
                Logger.debug(f'ImageRecognition: 未找到，相似度 {max_val:.3f} < {threshold}')
                return (False, None, None)
                
        except Exception as e:
            Logger.error(f'ImageRecognition: 模板匹配失败 - {e}')
            return (False, None, None)
            
    def _multi_match_template(self, screen, template):
        """多次模板匹配（多种算法轮换）"""
        # 相似度阈值列表（与PC端一致）
        thresholds = [0.9, 0.8, 0.7]
        
        for threshold in thresholds:
            for algo, algo_name in self.algorithms:
                try:
                    result = cv2.matchTemplate(screen, template, algo)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    # 对于TM_SQDIFF_NORMED，值越小越好
                    if algo == cv2.TM_SQDIFF_NORMED:
                        if min_val <= (1 - threshold):
                            h, w = template.shape[:2]
                            center_x = min_loc[0] + w // 2
                            center_y = min_loc[1] + h // 2
                            Logger.info(f'ImageRecognition: 找到图片({algo_name})，坐标 ({center_x}, {center_y})')
                            return (True, center_x, center_y)
                    else:
                        if max_val >= threshold:
                            h, w = template.shape[:2]
                            center_x = max_loc[0] + w // 2
                            center_y = max_loc[1] + h // 2
                            Logger.info(f'ImageRecognition: 找到图片({algo_name})，坐标 ({center_x}, {center_y})')
                            return (True, center_x, center_y)
                            
                except Exception as e:
                    Logger.error(f'ImageRecognition: 算法{algo_name}匹配失败 - {e}')
                    continue
                    
        Logger.debug('ImageRecognition: 多次查找未找到图片')
        return (False, None, None)
        
    def find_image_in_range(self, template_path, x, y, search_range=300, threshold=None):
        """
        在指定范围内查找图片
        
        Args:
            template_path: 模板图片路径
            x, y: 中心坐标
            search_range: 搜索范围（像素）
            threshold: 相似度阈值
            
        Returns:
            (found, x, y) 或 (False, None, None)
        """
        if threshold is None:
            threshold = self.similarity
            
        # 检查模板文件
        if not os.path.exists(template_path):
            Logger.error(f'ImageRecognition: 模板文件不存在 - {template_path}')
            return (False, None, None)
            
        # 加载模板
        template = cv2.imread(template_path)
        if template is None:
            Logger.error(f'ImageRecognition: 无法读取模板文件 - {template_path}')
            return (False, None, None)
            
        # 获取屏幕截图
        screenshot = self._take_screenshot()
        if screenshot is None:
            return (False, None, None)
            
        # 计算搜索区域
        h, w = screenshot.shape[:2]
        th, tw = template.shape[:2]
        
        x1 = max(0, int(x - search_range))
        y1 = max(0, int(y - search_range))
        x2 = min(w, int(x + search_range))
        y2 = min(h, int(y + search_range))
        
        # 裁剪搜索区域
        search_region = screenshot[y1:y2, x1:x2]
        
        # 在区域内查找
        try:
            result = cv2.matchTemplate(search_region, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # 转换为全屏坐标
                match_x = x1 + max_loc[0] + tw // 2
                match_y = y1 + max_loc[1] + th // 2
                Logger.info(f'ImageRecognition: 在范围内找到图片，坐标 ({match_x}, {match_y})')
                return (True, match_x, match_y)
            else:
                Logger.debug(f'ImageRecognition: 范围内未找到，相似度 {max_val:.3f}')
                return (False, None, None)
                
        except Exception as e:
            Logger.error(f'ImageRecognition: 范围查找失败 - {e}')
            return (False, None, None)
            
    def multi_find_image(self, template_path, max_attempts=3):
        """
        多次查找图片（相似度递减）
        与PC端的multi_find_image函数对应
        
        Args:
            template_path: 模板图片路径
            max_attempts: 最大尝试次数
            
        Returns:
            (found, x, y) 或 (False, None, None)
        """
        # 相似度阈值列表
        thresholds = [0.9, 0.8, 0.7]
        
        for i, threshold in enumerate(thresholds[:max_attempts]):
            Logger.info(f'ImageRecognition: 第{i+1}次查找，相似度阈值 {threshold}')
            
            found, x, y = self.find_image(template_path, threshold=threshold, mode='trigger')
            if found:
                return (True, x, y)
                
            # 等待1秒后重试
            if i < max_attempts - 1:
                import time
                time.sleep(1)
                
        Logger.info('ImageRecognition: 多次查找均未找到')
        return (False, None, None)
        
    @staticmethod
    def load_image(image_path):
        """加载图片为numpy数组"""
        return cv2.imread(image_path)
        
    @staticmethod
    def save_image(image, save_path):
        """保存图片"""
        cv2.imwrite(save_path, image)
        
    @staticmethod
    def numpy_to_texture(image):
        """将numpy数组转换为Kivy纹理"""
        # OpenCV使用BGR，需要转换为RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 翻转图像（Kivy坐标系）
        image_rgb = np.flip(image_rgb, 0)
        
        # 创建纹理
        texture = Texture.create(size=(image.shape[1], image.shape[0]), colorfmt='rgb')
        texture.blit_buffer(image_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
        
        return texture
