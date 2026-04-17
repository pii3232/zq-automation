#!/bin/sh
# CloudBase 启动脚本

# 设置默认端口
PORT=${PORT:-5000}

# 输出启动信息
echo "Starting Flask application on port $PORT"
echo "Database type: $([ -n "$MYSQL_HOST" ] && echo 'MySQL (CloudBase)' || echo 'SQLite (local)')"

# 启动 gunicorn
exec gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --threads 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    "app:create_app()"
