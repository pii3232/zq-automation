"""核心引擎模块：AI引擎、执行引擎、图像识别、键盘引擎"""
import os
import time
import random
from typing import Optional, Tuple, List, Dict
from datetime import datetime

import requests
import pyautogui
import cv2
import numpy as np
from PIL import Image
import ctypes
from ctypes import windll

torch = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class AIEngine:
    def __init__(self, config):
        self.config = config
        # 使用 models\multimodal 作为模型路径
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(base_dir, 'models', 'multimodal')
        self.device = "cpu"
        self.model = None
        self.processor = None
        self.last_request_time = 0
        self.min_request_interval = 0.5
        self.max_retries = 3
        self.retry_delay = 1.0

        # 百度千帆API客户端
        self.qianfan_client = None
        if OpenAI and os.environ.get('QIANFAN_API_KEY'):
            try:
                self.qianfan_client = OpenAI(
                    base_url=os.environ.get('QIANFAN_BASE_URL', 'https://qianfan.baidubce.com/v2'),
                    api_key=os.environ.get('QIANFAN_API_KEY')
                )
                print("百度千帆API客户端已初始化")
            except Exception as e:
                print(f"百度千帆API初始化失败: {e}")

        # 不在初始化时自动加载模型，统一由 main.py 的 load_multimodal_model() 控制
        print("AIEngine: 初始化完成，等待主程序控制模型加载")

    def chat(self, messages: List[Dict], system_prompt: str = None) -> str:
        global torch
        if torch is None:
            import torch as _torch
            torch = _torch
        
        if not self.model or not self.processor:
            return "模型未加载"
        
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        if system_prompt:
            messages_list = [{"role": "system", "content": system_prompt}] + messages
        else:
            messages_list = messages
        
        text = self.processor.apply_chat_template(
            messages_list,
            tokenize=False,
            add_generation_prompt=True
        )
        
        inputs = self.processor(text=[text], return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=2048,
                do_sample=True,
                temperature=0.7,
                top_p=0.95
            )
        
        generated_ids = [output_ids[len(input_ids):] 
                        for input_ids, output_ids in zip(inputs['input_ids'], output_ids)]
        
        output_text = self.processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]
        
        self.last_request_time = time.time()
        return output_text


