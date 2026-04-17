with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

expected = {
    '调动': 7974,
    '走到': 6696,
    '预约': 17464,
    '集结': 15716,
    '集火': 8192,
    '攻城': 7974,
    '打地': 8007,
    '翻红地': 10857,
    '铺路': 10130,
    '驻守': 7977
}

print('=== tabs.py BUILTIN_COMMAND_TEMPLATES 验证 ===')

for name, exp_chars in expected.items():
    # 找模板开始
    start_match = re.search(rf'"{name}"\s*:\s*\{{', content)
    if not start_match:
        print(f'{name}: 未找到开始')
        continue
    
    start = start_match.start()
    
    # 找 python_code 开始
    code_start_match = re.search(r'"python_code"\s*:\s*"""', content[start:])
    if not code_start_match:
        print(f'{name}: 未找到 python_code')
        continue
    
    code_start = start + code_start_match.end()
    
    # 找结束的 """
    pos = code_start
    while True:
        end_match = re.search(r'"""', content[pos:])
        if not end_match:
            print(f'{name}: 未找到结束')
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
            actual = len(unescaped)
            status = 'OK' if actual == exp_chars else 'FAIL'
            print(f'{name}: {actual}字符 (预期{exp_chars}) {status}')
            break
