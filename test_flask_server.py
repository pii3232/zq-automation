import sys
import time
import threading
import requests
sys.path.insert(0, 'E:/5-ZDZS-TXA5/SERVER')

from app import create_app

# 创建应用
app = create_app()
print("[OK] Flask应用创建成功")

# 在后台线程启动服务器
def run_server():
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()
print("[OK] 服务器启动中...")

# 等待服务器就绪
time.sleep(3)

# 测试健康检查接口
try:
    r = requests.get('http://127.0.0.1:5000/api/health', timeout=5)
    print(f"[OK] 健康检查: HTTP {r.status_code}")
    print(f"  响应: {r.text}")
except Exception as e:
    print(f"[FAIL] 健康检查失败: {e}")

# 测试用户列表接口
try:
    r2 = requests.get('http://127.0.0.1:5000/api/admin/users', timeout=10)
    print(f"[OK] 用户列表API: HTTP {r2.status_code}")
    if r2.status_code == 200:
        result = r2.json()
        print(f"  用户数量: {result.get('data', {}).get('total', 0)}")
    else:
        print(f"  错误响应: {r2.text[:200]}")
except Exception as e:
    print(f"[FAIL] 用户列表API失败: {e}")

# 保持服务器运行
print("\n服务器运行中,按Ctrl+C停止...")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n服务器停止")
