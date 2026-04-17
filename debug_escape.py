import json

with open('E:/5-ZDZS-TXA5/data/workgroup_state.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

templates = data.get('cmd_templates', {})
code = templates.get('调动', {}).get('python_code', '')

# 找第一个三引号
import re
match = re.search(r'"""', code)
if match:
    pos = match.start()
    print(f'第一个三引号位置: {pos}')
    print(f'三引号前20字符: {repr(code[pos-20:pos])}')
    print(f'三引号: {repr(code[pos:pos+3])}')
    print(f'三引号后20字符: {repr(code[pos+3:pos+23])}')
    
    # 测试不同的转义方式
    print('\n=== 转义测试 ===')
    
    # 方式1: 用 r 字符串
    escaped1 = code.replace('"""', r'\"""')
    print(f'方式1 (r\'\\\\"\\"\\"\'): {repr(escaped1[pos-5:pos+15])}')
    
    # 方式2: 用双反斜杠
    escaped2 = code.replace('"""', '\\"""')
    print(f'方式2 (\'\\\\"\\"\\"\'): {repr(escaped2[pos-5:pos+15])}')
