import json

with open('E:/5-ZDZS-TXA5/data/workgroup_state.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

templates = data.get('cmd_templates', {})
code = templates.get('调动', {}).get('python_code', '')

# 模拟转义
escaped = code.replace('"""', '\\"\\"\\"')

# 找转义后的三引号位置
import re
matches = list(re.finditer(r'\\"\\"\\"', escaped))
print(f'转义后三引号出现次数: {len(matches)}')

# 找原始三引号位置
original_matches = list(re.finditer(r'"""', code))
print(f'原始三引号出现次数: {len(original_matches)}')

# 检查第一个三引号附近
if original_matches:
    pos = original_matches[0].start()
    print(f'\n原始第一个三引号位置: {pos}')
    print('原始上下文:', repr(code[pos-20:pos+30]))
    
    # 转义后应该是什么样
    print(f'\n转义后应该变成: {repr(code[pos-20:pos]) + "\\\"\\\"\\\"" + repr(code[pos+3:pos+30])}')
