import json
import re

# 读取 workgroup_state.json
with open('E:/5-ZDZS-TXA5/data/workgroup_state.json', 'r', encoding='utf-8') as f:
    wg_data = json.load(f)

templates = wg_data.get('cmd_templates', {})

# 读取 tabs.py
with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 需要同步的模板及其元数据
template_info = {
    '调动': {'type': 'python_script', 'description': '调动：执行调动操作', 'has_multi_coords': True, 'has_auto_input': True, 'is_python_template': True},
    '走到': {'type': 'python_script', 'description': '走到：执行走到操作', 'has_multi_coords': True, 'has_auto_input': True, 'is_python_template': True},
    '预约': {'type': 'python_script', 'description': '预约：执行预约操作', 'has_multi_coords': True, 'has_auto_input': True, 'is_python_template': True},
    '集结': {'type': 'python_script', 'description': '集结：执行集结操作', 'has_multi_coords': True, 'has_auto_input': True, 'is_python_template': True},
    '集火': {'type': 'python_script', 'description': '集火：执行集火操作', 'has_multi_coords': True, 'has_auto_input': True, 'is_python_template': True},
    '攻城': {'type': 'python_script', 'description': '攻城：执行攻城操作', 'has_multi_coords': True, 'has_auto_input': True, 'is_python_template': True},
    '打地': {'type': 'python_script', 'description': '打地：按新流程执行图片查找点击和文本参数输入', 'has_multi_coords': True, 'has_auto_input': True, 'is_python_template': True},
    '翻红地': {'type': 'python_script', 'description': '翻红地：执行翻红地操作', 'has_multi_coords': True, 'has_auto_input': True, 'is_python_template': True},
    '铺路': {'type': 'python_script', 'description': '铺路：执行铺路操作', 'has_multi_coords': True, 'has_auto_input': True, 'is_python_template': True},
    '驻守': {'type': 'python_script', 'description': '驻守：执行驻守操作', 'has_multi_coords': True, 'has_auto_input': True, 'is_python_template': True},
}

for name in template_info:
    if name not in templates:
        print(f'跳过 {name}: 在 workgroup_state.json 中不存在')
        continue
    
    new_code = templates[name].get('python_code', '')
    info = template_info[name]
    
    # 构建新的模板定义
    # 注意：python_code中的三引号需要转义
    escaped_code = new_code.replace('"""', '\\"\\"\\"')
    
    new_template = f'''    "{name}": {{
        "type": "{info['type']}",
        "description": "{info['description']}",
        "has_multi_coords": {info['has_multi_coords']},
        "has_auto_input": {info['has_auto_input']},
        "is_python_template": {info['is_python_template']},
        "python_code": """{escaped_code}""",
        "template": {{
            "coords": [
                {{"x": 0, "y": 0, "label": "坐标1"}}
            ],
            "auto_input": "",
            "params": []
        }}
    }}'''
    
    # 匹配整个模板定义（从 "模板名": { 到下一个模板定义或字典结束）
    pattern = rf'    "{name}"\s*:\s*\{{[^}}]*?"python_code"\s*:\s*""".*?""",\s*"template":\s*\{{[^}}]*\}}\s*\}}'
    
    new_content, count = re.subn(pattern, new_template, content, flags=re.DOTALL)
    
    if count > 0:
        content = new_content
        print(f'已更新 {name}: {len(new_code)}字符')
    else:
        print(f'未找到 {name} 的匹配')

# 写回 tabs.py
with open('E:/5-ZDZS-TXA5/tabs.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\n同步完成!')
