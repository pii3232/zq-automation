import re

with open(r'E:\5-ZDZS-TXA5\tabs.py', encoding='utf-8-sig') as f:
    c = f.read()

m = re.search(r'"翻红地":.*?"python_code": """(.*?)"""', c, re.DOTALL)
if m:
    code = m.group(1)
    print(f'tabs.py代码长度: {len(code)}')
    print('包含点击960,592:', '960, 592' in code)
    print('包含find_any_red_land:', 'find_any_red_land' in code)
else:
    print('未找到翻红地模板')
