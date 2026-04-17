import re

with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找第一个模板的开始
match = re.search(r'"调动"\s*:\s*\{', content)
if match:
    start = match.start()
    # 打印从开始位置往后500字符
    print(content[start:start+500])
