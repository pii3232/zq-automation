import re

with open(r'E:\5-ZDZS-TXA5\tabs.py', 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Find all triple quotes
matches = list(re.finditer(r'"""', content))
print(f'Total triple quotes: {len(matches)}')

# Show positions
for i, m in enumerate(matches[:30]):
    line_num = content[:m.start()].count('\n') + 1
    print(f'{i+1}: Line {line_num}, position {m.start()}')
