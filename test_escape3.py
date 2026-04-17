# 测试不同的转义方式

# 原始字符串
code = 'def foo():\n    """docstring"""\n    pass'

# 方式1: '\\"""'
escaped1 = code.replace('"""', '\\""')
print(f'方式1 (\'\\\\"\\"\\"\'): {repr(escaped1)}')

# 方式2: 直接拼接反斜杠
escaped2 = code.replace('"""', '\\' + '"""')
print(f'方式2 (\'\\\\\\\' + \'\\"\\"\\"\'): {repr(escaped2)}')

# 方式3: 使用chr
escaped3 = code.replace('"""', chr(92) + '"""')
print(f'方式3 (chr(92) + \'\\"\\"\\"\'): {repr(escaped3)}')

# 验证哪个正确
print('\n=== 验证 ===')
# 正确的转义应该是: \"\"\"
# 即: 一个反斜杠 + 三个引号
correct_escape = chr(92) + '"""'
print(f'正确的转义: {repr(correct_escape)}')

# 测试放入三引号字符串
test = f"""before{correct_escape}middle{correct_escape}after"""
print(f'测试结果: {repr(test)}')
