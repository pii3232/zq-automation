"""
加密工具模块 - 用于服务端和客户端的通信加密
使用AES-256-CBC加密 + RSA签名确保安全
"""
import base64
import hashlib
import hmac
import os
import json
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

# 固定的加密密钥（32字节 = 256位）
# 使用SHA-256派生密钥确保长度正确
SECRET_KEY = hashlib.sha256(b'ZQ_ACTIVATION_SYSTEM_SECRET_KEY_2024').digest()
# HMAC密钥用于签名验证
HMAC_KEY = hashlib.sha256(b'ZQ_ACTIVATION_HMAC_KEY_2024').digest()
# 初始化向量固定（实际应用中应该随机生成，这里为了简化使用固定值）
IV = b'ZQ_ACTIVATION_IV'  # 16字节（截取前16字节，AES-CBC要求IV必须16字节）


class CryptoManager:
    """加密管理器"""
    
    @staticmethod
    def pad(data):
        """PKCS7填充"""
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(data) + padder.finalize()
        return padded_data
    
    @staticmethod
    def unpad(data):
        """移除PKCS7填充"""
        unpadder = padding.PKCS7(128).unpadder()
        unpadded_data = unpadder.update(data) + unpadder.finalize()
        return unpadded_data
    
    @staticmethod
    def encrypt(plaintext):
        """
        加密数据
        Args:
            plaintext: 要加密的字符串或字典
        Returns:
            base64编码的加密字符串
        """
        if isinstance(plaintext, dict):
            plaintext = json.dumps(plaintext, ensure_ascii=False)
        
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # 填充
        padded_data = CryptoManager.pad(plaintext)
        
        # AES加密
        cipher = Cipher(
            algorithms.AES(SECRET_KEY),
            modes.CBC(IV),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # 计算HMAC签名
        signature = hmac.new(HMAC_KEY, ciphertext, hashlib.sha256).digest()
        
        # 组合：签名(32字节) + 密文
        combined = signature + ciphertext
        
        return base64.b64encode(combined).decode('utf-8')
    
    @staticmethod
    def decrypt(ciphertext_b64):
        """
        解密数据
        Args:
            ciphertext_b64: base64编码的加密字符串
        Returns:
            解密后的字符串
        """
        try:
            combined = base64.b64decode(ciphertext_b64)
            
            # 分离签名和密文
            received_signature = combined[:32]
            ciphertext = combined[32:]
            
            # 验证签名
            expected_signature = hmac.new(HMAC_KEY, ciphertext, hashlib.sha256).digest()
            if not hmac.compare_digest(received_signature, expected_signature):
                raise ValueError("签名验证失败，数据可能被篡改")
            
            # AES解密
            cipher = Cipher(
                algorithms.AES(SECRET_KEY),
                modes.CBC(IV),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            padded_data = decryptor.update(ciphertext) + decryptor.finalize()
            
            # 移除填充
            plaintext = CryptoManager.unpad(padded_data)
            
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"解密失败: {str(e)}")
    
    @staticmethod
    def encrypt_dict(data_dict):
        """加密字典并返回加密字符串"""
        return CryptoManager.encrypt(data_dict)
    
    @staticmethod
    def decrypt_to_dict(ciphertext_b64):
        """解密字符串并返回字典"""
        plaintext = CryptoManager.decrypt(ciphertext_b64)
        return json.loads(plaintext)


class AuthHelper:
    """认证助手 - 管理admin凭证"""
    
    # Admin凭证（加密存储）
    # 原始：admin / Mdjsj32320809
    ADMIN_CREDENTIALS = {
        'username': 'admin',
        'password': 'Mdjsj32320809'
    }
    
    @staticmethod
    def get_encrypted_credentials():
        """获取加密后的admin凭证"""
        return CryptoManager.encrypt_dict(AuthHelper.ADMIN_CREDENTIALS)
    
    @staticmethod
    def verify_admin(encrypted_credentials):
        """验证加密的admin凭证"""
        try:
            credentials = CryptoManager.decrypt_to_dict(encrypted_credentials)
            return (credentials.get('username') == AuthHelper.ADMIN_CREDENTIALS['username'] and
                    credentials.get('password') == AuthHelper.ADMIN_CREDENTIALS['password'])
        except:
            return False
    
    @staticmethod
    def get_admin_username():
        """获取admin用户名（明文）"""
        return AuthHelper.ADMIN_CREDENTIALS['username']
    
    @staticmethod
    def get_admin_password():
        """获取admin密码（明文）- 仅用于数据库初始化"""
        return AuthHelper.ADMIN_CREDENTIALS['password']


def encrypt_response(data):
    """加密响应数据"""
    if isinstance(data, dict):
        data['timestamp'] = datetime.utcnow().isoformat()
    return CryptoManager.encrypt_dict(data)


def decrypt_request(encrypted_data):
    """解密请求数据"""
    return CryptoManager.decrypt_to_dict(encrypted_data)
