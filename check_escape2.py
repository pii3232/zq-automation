with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找调动模板中第一个三引号附近
import re

# 找调动模板
match = re.search(r'"调动".*?"python_code"\s*:\s*"""', content, re.DOTALL)
if match:
    start = match.end()
    snippet = content[start:start+1000]
    
    # 找 \"\"\" 模式（转义的三引号）
    escaped_match = re.search(r'\\"""', snippet)
    if escaped_match:
        print(f'找到转义引号位置: {escaped_match.start()}')
        print('上下文:', repr(snippet[escaped_match.start()-30:escaped_match.start()+50]))
    else:
        print('未找到转义引号')
        # 找普通三引号
        normal_match = re.search(r'"""', snippet)
        if normal_match:
            print(f'找到普通三引号位置: {normal_match.start()}')
            print('上下文:', repr(snippet[normal_match.start()-30:normal_match.start()+50]))
