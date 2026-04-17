"""测试脚本 - 检查导入和基本功能"""
import sys
import traceback

print("开始测试导入...")

try:
    print("1. 测试导入 main.py...")
    import main
    print("[OK] main.py 导入成功")
except Exception as e:
    print(f"[FAIL] main.py 导入失败: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("2. 测试导入 handlers.py...")
    import handlers
    print("[OK] handlers.py 导入成功")
except Exception as e:
    print(f"[FAIL] handlers.py 导入失败: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("3. 测试导入 tabs.py...")
    import tabs
    print("[OK] tabs.py 导入成功")
except Exception as e:
    print(f"[FAIL] tabs.py 导入失败: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("4. 测试导入 discovery_handlers.py...")
    import discovery_handlers
    print("[OK] discovery_handlers.py 导入成功")
except Exception as e:
    print(f"[FAIL] discovery_handlers.py 导入失败: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("5. 检查 GlobalClickListener 类...")
    if hasattr(handlers, 'GlobalClickListener'):
        print("[OK] GlobalClickListener 类存在")
    else:
        print("[FAIL] GlobalClickListener 类不存在")
except Exception as e:
    print(f"[FAIL] 检查失败: {e}")

try:
    print("6. 检查 LongRecordingListener 类...")
    if hasattr(handlers, 'LongRecordingListener'):
        print("[OK] LongRecordingListener 类存在")
    else:
        print("[FAIL] LongRecordingListener 类不存在")
except Exception as e:
    print(f"[FAIL] 检查失败: {e}")

print("\n所有基础测试完成！")
