import re

with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

print('=== tabs.py BUILTIN_COMMAND_TEMPLATES 验证 ===')
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

for name, exp_chars in expected.items():
    pattern = rf'"{name}"\s*:\s*\{{.*?"python_code"\s*:\s*"""(.*?)"""'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        code = match.group(1)
        # 反转义
        unescaped = code.replace('\\"""', '"""')
        actual = len(unescaped)
        status = 'OK' if actual == exp_chars else 'FAIL'
        print(f'{name}: {actual}字符 (预期{exp_chars}) {status}')
    else:
        print(f'{name}: 未找到 FAIL')
