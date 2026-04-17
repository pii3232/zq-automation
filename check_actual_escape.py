with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找调动模板
import re
match = re.search(r'"调动".*?"python_code"\s*:\s*"""', content, re.DOTALL)
if match:
    start = match.end()
    snippet = content[start:start+800]
    
    # 找第710-730字符
    print(f'python_code开始后705-740字符:')
    print(repr(snippet[705:745]))
    
    # 检查是否有转义的三引号
    escaped = re.findall(r'\\"""', snippet)
    print(f'\n找到转义三引号数量: {len(escaped)}')
    
    # 检查是否有未转义的三引号
    # 找所有 """ 但不是 \"\"\" 的
    all_triple = list(re.finditer(r'"""', snippet))
    print(f'\n所有三引号位置:')
    for m in all_triple[:5]:
        pos = m.start()
        context = snippet[max(0,pos-10):pos+15]
        print(f'  位置 {pos}: {repr(context)}')
