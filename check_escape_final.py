with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re
match = re.search(r'"调动".*?"python_code"\s*:\s*"""', content, re.DOTALL)
if match:
    start = match.end()
    snippet = content[start:start+800]
    
    print("tabs.py中python_code开始后710-735字符:")
    print(repr(snippet[710:740]))
    
    # 检查反斜杠数量
    pos = snippet.find('"""')
    if pos > 0:
        # 检查前面的反斜杠
        backslash_count = 0
        check_pos = pos - 1
        while check_pos >= 0 and snippet[check_pos] == '\\':
            backslash_count += 1
            check_pos -= 1
        print(f'\n三引号前面有 {backslash_count} 个反斜杠')
