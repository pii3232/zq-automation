import json
import re

# 读取 tabs.py 并提取各模板字符数
with open('tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

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
    '驻守': 7977,
}

print('tabs.py BUILTIN_COMMAND_TEMPLATES 验证:')
for name, exp_len in expected.items():
    pattern = r'"' + re.escape(name) + r'":\s*\{[^}]*?"python_code":\s*"""(.+?)"""'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        actual_len = len(match.group(1))
        status = 'OK' if actual_len == exp_len else f'DIFF (actual: {actual_len})'
        print(f'  {name}: {exp_len} {status}')
    else:
        print(f'  {name}: NOT FOUND')

# 验证 command_templates.json
with open('data/command_templates.json', 'r', encoding='utf-8') as f:
    ct = json.load(f)

print('')
print('command_templates.json 验证:')
for name, exp_len in expected.items():
    if name in ct:
        actual_len = len(ct[name]['python_code'])
        status = 'OK' if actual_len == exp_len else f'DIFF (actual: {actual_len})'
        print(f'  {name}: {exp_len} {status}')
    else:
        print(f'  {name}: NOT FOUND')
