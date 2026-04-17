with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
match = re.search(r'"调动".*?"python_code"\s*:\s*"""', content, re.DOTALL)
if match:
    start = match.end()
    snippet = content[start:start+800]
    
    # 找三引号位置
    pos = snippet.find('"""')
    if pos > 0:
        # 打印三引号前后的原始字符
        print("三引号前后的字符:")
        for i in range(max(0, pos-5), min(len(snippet), pos+10)):
            c = snippet[i]
            print(f'  位置{i-pos}: {repr(c)} (ord={ord(c)})')
