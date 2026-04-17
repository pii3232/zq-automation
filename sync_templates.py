import json
import re

# 读取 workgroup_state.json 获取最新模板
with open('data/workgroup_state.json', 'r', encoding='utf-8') as f:
    ws = json.load(f)
templates = ws.get('cmd_templates', {})

# 读取 tabs.py
with open('tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到 BUILTIN_COMMAND_TEMPLATES 的开始和结束位置
start_match = re.search(r'BUILTIN_COMMAND_TEMPLATES\s*=\s*\{', content)
if not start_match:
    print("Cannot find BUILTIN_COMMAND_TEMPLATES")
    exit(1)

start_pos = start_match.end() - 1  # 包含 {

# 找到匹配的结束括号 - 需要计算括号嵌套
brace_count = 0
end_pos = start_pos
for i, char in enumerate(content[start_pos:], start_pos):
    if char == '{':
        brace_count += 1
    elif char == '}':
        brace_count -= 1
        if brace_count == 0:
            end_pos = i + 1
            break

# 生成新的 BUILTIN_COMMAND_TEMPLATES 内容
new_templates = "BUILTIN_COMMAND_TEMPLATES = {\n"

for name, template_data in templates.items():
    python_code = template_data['python_code']
    has_multi_coords = template_data.get('has_multi_coords', False)
    has_auto_input = template_data.get('has_auto_input', False)
    description = template_data.get('description', '')
    
    new_templates += f'    "{name}": {{\n'
    new_templates += f'        "type": "python_script",\n'
    new_templates += f'        "description": "{description}",\n'
    new_templates += f'        "has_multi_coords": {has_multi_coords},\n'
    new_templates += f'        "has_auto_input": {has_auto_input},\n'
    new_templates += f'        "is_python_template": True,\n'
    new_templates += f'        "python_code": """{python_code}""",\n'
    new_templates += f'        "template": {{\n'
    new_templates += f'            "coords": [\n'
    new_templates += f'                {{"x": 0, "y": 0, "label": "坐标1"}}\n'
    new_templates += f'            ],\n'
    new_templates += f'            "workflows": [],\n'
    new_templates += f'            "exec_mode": "immediate"\n'
    new_templates += f'        }}\n'
    new_templates += f'    }},\n'

new_templates += "}\n"

# 替换原来的 BUILTIN_COMMAND_TEMPLATES
new_content = content[:start_match.start()] + new_templates + content[end_pos:]

# 写回 tabs.py
with open('tabs.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('tabs.py updated successfully')

# 验证
with open('tabs.py', 'r', encoding='utf-8') as f:
    new_file_content = f.read()

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

print('\n验证结果:')
for name, exp_len in expected.items():
    pattern = r'"' + re.escape(name) + r'".*?"python_code":\s*"""(.+?)"""'
    match = re.search(pattern, new_file_content, re.DOTALL)
    if match:
        actual_len = len(match.group(1))
        status = 'OK' if actual_len == exp_len else f'DIFF (actual: {actual_len})'
        print(f'  {name}: {exp_len} {status}')
    else:
        print(f'  {name}: NOT FOUND')
