"""
操作审计日志系统
- 记录关键操作（生成激活码等）
- 文件锁定防篡改
- 自动轮换（文件过大时换新文件）
"""
import os
import json
import hashlib
import threading
from datetime import datetime
from pathlib import Path

# 跨平台文件锁支持
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False  # Windows环境


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, log_dir=None, max_file_size_mb=10):
        """
        初始化审计日志
        Args:
            log_dir: 日志目录
            max_file_size_mb: 单个日志文件最大大小（MB）
        """
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'audit_logs')
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.lock = threading.Lock()
        self.current_log_file = None
        
        # 在Windows上使用文件锁的替代方案
        self._lock_file = None
    
    def _get_current_log_file(self):
        """获取当前日志文件路径"""
        # 检查是否存在当前日志文件
        today = datetime.now().strftime('%Y%m%d')
        pattern = f'audit_{today}_*.log'
        
        existing_logs = list(self.log_dir.glob(pattern))
        
        if existing_logs:
            # 找到最新的日志文件
            latest_log = max(existing_logs, key=lambda x: x.stat().st_mtime)
            
            # 检查文件大小
            if latest_log.stat().st_size < self.max_file_size:
                return latest_log
        
        # 创建新日志文件
        seq = len(existing_logs) + 1
        new_log = self.log_dir / f'audit_{today}_{seq:03d}.log'
        return new_log
    
    def _acquire_file_lock(self, file_obj):
        """获取文件锁（防止并发写入）"""
        try:
            if HAS_FCNTL:
                fcntl.flock(file_obj.fileno(), fcntl.LOCK_EX)
            # Windows上使用线程锁作为替代
        except Exception:
            pass

    def _release_file_lock(self, file_obj):
        """释放文件锁"""
        try:
            if HAS_FCNTL:
                fcntl.flock(file_obj.fileno(), fcntl.LOCK_UN)
        except Exception:
            pass
    
    def _calculate_hash(self, content):
        """计算内容哈希（用于防篡改）"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _write_with_lock(self, file_path, content):
        """带锁写入文件"""
        with self.lock:
            try:
                with open(file_path, 'a', encoding='utf-8') as f:
                    self._acquire_file_lock(f)
                    try:
                        f.write(content)
                        f.flush()
                        os.fsync(f.fileno())  # 确保写入磁盘
                    finally:
                        self._release_file_lock(f)
            except Exception as e:
                print(f"写入审计日志失败: {e}")
    
    def _verify_file_integrity(self, file_path):
        """验证文件完整性"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                try:
                    entry = json.loads(line.strip())
                    # 验证哈希
                    stored_hash = entry.pop('_hash', None)
                    if stored_hash:
                        calculated_hash = self._calculate_hash(json.dumps(entry, ensure_ascii=False))
                        if stored_hash != calculated_hash:
                            return False, f"第{i}行数据被篡改"
                except json.JSONDecodeError:
                    return False, f"第{i}行格式错误"
            
            return True, "文件完整"
        except Exception as e:
            return False, str(e)
    
    def log_operation(self, operation_type, details, operator=None, level='INFO'):
        """
        记录操作日志
        Args:
            operation_type: 操作类型（如：GENERATE_CODE, USER_LOGIN_ADMIN, BACKUP_CREATE等）
            details: 操作详情字典
            operator: 操作者（通常是admin或system）
            level: 日志级别（INFO, WARNING, ERROR, CRITICAL）
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'operation_type': operation_type,
            'details': details,
            'operator': operator or 'system',
            'level': level
        }
        
        # 计算哈希用于防篡改
        entry_hash = self._calculate_hash(json.dumps(log_entry, ensure_ascii=False))
        log_entry['_hash'] = entry_hash
        
        # 写入日志
        log_line = json.dumps(log_entry, ensure_ascii=False) + '\n'
        log_file = self._get_current_log_file()
        
        # 检查是否需要轮换
        if log_file.exists() and log_file.stat().st_size + len(log_line) > self.max_file_size:
            # 创建新文件
            today = datetime.now().strftime('%Y%m%d')
            seq = len(list(self.log_dir.glob(f'audit_{today}_*.log'))) + 1
            log_file = self.log_dir / f'audit_{today}_{seq:03d}.log'
        
        self._write_with_lock(log_file, log_line)
    
    def log_code_generation(self, codes_generated, order_no=None, user_id=None):
        """记录激活码生成"""
        self.log_operation(
            'GENERATE_ACTIVATION_CODE',
            {
                'codes_count': len(codes_generated) if isinstance(codes_generated, list) else 1,
                'order_no': order_no,
                'user_id': user_id,
                'codes_preview': codes_generated[:2] if isinstance(codes_generated, list) and len(codes_generated) > 2 else codes_generated
            },
            level='INFO'
        )
    
    def log_admin_action(self, action, target_user=None, details=None):
        """记录管理员操作"""
        self.log_operation(
            f'ADMIN_{action}',
            {
                'target_user': target_user,
                'details': details
            },
            operator='admin',
            level='WARNING'
        )
    
    def log_database_operation(self, operation, table, details=None):
        """记录数据库关键操作"""
        self.log_operation(
            f'DATABASE_{operation}',
            {
                'table': table,
                'details': details
            },
            level='WARNING'
        )
    
    def log_backup_operation(self, operation, filename, success=True):
        """记录备份操作"""
        self.log_operation(
            f'BACKUP_{operation}',
            {
                'filename': filename,
                'success': success
            },
            level='INFO'
        )
    
    def log_system_event(self, event_type, details):
        """记录系统事件"""
        self.log_operation(
            f'SYSTEM_{event_type}',
            details,
            level='INFO'
        )
    
    def get_logs(self, date=None, operation_type=None, limit=100):
        """
        读取日志
        Args:
            date: 日期字符串（YYYYMMDD格式）
            operation_type: 操作类型过滤
            limit: 最大返回条数
        """
        logs = []
        
        if date:
            pattern = f'audit_{date}_*.log'
        else:
            pattern = 'audit_*.log'
        
        log_files = list(self.log_dir.glob(pattern))
        log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if operation_type is None or entry.get('operation_type') == operation_type:
                                logs.append(entry)
                        except:
                            pass
                        
                        if len(logs) >= limit:
                            return logs
            except:
                pass
        
        return logs
    
    def verify_all_logs(self):
        """验证所有日志文件的完整性"""
        results = {}
        log_files = list(self.log_dir.glob('audit_*.log'))
        
        for log_file in log_files:
            is_valid, message = self._verify_file_integrity(log_file)
            results[log_file.name] = {
                'valid': is_valid,
                'message': message
            }
        
        return results


# 全局审计日志实例
audit_logger = AuditLogger()
