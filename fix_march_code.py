import os

# The clean, simple version of the MARCH_PYTHON_CODE
clean_code = '''# 调动模板的Python代码
MARCH_PYTHON_CODE = """
import os
import time
import pyautogui

# 主流程开始
print('=== 开始执行输入方法调试 ===')

# 准备输入参数
print('=== 准备输入参数 ===')

# 点击输入框多次确保激活
print('多次点击输入框确保激活')
pyautogui.click(978, 718)
time.sleep(0.5)

# 方法1: Typewrite 输入1
print('\\n方法1: 使用pyautogui.typewrite() 输入1')
pyautogui.typewrite('1')
time.sleep(1)
print('方法1完成')

# 按回车键
pyautogui.press('enter')
time.sleep(0.5)

# 清除内容
pyautogui.hotkey('ctrl', 'a')
time.sleep(0.1)
pyautogui.press('delete')
time.sleep(0.5)

# 方法2: Press 输入2
print('\\n方法2: 使用pyautogui.press() 输入2')
pyautogui.press('2')
time.sleep(1)
print('方法2完成')

# 按回车键
pyautogui.press('enter')
time.sleep(0.5)

# 清除内容
pyautogui.hotkey('ctrl', 'a')
time.sleep(0.1)
pyautogui.press('delete')
time.sleep(0.5)

# 方法3: 剪贴板 输入3
print('\\n方法3: 使用剪贴板 输入3')
try:
    import pyperclip
    pyperclip.copy('3')
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)
    print('方法3完成')
except:
    print('方法3失败')

# 按回车键
pyautogui.press('enter')
time.sleep(0.5)

# 所有方法测试完成
print('\\n所有输入方法测试完成')

# 写入日志
with open('input_debug.txt', 'w') as f:
    f.write('测试完成')

print('=== 调动流程执行完成 ===')
"""
'''

# Read the original file
with open('tabs.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start of MARCH_PYTHON_CODE
start_idx = None
for i, line in enumerate(lines):
    if line.strip().startswith('# 调动模板的Python代码'):
        start_idx = i
        break

# Find the end of MARCH_PYTHON_CODE (next triple quote after start)
if start_idx is not None:
    end_idx = None
    # Find the first line with ''' after start_idx
    for i in range(start_idx + 1, len(lines)):
        if '''''' in lines[i]:
            end_idx = i
            break
    
    if end_idx is not None:
        # Recreate the file content
        new_content = ''.join(lines[:start_idx]) + clean_code + ''.join(lines[end_idx+1:])
        
        # Write back the fixed content
        with open('tabs.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print('Successfully fixed MARCH_PYTHON_CODE!')
    else:
        print('Could not find end of MARCH_PYTHON_CODE')
else:
    print('Could not find start of MARCH_PYTHON_CODE')
