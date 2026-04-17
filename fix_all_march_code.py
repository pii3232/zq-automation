import os

# The clean, simple version of the MARCH_PYTHON_CODE
clean_code = '''MARCH_PYTHON_CODE = """
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
    content = f.read()

# Fix all occurrences of MARCH_PYTHON_CODE
before_march = content.split('# 调动模板的Python代码')[0]
content_after_march = content.split('# 调动模板的Python代码')[1]

# Fix the first occurrence
parts = content_after_march.split('MARCH_PYTHON_CODE =')
if len(parts) > 1:
    # Replace the first instance
    result = before_march + '# 调动模板的Python代码\n' + clean_code + ''.join(parts[2:])
    
    # Fix the second occurrence in global_cmd_edit_workflow_item
    # Look for the pattern in the global_cmd_edit_workflow_item function
    if 'global MARCH_PYTHON_CODE' in result:
        parts2 = result.split('MARCH_PYTHON_CODE =')
        if len(parts2) > 2:
            fixed_result = parts2[0] + 'MARCH_PYTHON_CODE =' + clean_code.split('MARCH_PYTHON_CODE =')[1] + ''.join(parts2[2:])
            result = fixed_result
    
    # Write back the fixed content
    with open('tabs.py', 'w', encoding='utf-8') as f:
        f.write(result)
    
    print('Successfully fixed all instances of MARCH_PYTHON_CODE!')
else:
    print('Could not find MARCH_PYTHON_CODE in the file')
