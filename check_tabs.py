import re

with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

print('=== tabs.py BUILTIN_COMMAND_TEMPLATES ===')
for name in ['调动', '走到', '预约', '集结', '集火', '攻城', '打地', '翻红地', '铺路', '驻守']:
    # 匹配模板
    pattern = rf'"{name}"\s*:\s*\{{[^}}]*?"python_code"\s*:\s*"""(.*?)"""'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        code = match.group(1)
        print(f'{name}: {len(code)}字符')
        if '【' in code and '】' in code:
            start = code.find('【')
            end = code.find('】') + 1
            print(f'  模块标记: {code[start:end]}')
    else:
        print(f'{name}: 未找到')
