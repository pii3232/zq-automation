"""
网络管理模块
实现PC端的网络连接逻辑，优先级：花生壳直连 > 局域网直连 > 花生壳域名
"""
import requests
from kivy.logger import Logger
from kivy.clock import Clock


class NetworkManager:
    """网络管理类"""
    
    def __init__(self, config):
        self.config = config
        self.timeout = 10
        self.current_connection = None
        self.connection_status = 'disconnected'
        
        # 连接配置
        self.peanut_direct_config = {
            'url': config.server_url,
            'name': '花生壳直连'
        }
        
        self.local_direct_config = {
            'ip': config.local_server_ip,
            'port': config.local_server_port,
            'name': '局域网直连'
        }
        
        self.peanut_domain_config = {
            'domain': config.peanut_shell_domain,
            'name': '花生壳域名'
        }
        
        Logger.info('NetworkManager: 初始化成功')
        
    def test_connection(self, url):
        """测试连接"""
        try:
            response = requests.get(f'{url}/api/health', timeout=self.timeout)
            if response.status_code == 200:
                return True
        except:
            pass
        return False
        
    def get_best_connection(self):
        """获取最佳连接（按优先级）"""
        connections = []
        
        # 1. 花生壳直连配置
        peanut_url = self.peanut_direct_config['url']
        if peanut_url and self.test_connection(peanut_url):
            self.current_connection = peanut_url
            self.connection_status = 'connected'
            Logger.info(f"NetworkManager: 使用{self.peanut_direct_config['name']}")
            return peanut_url
            
        # 2. 局域网直连
        local_ip = self.local_direct_config['ip']
        local_port = self.local_direct_config['port']
        if local_ip and local_port:
            local_url = f'http://{local_ip}:{local_port}'
            if self.test_connection(local_url):
                self.current_connection = local_url
                self.connection_status = 'connected'
                Logger.info(f"NetworkManager: 使用{self.local_direct_config['name']}")
                return local_url
                
        # 3. 花生壳域名
        domain = self.peanut_domain_config['domain']
        if domain:
            domain_url = f'https://{domain}'
            if self.test_connection(domain_url):
                self.current_connection = domain_url
                self.connection_status = 'connected'
                Logger.info(f"NetworkManager: 使用{self.peanut_domain_config['name']}")
                return domain_url
                
        self.connection_status = 'disconnected'
        Logger.warning('NetworkManager: 所有连接均失败')
        return None
        
    def get(self, endpoint, params=None):
        """发送GET请求"""
        if not self.current_connection:
            self.get_best_connection()
            
        if not self.current_connection:
            return None, '无法连接到服务器'
            
        url = f'{self.current_connection}{endpoint}'
        
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f'HTTP {response.status_code}'
                
        except requests.exceptions.ConnectionError:
            self.connection_status = 'disconnected'
            return None, '无法连接到服务器'
        except requests.exceptions.Timeout:
            return None, '请求超时'
        except Exception as e:
            return None, str(e)
            
    def post(self, endpoint, data=None):
        """发送POST请求"""
        if not self.current_connection:
            self.get_best_connection()
            
        if not self.current_connection:
            return None, '无法连接到服务器'
            
        url = f'{self.current_connection}{endpoint}'
        
        try:
            response = requests.post(url, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f'HTTP {response.status_code}'
                
        except requests.exceptions.ConnectionError:
            self.connection_status = 'disconnected'
            return None, '无法连接到服务器'
        except requests.exceptions.Timeout:
            return None, '请求超时'
        except Exception as e:
            return None, str(e)
            
    def upload_file(self, endpoint, file_path, params=None):
        """上传文件"""
        if not self.current_connection:
            self.get_best_connection()
            
        if not self.current_connection:
            return None, '无法连接到服务器'
            
        url = f'{self.current_connection}{endpoint}'
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(url, files=files, data=params, timeout=self.timeout * 3)
                
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, f'HTTP {response.status_code}'
                
        except Exception as e:
            return None, str(e)
            
    def download_file(self, url, save_path):
        """下载文件"""
        try:
            response = requests.get(url, stream=True, timeout=self.timeout * 3)
            
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True, None
            else:
                return False, f'HTTP {response.status_code}'
                
        except Exception as e:
            return False, str(e)
            
    def sync_workgroup_data(self, workgroup_id, data_type='all'):
        """
        同步工作组数据
        
        Args:
            workgroup_id: 工作组ID
            data_type: 'all', 'images', 'commands'
        """
        endpoint = f'/api/workgroup/{workgroup_id}/sync'
        result, error = self.post(endpoint, {'data_type': data_type})
        
        if error:
            Logger.error(f'NetworkManager: 同步工作组数据失败 - {error}')
            return None
            
        return result
        
    def get_workgroup_commands(self, workgroup_id):
        """获取工作组命令列表"""
        endpoint = f'/api/workgroup/{workgroup_id}/commands'
        result, error = self.get(endpoint)
        
        if error:
            Logger.error(f'NetworkManager: 获取命令列表失败 - {error}')
            return None
            
        return result
        
    def join_workgroup(self, workgroup_id, password=None):
        """加入工作组"""
        endpoint = f'/api/workgroup/{workgroup_id}/join'
        data = {'password': password} if password else {}
        result, error = self.post(endpoint, data)
        
        if error:
            Logger.error(f'NetworkManager: 加入工作组失败 - {error}')
            return None
            
        return result
        
    def leave_workgroup(self, workgroup_id):
        """退出工作组"""
        endpoint = f'/api/workgroup/{workgroup_id}/leave'
        result, error = self.post(endpoint)
        
        if error:
            Logger.error(f'NetworkManager: 退出工作组失败 - {error}')
            return None
            
        return result
