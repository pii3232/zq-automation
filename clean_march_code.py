MARCH_PYTHON_CODE = '''import os
import time
import pyautogui

# 主流程开始
print('=== 开始执行输入方法调试 ===')

# 点击坐标978,718（输入框位置）
print('=== 准备输入参数 ===')

# 检查当前鼠标位置
current_x, current_y = pyautogui.position()
print(f'调试: 当前鼠标位置: ({current_x}, {current_y})')

# 直接移动到输入框并点击多次确保激活
print('多次点击输入框确保激活')
pyautogui.moveTo(978, 718, duration=0.2)
for i in range(3):
    print(f'第{i+1}次点击输入框')
    pyautogui.click()
    time.sleep(0.3)

# ============== 方法1: Typewrite 输入1 ==============
print('\n📝 方法1: 使用pyautogui.typewrite() 输入"1"')
pyautogui.typewrite('1')
time.sleep(1)
print('方法1完成，输入了1')

# 按回车键
pyautogui.press('enter')
time.sleep(0.5)

# 清除内容
pyautogui.hotkey('ctrl', 'a')
time.sleep(0.1)
pyautogui.press('delete')
time.sleep(0.5)

# ============== 方法2: Press每个字符 输入2 ==============
print('\n📝 方法2: 使用pyautogui.press()逐个字符 输入"2"')
pyautogui.press('2')
time.sleep(1)
print('方法2完成，输入了2')

# 按回车键
pyautogui.press('enter')
time.sleep(0.5)

# 清除内容
pyautogui.hotkey('ctrl', 'a')
time.sleep(0.1)
pyautogui.press('delete')
time.sleep(0.5)

# ============== 方法3: KeyDown/KeyUp 输入3 ==============
print('\n📝 方法3: 使用pyautogui.keyDown/keyUp模拟按键 输入"3"')
pyautogui.keyDown('3')
time.sleep(0.1)
pyautogui.keyUp('3')
time.sleep(1)
print('方法3完成，输入了3')

# 按回车键
pyautogui.press('enter')
time.sleep(0.5)

# 清除内容
pyautogui.hotkey('ctrl', 'a')
time.sleep(0.1)
pyautogui.press('delete')
time.sleep(0.5)

# ============== 方法4: 剪贴板 输入4 ==============
print('\n📝 方法4: 使用剪贴板复制粘贴 输入"4"')
try:
    import pyperclip
    
    # 复制内容到剪贴板
    pyperclip.copy('4')
    clipboard_content = pyperclip.paste()
    print(f'已复制到剪贴板: "{clipboard_content}"')
    time.sleep(0.5)
    
    # 粘贴内容
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1)
    print('方法4完成，输入了4')
    
except ImportError:
    print('❌ pyperclip不可用，跳过此方法')

# 按回车键
pyautogui.press('enter')
time.sleep(0.5)

# 清除内容
pyautogui.hotkey('ctrl', 'a')
time.sleep(0.1)
pyautogui.press('delete')
time.sleep(0.5)

# ============== 方法5: 数字键盘 输入5 ==============
print('\n📝 方法5: 使用数字键盘输入 输入"5"')
pyautogui.press('num5')
time.sleep(1)
print('方法5完成，输入了5')

# 按回车键
pyautogui.press('enter')
time.sleep(0.5)

# 直接输出到控制台，确认测试完成
print('\n✅ 所有输入方法测试完成')
print('每个方法分别输入了: 1, 2, 3, 4, 5')

# 将输入内容写入文件，方便检查
with open('input_debug_log.txt', 'w') as f:
    f.write(f'输入测试完成\n')
    f.write(f'测试时间: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
    f.write(f'使用的方法: 5种方法分别输入1-5\n')
print('调试日志已写入input_debug_log.txt文件')

# 点击坐标1240,708
print('\n点击坐标: (1240, 708)')
pyautogui.click(1240, 708)
time.sleep(1)

# 点击坐标1158,718
print('点击坐标: (1158, 718)')
pyautogui.click(1158, 718)
time.sleep(2)

# 点击坐标666,386
print('点击坐标: (666, 386)')
pyautogui.click(666, 386)
time.sleep(1)

print('=== 调动流程执行完成 ===')
'''