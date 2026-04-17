import os
import re

# 读取干净的代码
with open('e:\\5-ZDZS-TXA5\\clean_march_code.py', 'r', encoding='utf-8') as f:
    clean_code = f.read()

# 提取MARCH_PYTHON_CODE变量的内容
march_code_match = re.search(r'MARCH_PYTHON_CODE = (.*)', clean_code, re.DOTALL)
if march_code_match:
    new_march_code = march_code_match.group(1)
else:
    print('无法提取MARCH_PYTHON_CODE')
    exit(1)

# 读取原始文件
with open('e:\\5-ZDZS-TXA5\\tabs.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换MARCH_PYTHON_CODE内容
new_content = re.sub(r'MARCH_PYTHON_CODE = (.*?)(?=(\n\n[^\n]*?=|\Z))', 
                    f'MARCH_PYTHON_CODE = {new_march_code}', 
                    content, 
                    flags=re.DOTALL)

# 写入更新后的内容
with open('e:\\5-ZDZS-TXA5\\tabs.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('已成功重写MARCH_PYTHON_CODE变量')
