"""数据库管理模块"""
import sqlite3
from typing import List, Dict
import os


class DatabaseManager:
    def __init__(self, config):
        self.config = config
        db_dir = os.path.dirname(config.database_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            
        self.conn = sqlite3.connect(config.database_path, check_same_thread=False)
        self.create_tables()
        
    def create_tables(self):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                project TEXT DEFAULT 'default'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,
                parameters TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                project TEXT DEFAULT 'default'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                context TEXT NOT NULL,
                action TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                project TEXT DEFAULT 'default'
            )
        ''')
        
        self.conn.commit()
        
    def add_chat_message(self, role: str, content: str, project: str = 'default'):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO chat_history (role, content, project) VALUES (?, ?, ?)',
            (role, content, project)
        )
        self.conn.commit()
        return cursor.lastrowid
        
    def get_chat_history(self, project: str = 'default', limit: int = 100) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id, role, content, timestamp FROM chat_history WHERE project = ? ORDER BY timestamp DESC LIMIT ?',
            (project, limit)
        )
        rows = cursor.fetchall()
        return [
            {
                'id': row[0],
                'role': row[1],
                'content': row[2],
                'timestamp': row[3]
            }
            for row in rows
        ]
        
    def delete_chat_message(self, message_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM chat_history WHERE id = ?', (message_id,))
        self.conn.commit()
        
    def add_operation_record(self, operation: str, parameters: str = None, project: str = 'default'):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO operation_records (operation, parameters, project) VALUES (?, ?, ?)',
            (operation, parameters, project)
        )
        self.conn.commit()
        
    def get_operation_records(self, project: str = 'default', limit: int = 100) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id, operation, parameters, timestamp FROM operation_records WHERE project = ? ORDER BY timestamp DESC LIMIT ?',
            (project, limit)
        )
        rows = cursor.fetchall()
        return [
            {
                'id': row[0],
                'operation': row[1],
                'parameters': row[2],
                'timestamp': row[3]
            }
            for row in rows
        ]
        
    def add_learning_record(self, context: str, action: str, project: str = 'default'):
        cursor = self.conn.cursor()
        cursor.execute(
            'INSERT INTO learning_records (context, action, project) VALUES (?, ?, ?)',
            (context, action, project)
        )
        self.conn.commit()
        
    def get_learning_records(self, project: str = 'default', limit: int = 100) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT id, context, action, frequency, timestamp FROM learning_records WHERE project = ? ORDER BY frequency DESC, timestamp DESC LIMIT ?',
            (project, limit)
        )
        rows = cursor.fetchall()
        return [
            {
                'id': row[0],
                'context': row[1],
                'action': row[2],
                'frequency': row[3],
                'timestamp': row[4]
            }
            for row in rows
        ]
        
    def delete_learning_record(self, record_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM learning_records WHERE id = ?', (record_id,))
        self.conn.commit()
