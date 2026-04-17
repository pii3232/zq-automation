import json

with open('E:/5-ZDZS-TXA5/data/workgroup_state.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

templates = data.get('cmd_templates', {})
code = templates.get('调动', {}).get('python_code', '')

# 找所有三引号的位置
import re
matches = list(re.finditer(r'"""', code))
print(f'调动模板中三引号出现次数: {len(matches)}')

for i, m in enumerate(matches[:5]):
    start = m.start()
    print(f'\n第{i+1}个三引号位置: {start}')
    print('上下文:', repr(code[max(0,start-30):start+50]))
