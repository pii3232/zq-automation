with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找调动模板中第一个三引号附近
import re

# 找调动模板
match = re.search(r'"调动".*?"python_code"\s*:\s*"""', content, re.DOTALL)
if match:
    start = match.end()
    # 找第一个转义的三引号
    # 应该是 \"\"\"
    snippet = content[start:start+1000]
    print('调动模板python_code开始1000字符:')
    print(snippet[:500])
    
    # 找 \"\"\" 模式
    escaped_match = re.search(r'\\"', snippet)
    if escaped_match:
        print(f'\n找到转义引号位置: {escaped_match.start()}')
        print('上下文:', repr(snippet[escaped_match.start()-20:escaped_match.start()+50]))
