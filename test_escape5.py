# 测试在三引号字符串中表示字面三引号的正确方式

# 方式1: \"\"\"
test1 = """def foo():
    \"""docstring\"""
    pass"""
print("方式1 (\\\"\\\"\\\"):")
print(repr(test1))
print()

# 方式2: 检查实际写入的内容
import re
with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找调动模板
match = re.search(r'"调动".*?"python_code"\s*:\s*"""', content, re.DOTALL)
if match:
    start = match.end()
    snippet = content[start:start+800]
    
    # 找第710-730字符
    print("tabs.py中python_code开始后710-730字符:")
    print(repr(snippet[710:735]))
