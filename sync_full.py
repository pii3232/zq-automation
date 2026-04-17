import json
import re

# 读取 workgroup_state.json
with open('E:/5-ZDZS-TXA5/data/workgroup_state.json', 'r', encoding='utf-8') as f:
    wg_data = json.load(f)

templates = wg_data.get('cmd_templates', {})

# 读取 tabs.py
with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找 BUILTIN_COMMAND_TEMPLATES 的开始和结束
start_match = re.search(r'BUILTIN_COMMAND_TEMPLATES\s*=\s*\{', content)
if not start_match:
    print('未找到 BUILTIN_COMMAND_TEMPLATES')
    exit(1)

dict_start = start_match.end() - 1  # 包含 {

# 找到字典的结束位置 - 需要匹配括号
brace_count = 0
pos = dict_start
while pos < len(content):
    if content[pos] == '{':
        brace_count += 1
    elif content[pos] == '}':
        brace_count -= 1
        if brace_count == 0:
            dict_end = pos + 1
            break
    pos += 1

# 提取模板元数据（从现有的 tabs.py 中）
# 先读取第一个模板的结构
first_template_match = re.search(r'"调动"\s*:\s*\{.*?"template"\s*:\s*\{.*?\}\s*\}', content[dict_start:dict_end], re.DOTALL)
if first_template_match:
    first_template = first_template_match.group(0)
    # 提取 template 部分
    template_meta_match = re.search(r'"template"\s*:\s*\{.*?\}', first_template, re.DOTALL)
    if template_meta_match:
        template_meta = template_meta_match.group(0)
        print(f'模板元数据: {template_meta[:100]}...')

# 构建新的模板字典
new_templates = []

template_names = ['调动', '走到', '预约', '集结', '集火', '攻城', '打地', '翻红地', '铺路', '驻守']

for name in template_names:
    if name not in templates:
        print(f'跳过 {name}')
        continue
    
    code = templates[name].get('python_code', '')
    
    # 转义三引号
    escaped_code = code.replace('"""', chr(92) + '"""')
    
    # 构建模板定义
    template_str = f'''    "{name}": {{
        "type": "python_script",
        "description": "{name}：执行{name}操作",
        "has_multi_coords": True,
        "has_auto_input": True,
        "is_python_template": True,
        "python_code": """{escaped_code}""",
        "template": {{
            "coords": [
                {{"x": 0, "y": 0, "label": "坐标1"}}
            ],
            "auto_input": "",
            "params": []
        }}
    }}'''
    
    new_templates.append(template_str)
    print(f'已构建 {name}: {len(code)}字符')

# 构建新的字典
new_dict_content = 'BUILTIN_COMMAND_TEMPLATES = {\n' + ',\n'.join(new_templates) + '\n}'

# 替换原来的字典
new_content = content[:start_match.start()] + new_dict_content + content[dict_end:]

# 写回 tabs.py
with open('E:/5-ZDZS-TXA5/tabs.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('\n同步完成!')

# 验证语法
print('\n验证语法...')
import py_compile
try:
    py_compile.compile('E:/5-ZDZS-TXA5/tabs.py', doraise=True)
    print('语法检查通过!')
except py_compile.PyCompileError as e:
    print(f'语法错误: {e}')
