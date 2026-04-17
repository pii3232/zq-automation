# 测试：在三引号字符串中如何表示字面的三引号

# 方式1: \"\"\"
test1 = """这是一个测试\"\"\"这是三引号"""
print(f'方式1成功: {repr(test1)}')

# 方式2: \\""" - 这会导致语法错误吗？
# test2 = """这是一个测试\\"""

# 方式3: 用变量
code = 'def foo():\n    """docstring"""\n    pass'
escaped = code.replace('"""', r'\"""')
print(f'\n原始代码: {repr(code)}')
print(f'转义后: {repr(escaped)}')

# 测试放入三引号字符串
test3 = f"""{escaped}"""
print(f'\n方式3成功: {repr(test3)}')
