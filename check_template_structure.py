import re

with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找调动模板
match = re.search(r'"调动"\s*:\s*\{', content)
if match:
    start = match.start()
    # 找下一个模板（以 "开头，后面是中文）
    next_match = re.search(r'\n    "[\u4e00-\u9fa5]+"\s*:\s*\{', content[start+10:])
    if next_match:
        end = start + 10 + next_match.start()
    else:
        # 找字典结束
        end_match = re.search(r'\n\}', content[start:])
        if end_match:
            end = start + end_match.end()
        else:
            end = len(content)
    
    template_content = content[start:end]
    print(f'调动模板长度: {len(template_content)}')
    
    # 找所有三引号
    triple_quotes = list(re.finditer(r'"""', template_content))
    print(f'\n三引号出现次数: {len(triple_quotes)}')
    for i, m in enumerate(triple_quotes):
        pos = m.start()
        context = template_content[max(0, pos-30):pos+30]
        print(f'\n第{i+1}个三引号位置: {pos}')
        print(f'上下文: {repr(context)}')
