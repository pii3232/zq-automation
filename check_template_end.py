import re

with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找调动模板的开始和结束
start_match = re.search(r'"调动"\s*:\s*\{', content)
if start_match:
    start = start_match.start()
    # 找下一个模板名（以 "开头，后面是中文，然后是": {）
    end_match = re.search(r'\n    "[\u4e00-\u9fa5]+"\s*:\s*\{', content[start+10:])
    if end_match:
        end = start + 10 + end_match.start()
        template_content = content[start:end]
        print(f'调动模板长度: {len(template_content)}')
        print('最后200字符:')
        print(repr(template_content[-200:]))
    else:
        print('未找到结束位置')
