import json
import re

# 读取 workgroup_state.json
with open('E:/5-ZDZS-TXA5/data/workgroup_state.json', 'r', encoding='utf-8') as f:
    wg_data = json.load(f)

templates = wg_data.get('cmd_templates', {})

# 读取 tabs.py
with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 需要同步的模板
template_names = ['调动', '走到', '预约', '集结', '集火', '攻城', '打地', '翻红地', '铺路', '驻守']

for name in template_names:
    if name not in templates:
        print(f'跳过 {name}: 在 workgroup_state.json 中不存在')
        continue
    
    new_code = templates[name].get('python_code', '')
    
    # 转义三引号
    escaped_code = new_code.replace('"""', '\\"\\"\\"')
    
    # 匹配并替换模板
    pattern = rf'("{name}"\s*:\s*\{{[^}}]*?"python_code"\s*:\s*""").*?(""")'
    
    def replace_func(match):
        return match.group(1) + escaped_code + match.group(2)
    
    new_content, count = re.subn(pattern, replace_func, content, flags=re.DOTALL)
    
    if count > 0:
        content = new_content
        print(f'已更新 {name}: {len(new_code)}字符')
    else:
        print(f'未找到 {name} 的匹配')

# 写回 tabs.py
with open('E:/5-ZDZS-TXA5/tabs.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\n同步完成!')

# 验证
print('\n=== 验证结果 ===')
with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

for name in template_names:
    pattern = rf'"{name}"\s*:\s*\{{[^}}]*?"python_code"\s*:\s*"""(.*?)"""'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        code = match.group(1)
        print(f'{name}: {len(code)}字符')
    else:
        print(f'{name}: 未找到')
