"""配置管理模块"""
import json
import os


class Config:
    def __init__(self, config_path='config.json'):
        self.config_path = config_path

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # 调试：打印 load_multimodal_model 的值
        load_multimodal_value = config.get('load_multimodal_model', False)
        print(f"[Config调试] 读取 load_multimodal_model: {load_multimodal_value}")
        print(f"[Config调试] 类型: {type(load_multimodal_value)}")


        self.api_key = config['api_key']
        self.base_url = config['base_url']
        self.model = config['model']
        self.max_tokens = config['max_tokens']
        self.temperature = config['temperature']
        self.top_p = config['top_p']
        self.database_path = config['database_path']
        self.projects_directory = config['projects_directory']
        # 如果项目目录为projects，设置projects\pic为图片默认目录
        if self.projects_directory == 'projects':
            self.pic_directory = 'projects\\pic'
            # 自动保存修改后的配置
            config['pic_directory'] = self.pic_directory
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        else:
            self.pic_directory = config['pic_directory']
        self.default_timeout = config['default_timeout']
        self.search_range = config['search_range']
        self.random_delay_min = config['random_delay_min']
        self.random_delay_max = config['random_delay_max']
        self.show_mouse_coordinates = config.get('show_mouse_coordinates', True)
        self.global_similarity = config.get('global_similarity', 90)
        self.global_interval = config.get('global_interval', 100)  # 默认100ms
        self.daily_tasks_main_switch_enabled = config.get('daily_tasks_main_switch_enabled', True)
        self.daily_tasks_loop_enabled = config.get('daily_tasks_loop_enabled', False)
        self.daily_tasks_repeat_count = config.get('daily_tasks_repeat_count', 1)
        self.daily_tasks_time_mode = config.get('daily_tasks_time_mode', 'none')
        self.daily_tasks_schedule_time = config.get('daily_tasks_schedule_time', '')
        self.daily_tasks_delay_minutes = config.get('daily_tasks_delay_minutes', 60)
        self.answer_tasks_main_switch_enabled = config.get('answer_tasks_main_switch_enabled', True)
        self.answer_tasks_loop_enabled = config.get('answer_tasks_loop_enabled', False)
        self.answer_tasks_repeat_count = config.get('answer_tasks_repeat_count', 1)
        self.answer_tasks_time_mode = config.get('answer_tasks_time_mode', 'none')
        self.answer_tasks_schedule_time = config.get('answer_tasks_schedule_time', '')
        self.answer_tasks_delay_minutes = config.get('answer_tasks_delay_minutes', 60)
        
        # 发现即点任务配置
        self.discovery_tasks_main_switch_enabled = config.get('discovery_tasks_main_switch_enabled', True)
        self.discovery_tasks_loop_enabled = config.get('discovery_tasks_loop_enabled', False)
        self.discovery_tasks_repeat_count = config.get('discovery_tasks_repeat_count', 1)
        self.discovery_tasks_time_mode = config.get('discovery_tasks_time_mode', 'none')
        self.discovery_tasks_schedule_time = config.get('discovery_tasks_schedule_time', '')
        self.discovery_tasks_delay_minutes = config.get('discovery_tasks_delay_minutes', 60)

        # 多模态大模型配置
        self.load_multimodal_model = config.get('load_multimodal_model', False)
        
        # OpenAI API 配置
        self.use_openai_api = config.get('use_openai_api', False)
        self.api_provider = config.get('api_provider', '百度API')
        self.api_base_url = config.get('api_base_url', '')
        self.api_key = config.get('api_key', '')
        self.api_model = config.get('api_model', 'gpt-3.5-turbo')
        self.api_enable_thinking = config.get('api_enable_thinking', False)
        
        # 各API提供商的独立配置
        self.api_base_url_baidu = config.get('api_base_url_baidu', 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/')
        self.api_key_baidu = config.get('api_key_baidu', '')
        self.api_model_baidu = config.get('api_model_baidu', 'deepseek-v3.2-think')
        
        self.api_base_url_xiaomi = config.get('api_base_url_xiaomi', '')
        self.api_key_xiaomi = config.get('api_key_xiaomi', '')
        self.api_model_xiaomi = config.get('api_model_xiaomi', '')
        
        self.api_base_url_xunfei = config.get('api_base_url_xunfei', 'https://spark-api-open.xf-yun.com/v2/')
        self.api_key_xunfei = config.get('api_key_xunfei', '')
        self.api_model_xunfei = config.get('api_model_xunfei', 'spark-x')
        
        self.api_base_url_zhipu = config.get('api_base_url_zhipu', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')
        self.api_key_zhipu = config.get('api_key_zhipu', '')
        self.api_model_zhipu = config.get('api_model_zhipu', 'glm-4')

    def save(self):
        """保存配置到文件"""
        # 先读取现有的配置文件（如果存在），保留其中的所有字段
        existing_config = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
            except Exception as e:
                print(f"读取现有配置文件失败: {e}，将创建新配置文件")
        
        # 更新配置字段
        existing_config.update({
            'api_key': self.api_key,
            'base_url': self.base_url,
            'model': self.model,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'database_path': self.database_path,
            'pic_directory': self.pic_directory,
            'projects_directory': self.projects_directory,
            'default_timeout': self.default_timeout,
            'search_range': self.search_range,
            'random_delay_min': self.random_delay_min,
            'random_delay_max': self.random_delay_max,
            'show_mouse_coordinates': self.show_mouse_coordinates,
            'global_similarity': self.global_similarity,
            'global_interval': self.global_interval,
            'daily_tasks_main_switch_enabled': self.daily_tasks_main_switch_enabled,
            'daily_tasks_loop_enabled': self.daily_tasks_loop_enabled,
            'daily_tasks_repeat_count': self.daily_tasks_repeat_count,
            'daily_tasks_time_mode': self.daily_tasks_time_mode,
            'daily_tasks_schedule_time': self.daily_tasks_schedule_time,
            'daily_tasks_delay_minutes': self.daily_tasks_delay_minutes,
            'answer_tasks_main_switch_enabled': self.answer_tasks_main_switch_enabled,
            'answer_tasks_loop_enabled': self.answer_tasks_loop_enabled,
            'answer_tasks_repeat_count': self.answer_tasks_repeat_count,
            'answer_tasks_time_mode': self.answer_tasks_time_mode,
            'answer_tasks_schedule_time': self.answer_tasks_schedule_time,
            'answer_tasks_delay_minutes': self.answer_tasks_delay_minutes,
            'discovery_tasks_main_switch_enabled': self.discovery_tasks_main_switch_enabled,
            'discovery_tasks_loop_enabled': self.discovery_tasks_loop_enabled,
            'discovery_tasks_repeat_count': self.discovery_tasks_repeat_count,
            'discovery_tasks_time_mode': self.discovery_tasks_time_mode,
            'discovery_tasks_schedule_time': self.discovery_tasks_schedule_time,
            'discovery_tasks_delay_minutes': self.discovery_tasks_delay_minutes,
            'load_multimodal_model': self.load_multimodal_model,
            'use_openai_api': self.use_openai_api,
            'api_provider': self.api_provider,
            'api_base_url': self.api_base_url,
            'api_key': self.api_key,
            'api_model': self.api_model,
            'api_enable_thinking': self.api_enable_thinking,
            'api_base_url_baidu': self.api_base_url_baidu,
            'api_key_baidu': self.api_key_baidu,
            'api_model_baidu': self.api_model_baidu,
            'api_base_url_xiaomi': self.api_base_url_xiaomi,
            'api_key_xiaomi': self.api_key_xiaomi,
            'api_model_xiaomi': self.api_model_xiaomi,
            'api_base_url_xunfei': self.api_base_url_xunfei,
            'api_key_xunfei': self.api_key_xunfei,
            'api_model_xunfei': self.api_model_xunfei,
            'api_base_url_zhipu': self.api_base_url_zhipu,
            'api_key_zhipu': self.api_key_zhipu,
            'api_model_zhipu': self.api_model_zhipu
        })

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(existing_config, f, ensure_ascii=False, indent=2)
