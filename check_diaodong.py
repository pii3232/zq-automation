import json

with open('E:/5-ZDZS-TXA5/data/workgroup_state.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

templates = data.get('cmd_templates', {})
code = templates.get('调动', {}).get('python_code', '')

# 检查是否包含 '多次找图'
if '多次找图' in code:
    idx = code.find('多次找图')
    print(f'调动模板包含"多次找图"，位置: {idx}')
    print('上下文:', repr(code[idx-50:idx+100]))
else:
    print('调动模板不包含"多次找图"')

# 检查调动模板的前500字符
print('\n调动模板前500字符:')
print(code[:500])
