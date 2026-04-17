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
    
    start = start_match.start()
    
    # 找 python_code 的位置
    python_code_match = re.search(r'"python_code"\s*:\s*"""', content[start:])
    if not python_code_match:
        print(f'未找到 {name} 的 python_code')
        continue
    
    code_start = start + python_code_match.end()
    
    # 找三引号结束位置（需要处理转义的三引号）
    # 从code_start开始，找到第一个非转义的三引号
    pos = code_start
    while True:
        end_match = re.search(r'"""', content[pos:])
        if not end_match:
            print(f'未找到 {name} 的结束三引号')
            break
        # 检查是否是转义的（前面是否有奇数个反斜杠）
        end_pos = pos + end_match.start()
        # 计算前面的反斜杠数
        backslash_count = 0
        check_pos = end_pos - 1
        while check_pos >= 0 and content[check_pos] == '\\':
            backslash_count += 1
            check_pos -= 1
        if backslash_count % 2 == 0:  # 偶数个反斜杠，说明不是转义
            code_end = end_pos
            break
        else:
            pos = end_pos + 3  # 跳过这个转义的三引号
    else:
        continue
    
    # 替换内容
    old_code = content[code_start:code_end]
    
    # 新代码需要转义三引号
    escaped_new_code = new_code.replace('"""', '\\"\\"\\"')
    
    content = content[:code_start] + escaped_new_code + content[code_end:]
    
    print(f'已更新 {name}: {len(new_code)}字符 (原{len(old_code)}字符)')

# 写回 tabs.py
with open('E:/5-ZDZS-TXA5/tabs.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('\n同步完成!')
