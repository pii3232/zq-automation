# 使用 Python 3.11 slim 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

# 先复制依赖文件
COPY requirements.txt .

# 安装依赖（分步安装，便于定位问题）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir Flask==3.0.0 Flask-CORS==4.0.0 Flask-SQLAlchemy==3.1.1 && \
    pip install --no-cache-dir PyMySQL==1.1.0 python-dotenv==1.0.0 email-validator==2.1.0 && \
    pip install --no-cache-dir requests==2.31.0 cryptography>=41.0.0 && \
    pip install --no-cache-dir reportlab==4.0.7 Pillow==10.1.0

# 复制应用代码
COPY . .

# 创建必要目录
RUN mkdir -p /app/instance /app/audit_logs /app/backups

# 暴露端口
EXPOSE 5000

# 创建启动脚本
RUN echo '#!/bin/bash\nset -e\necho "Starting application..."\necho "Port: ${PORT}"\nexec python app.py\n' > /app/start.sh && \
    chmod +x /app/start.sh

# 启动应用
CMD ["/bin/bash", "/app/start.sh"]
