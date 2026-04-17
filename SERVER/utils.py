import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import random
import string
from datetime import datetime, timedelta
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailService:
    """邮件服务"""

    @staticmethod
    def send_verification_code(email, code):
        """发送验证码"""
        try:
            msg = MIMEMultipart()
            msg['From'] = Header(Config.MAIL_DEFAULT_SENDER)
            msg['To'] = Header(email)
            msg['Subject'] = Header('激活系统 - 验证码')

            body = f'''
            <html>
            <body>
                <h2>验证码</h2>
                <p>您好，</p>
                <p>您的验证码是：<strong style="font-size: 24px; color: #007bff;">{code}</strong></p>
                <p>验证码有效期为10分钟，请及时输入。</p>
                <p>如果这不是您的操作，请忽略此邮件。</p>
                <br>
                <p>激活系统团队</p>
            </body>
            </html>
            '''

            msg.attach(MIMEText(body, 'html', 'utf-8'))

            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                if Config.MAIL_USE_TLS:
                    server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail(Config.MAIL_DEFAULT_SENDER, email, msg.as_string())

            logger.info(f"验证码已发送到 {email}")
            return True
        except Exception as e:
            logger.error(f"发送验证码失败: {str(e)}")
            return False

    @staticmethod
    def send_ticket_confirmation(email, ticket_id):
        """发送报障确认邮件"""
        try:
            msg = MIMEMultipart()
            msg['From'] = Header(Config.MAIL_DEFAULT_SENDER)
            msg['To'] = Header(email)
            msg['Subject'] = Header('报障订单已收到')

            body = f'''
            <html>
            <body>
                <h2>报障订单已收到</h2>
                <p>您好，</p>
                <p>您的报障订单（编号：{ticket_id}）已经收到。</p>
                <p>我们正在处理您的报障，请耐心等待后台处理。</p>
                <p>如有需要，我们会通过邮件或电话与您联系。</p>
                <br>
                <p>谢谢！</p>
                <br>
                <p>激活系统团队</p>
            </body>
            </html>
            '''

            msg.attach(MIMEText(body, 'html', 'utf-8'))

            with smtplib.SMTP(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                if Config.MAIL_USE_TLS:
                    server.starttls()
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                server.sendmail(Config.MAIL_DEFAULT_SENDER, email, msg.as_string())

            logger.info(f"报障确认邮件已发送到 {email}")
            return True
        except Exception as e:
            logger.error(f"发送报障确认邮件失败: {str(e)}")
            return False


class VerificationCodeGenerator:
    """验证码生成器"""

    @staticmethod
    def generate(length=6):
        """生成6位数字验证码"""
        return ''.join(random.choices(string.digits, k=length))


class ResponseHelper:
    """响应辅助类"""

    @staticmethod
    def success(data=None, message='操作成功'):
        """成功响应"""
        response = {
            'success': True,
            'message': message,
            'timestamp': datetime.utcnow().isoformat()
        }
        if data is not None:
            response['data'] = data
        return response

    @staticmethod
    def error(message='操作失败', code=400):
        """错误响应"""
        return {
            'success': False,
            'message': message,
            'code': code,
            'timestamp': datetime.utcnow().isoformat()
        }


def validate_email(email):
    """验证邮箱格式"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_username(username):
    """验证用户名（至少6位）"""
    if len(username) < 6:
        return False, '用户名至少需要6位'
    if not username.isalnum():
        return False, '用户名只能包含字母和数字'
    return True, ''


def validate_password(password):
    """验证密码"""
    if len(password) < 6:
        return False, '密码至少需要6位'
    return True, ''
