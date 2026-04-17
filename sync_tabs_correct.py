import json
import re

# 读取 workgroup_state.json
with open('E:/5-ZDZS-TXA5/data/workgroup_state.json', 'r', encoding='utf-8') as f:
    wg_data = json.load(f)

templates = wg_data.get('cmd_templates', {})

# 读取 tabs.py
with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

template_names = ['调动', '走到', '预约', '集结', '集火', '攻城', '打地', '翻红地', '铺路', '驻守']

for name in template_names:
    if name not in templates:
        print(f'跳过 {name}: 在 workgroup_state.json 中不存在')
        continue
    
    new_code = templates[name].get('python_code', '')
    
    # 找模板定义的开始位置
    start_match = re.search(rf'"{name}"\s*:\s*\{{', content)
    if not start_match:
        print(f'未找到 {name} 的开始位置')
        continue
    
    template_start = start_match.start()
    
    # 找 python_code 的位置
    python_code_match = re.search(r'"python_code"\s*:\s*"""', content[template_start:])
    if not python_code_match:
        print(f'未找到 {name} 的 python_code')
        continue
    
    code_start = template_start + python_code_match.end()
    
    # 找模板的结束位置
    search_start = code_start
    while True:
        end_match = re.search(r'"""', content[search_start:])
        if not end_match:
            print(f'未找到 {name} 的结束三引号')
            break
        
        end_pos = search_start + end_match.start()
        
        # 检查前面是否有反斜杠转义
        # 正确的转义是 \"\"\"（一个反斜杠后跟三个引号）
        # 所以我们检查是否有 \" 在三引号前面
        if end_pos >= 1 and content[end_pos-1] == '\\':
            # 这是转义的三引号，跳过
            search_start = end_pos + 3
            continue
        else:
            # 这是真正的结束三引号
            code_end = end_pos
            break
    else:
        continue
    
    # 正确的转义：将 """ 替换为 \"\"\"（一个反斜杠 + 三个引号）
    escaped_new_code = new_code.replace('"""', '\\"""')
    
    # 替换内容
    content = content[:code_start] + escaped_new_code + content[code_end:]
    
    print(f'已更新 {name}: {len(new_code)}字符')

# 写回 tabs.py
with open('E:/5-ZDZS-TXA5/tabs.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\n同步完成!')
