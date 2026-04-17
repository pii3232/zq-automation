import json

# 读取文件
with open('data/workgroup_state.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 定义要插入的新代码
new_step = '''    # 2.7.13.1 获得画面中心位置坐标，点击，等待1秒
    screen_width, screen_height = pyautogui.size()
    center_x = screen_width // 2
    center_y = screen_height // 2
    pyautogui.click(center_x, center_y)
    p(f'[2.7.13.1] 点击画面中心坐标: ({center_x}, {center_y})，等待1秒')
    time.sleep(1)
    
'''

# 更新 cmd_templates 中的"打地"模板
if '打地' in data.get('cmd_templates', {}):
    old_code = data['cmd_templates']['打地']['python_code']
    # 在2.7.13后面、2.7.14前面插入新步骤
    old_pattern = """    # 2.7.13 等待1秒
    p('[2.7.13] 等待1秒')
    time.sleep(1)
    
    # 2.7.14 多次找图1-GZ.png"""
    
    new_pattern = """    # 2.7.13 等待1秒
    p('[2.7.13] 等待1秒')
    time.sleep(1)
    
""" + new_step + """    # 2.7.14 多次找图1-GZ.png"""
    
    data['cmd_templates']['打地']['python_code'] = old_code.replace(old_pattern, new_pattern)
    print('已更新 cmd_templates 中的打地模板')

# 保存文件
with open('data/workgroup_state.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('文件已保存')