class ExecutionEngine:
    """鼠标操作执行引擎"""
    def __init__(self, config):
        self.config = config
        pyautogui.PAUSE = 0.1
        pyautogui.FAILSAFE = True
        # 确保pyautogui使用主屏幕
        pyautogui.FAILSAFE = False
        
        # 调试信息
        print(f"[ExecutionEngine] 初始化，屏幕大小: {pyautogui.size()}")
        print(f"[ExecutionEngine] pyautogui版本: {pyautogui.__version__}")
        
    def click(self, x: int, y: int):
        try:
            pyautogui.click(x, y)
            print(f"点击: ({x}, {y})")
            time.sleep(0.05)
        except Exception as e:
            print(f"点击失败: {e}")
        
    def double_click(self, x: int, y: int):
        try:
            pyautogui.doubleClick(x, y)
            print(f"双击: ({x}, {y})")
            time.sleep(0.05)
        except Exception as e:
            print(f"双击失败: {e}")
        
    def drag_to(self, x1: int, y1: int, x2: int, y2: int):
        """从坐标(x1, y1)拖动到坐标(x2, y2)"""
        try:
            pyautogui.moveTo(x1, y1)
            time.sleep(0.05)
            pyautogui.drag(x2 - x1, y2 - y1, duration=0.3)
            print(f"拖动: ({x1}, {y1}) -> ({x2}, {y2})")
            time.sleep(0.05)
        except Exception as e:
            print(f"拖动失败: {e}")
        
    def scroll(self, x1: int, y1: int, x2: int, y2: int):
        dx = x2 - x1
        dy = y2 - y1
        pyautogui.scroll(dy // 10, x=x1, y=y1)
        
    def screenshot(self, save_path: str = None):
        screenshot = pyautogui.screenshot()
        if save_path:
            screenshot.save(save_path)
        return screenshot
    
    def find_and_click_multiple_images(self, image_paths: List[str], timeout: int = 10,
                                       confidence: float = None) -> Dict:
        """查找多张图片并点击第一个找到的"""
        try:
            print(f"[ExecutionEngine] 开始查找多张图片: {[os.path.basename(p) for p in image_paths]}")
            
            # 创建ImageRecognition实例
            from engines import ImageRecognition
            image_recognition = ImageRecognition(self.config)
            
            # 查找多张图片
            result = image_recognition.find_multiple_images(image_paths, timeout, confidence)
            
            if result:
                x, y, found_image = result
                print(f"[ExecutionEngine] 找到图片: {os.path.basename(found_image)}, 坐标: ({x}, {y})")
                
                # 点击找到的坐标
                self.click(x, y)
                
                return {
                    'success': True,
                    'x': x,
                    'y': y,
                    'image': found_image,
                    'message': f'找到并点击了 {os.path.basename(found_image)}'
                }
            else:
                print(f"[ExecutionEngine] 未找到任何图片")
                return {
                    'success': False,
                    'error': f'在{timeout}秒内未找到任何图片',
                    'message': '未找到任何匹配的图片'
                }
                
        except Exception as e:
            print(f"[ExecutionEngine] 多图查找失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'message': f'多图查找失败: {e}'
            }


class KeyboardEngine:
    """键盘操作执行引擎"""
    def __init__(self, config):
        self.config = config
        
    def type(self, text: str):
        pyautogui.typewrite(text)
        
    def press(self, key: str):
        pyautogui.press(key)


class ImageRecognition:
    """图像识别引擎"""
    def __init__(self, config):
        self.config = config
        
    def find_image(self, image_path: str, timeout: int = 10, 
                   confidence: float = None, mode: str = 'normal') -> Optional[Tuple[int, int]]:
        """
        查找图片
        Args:
            image_path: 图片路径
            timeout: 超时时间（秒）
            confidence: 相似度阈值
            mode: 查找模式 - 'trigger'（触发模式，单次找图）或 'normal'（正常模式，多种算法轮换）
        """
        if confidence is None:
            confidence = self.config.global_similarity / 100.0
        
        if not os.path.exists(image_path):
            print(f"图片文件不存在: {image_path}")
            return None
        
        # 读取模板图片
        template = cv2.imread(image_path)
        if template is None:
            print(f"无法读取图片: {image_path}")
            return None
        
        h, w = template.shape[:2]
        
        start_time = time.time()
        attempt_count = 0
        
        if mode == 'trigger':
            # 触发模式：只执行一次找图，使用指定的相似度
            try:
                # 截取屏幕
                screenshot = pyautogui.screenshot()
                screen_np = np.array(screenshot)
                screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
                
                # 使用默认算法（TemplateMatching）
                algo = cv2.TM_CCOEFF_NORMED
                result = cv2.matchTemplate(screen_cv2, template, algo)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val >= confidence:
                    # 计算中心坐标
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    print(f"找到图片: 相似度 {max_val:.3f}, 坐标 ({int(center_x)}, {int(center_y)})")
                    return (int(center_x), int(center_y))
                else:
                    print(f"未找到: 相似度 {max_val:.3f} < 阈值 {confidence}")
                    return None
                    
            except Exception as e:
                print(f"找图出错: {e}")
                return None
        
        else:
            # 正常模式：多种算法轮换，相似度0.9-0.8-0.7
            print("正常模式：执行多种算法轮换找图...")
            
            # 定义算法列表和相似度轮换
            algorithms = [
                (cv2.TM_CCOEFF_NORMED, "TM_CCOEFF_NORMED"),
                (cv2.TM_CCORR_NORMED, "TM_CCORR_NORMED"),
                (cv2.TM_SQDIFF_NORMED, "TM_SQDIFF_NORMED")
            ]
            confidences = [0.9, 0.8, 0.7]
            
            while time.time() - start_time < timeout:
                try:
                    attempt_count += 1
                    print(f"第{attempt_count}次尝试...")
                    
                    # 截取屏幕
                    screenshot = pyautogui.screenshot()
                    screen_np = np.array(screenshot)
                    screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
                    
                    # 尝试不同算法和相似度
                    found = False
                    coords = None
                    
                    for algo_idx, (algo, algo_name) in enumerate(algorithms):
                        for conf_idx, conf_val in enumerate(confidences):
                            try:
                                print(f"尝试算法 {algo_name}, 相似度 {conf_val}")
                                
                                # 模板匹配
                                result = cv2.matchTemplate(screen_cv2, template, algo)
                                
                                # 根据不同算法类型获取最佳匹配位置
                                if algo in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                                    # 平方差算法：值越小越匹配
                                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                                    match_val = 1.0 - min_val  # 转换为相似度（越大越匹配）
                                    match_loc = min_loc
                                else:
                                    # 其他算法：值越大越匹配
                                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                                    match_val = max_val
                                    match_loc = max_loc
                                
                                print(f"相似度: {match_val:.3f}")
                                
                                if match_val >= conf_val:
                                    # 计算中心坐标
                                    center_x = match_loc[0] + w // 2
                                    center_y = match_loc[1] + h // 2
                                    print(f"找到图片，算法: {algo_name}, 相似度: {match_val:.3f}, 坐标: ({int(center_x)}, {int(center_y)})")
                                    
                                    # 只返回坐标，不执行点击（点击由调用方处理）
                                    coords = (int(center_x), int(center_y))
                                    found = True
                                    break
                                else:
                                    # 延时50ms后尝试下一个相似度
                                    if conf_idx < len(confidences) - 1:
                                        print(f"相似度不足，延时50ms后尝试更低相似度")
                                        time.sleep(0.05)
                                
                            except Exception as e:
                                print(f"算法 {algo_name} 出错: {e}")
                                continue
                        
                        if found:
                            break
                        
                        # 延时50ms后尝试下一个算法
                        if algo_idx < len(algorithms) - 1:
                            print(f"当前算法未找到，延时50ms后尝试下一个算法")
                            time.sleep(0.05)
                    
                    if found:
                        return coords
                    
                    # 等待后重试（0.5秒）
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"查找出错: {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(0.5)
            
            print(f"超时未找到图片: {image_path}")
            return None
    
    def find_multiple_images(self, image_paths: List[str], timeout: int = 10,
                              confidence: float = None) -> Optional[Tuple[int, int, str]]:
        """查找多张图片，返回第一个找到的坐标和文件名"""
        if confidence is None:
            confidence = self.config.global_similarity / 100.0
        
        print(f"查找多张图片: {image_paths}, 超时: {timeout}s, 相似度: {confidence}")
        
        # 过滤不存在的图片
        valid_images = []
        for img_path in image_paths:
            if os.path.exists(img_path):
                valid_images.append(img_path)
            else:
                print(f"图片文件不存在: {img_path}")
        
        if not valid_images:
            print("没有有效的图片文件")
            return None
        
        # 读取所有模板图片
        templates = []
        for img_path in valid_images:
            template = cv2.imread(img_path)
            if template is not None:
                h, w = template.shape[:2]
                templates.append((img_path, template, w, h))
                print(f"加载图片: {os.path.basename(img_path)}, 尺寸: {w}x{h}")
            else:
                print(f"无法读取图片: {img_path}")
        
        if not templates:
            print("没有成功加载任何模板图片")
            return None
        
        start_time = time.time()
        attempt_count = 0
        
        while time.time() - start_time < timeout:
            try:
                attempt_count += 1
                print(f"第{attempt_count}次尝试查找多张图片...")
                
                # 截取屏幕
                screenshot = pyautogui.screenshot()
                screen_np = np.array(screenshot)
                screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
                
                # 遍历所有模板，查找匹配
                for img_path, template, w, h in templates:
                    # 模板匹配
                    result = cv2.matchTemplate(screen_cv2, template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    print(f"  {os.path.basename(img_path)}: 相似度 {max_val:.3f}")
                    
                    if max_val >= confidence:
                        # 计算中心坐标
                        center_x = max_loc[0] + w // 2
                        center_y = max_loc[1] + h // 2
                        print(f"✓ 找到图片: {os.path.basename(img_path)}, 坐标: ({int(center_x)}, {int(center_y)})")
                        return (int(center_x), int(center_y), img_path)
                
                # 等待后重试
                time.sleep(0.5)
                
            except Exception as e:
                print(f"查找出错: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.5)
        
        print(f"超时未找到任何图片")
        return None


    def find_image_in_range(self, image_path: str, x: int, y: int, 
                           search_range: int = 300, timeout: int = 10,
                           confidence: float = None) -> Optional[Tuple[int, int]]:
        if confidence is None:
            confidence = self.config.global_similarity / 100.0
        
        start_time = time.time()
        template = cv2.imread(image_path)
        if template is None:
            print(f"无法读取图片: {image_path}")
            return None
            
        th, tw = template.shape[:2]
        
        while time.time() - start_time < timeout:
            try:
                region_x = max(0, x - search_range // 2)
                region_y = max(0, y - search_range // 2)
                screenshot = pyautogui.screenshot(region=(region_x, region_y, search_range, search_range))
                screen_np = np.array(screenshot)
                screen_cv2 = cv2.cvtColor(screen_np, cv2.COLOR_RGB2BGR)
                
                scales = [1.0, 0.95, 0.90, 0.85, 0.80, 0.75]
                best_match = None
                best_val = 0
                best_template_shape = None
                
                for scale in scales:
                    if scale == 1.0:
                        scaled_template = template
                    else:
                        new_width = int(template.shape[1] * scale)
                        new_height = int(template.shape[0] * scale)
                        if new_width < 10 or new_height < 10:
                            continue
                        scaled_template = cv2.resize(template, (new_width, new_height))
                    
                    result = cv2.matchTemplate(screen_cv2, scaled_template, cv2.TM_CCOEFF_NORMED)
                    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                    
                    if max_val > best_val:
                        best_val = max_val
                        best_match = max_loc
                        best_template_shape = scaled_template.shape
                
                if best_val >= confidence:
                    match_x, match_y = best_match
                    th, tw = best_template_shape[:2]
                    center_x = region_x + match_x + tw // 2
                    center_y = region_y + match_y + th // 2
                    print(f"在范围内找到图片，坐标: ({int(center_x)}, {int(center_y)})")
                    return (int(center_x), int(center_y))
                    
            except Exception as e:
                print(f"在范围内查找图片出错: {e}")
                
            time.sleep(0.5)
            
        return None
