# 测试：在三引号字符串中，\""" 是否会被解析为字符串结束？

# 测试1: 正常的三引号字符串
test1 = """abc"""
print(f'测试1: {repr(test1)}')

# 测试2: 包含 \" 的三引号字符串
test2 = """abc\"def"""
print(f'测试2: {repr(test2)}')

# 测试3: 包含 \"" 的三引号字符串
test3 = """abc\""def"""
print(f'测试3: {repr(test3)}')

# 测试4: 包含 \"\"\" 的三引号字符串 - 这会导致语法错误吗？
# test4 = """abc\"\"\"def"""

# 测试5: 用转义的方式
test5 = """abc\"\"\"def"""
print(f'测试5: {repr(test5)}')
