with open('E:/5-ZDZS-TXA5/tabs.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 检查第579行
print(f'第579行: {repr(lines[578])}')
print(f'第580行: {repr(lines[579])}')

# 检查第579行的最后几个字符
line579 = lines[578]
print(f'\n第579行最后10字符:')
for i in range(len(line579)-10, len(line579)):
    c = line579[i]
    print(f'  位置{i}: {repr(c)} (ord={ord(c)})')
