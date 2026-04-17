with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找调动模板的 python_code
import re

# 找 "调动": { 开始
start_match = re.search(r'"调动"\s*:\s*\{', content)
if start_match:
    start = start_match.start()
    
    # 找 "python_code": """ 
    code_start_match = re.search(r'"python_code"\s*:\s*"""', content[start:])
    if code_start_match:
        code_start = start + code_start_match.end()
        
        # 找结束的 """, 需要处理转义
        pos = code_start
        while True:
            end_match = re.search(r'"""', content[pos:])
            if not end_match:
                break
            end_pos = pos + end_match.start()
            # 检查是否转义
            if end_pos >= 1 and content[end_pos-1] == '\\':
                pos = end_pos + 3
                continue
            else:
                code = content[code_start:end_pos]
                # 反转义
                unescaped = code.replace('\\"""', '"""')
                print(f'调动模板 python_code 长度: {len(unescaped)}')
                print(f'前100字符: {unescaped[:100]}')
                break
