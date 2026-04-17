with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找调动模板
import re
match = re.search(r'"调动".*?"python_code"\s*:\s*"""', content, re.DOTALL)
if match:
    start = match.end()
    # 找第711-720字符
    snippet = content[start:start+800]
    print(f'python_code开始后710-730字符:')
    print(repr(snippet[705:735]))
