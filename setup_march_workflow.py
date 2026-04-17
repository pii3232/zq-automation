import os
import json
from datetime import datetime

# 设置工作流名称
WORKFLOW_NAME = "调动"

# 定义工作流步骤
workflow_steps = [
    # 步骤1: 如果找到1-CC.png图片文件，就获得坐标，点击该坐标，等待1秒
    {
        "keyword": "找图",
        "params": "1-CC.png"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 步骤2: 等待1秒
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 步骤3: 如果找到1-TC.png图片文件，就获得坐标，点击该坐标，等待1秒
    {
        "keyword": "找图",
        "params": "1-TC.png"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 步骤4: 等待1秒
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 步骤5: 如果找到1-TC.png图片文件，就获得坐标，点击该坐标，等待1秒
    {
        "keyword": "找图",
        "params": "1-TC.png"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 步骤6: 等待1秒
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 步骤7: 查找1-HC.png图片文件
    # 分支1: 如果不找到该图片就点击坐标67,700，等待2秒
    {
        "keyword": "找图",
        "params": "1-HC.png"
    },
    {
        "keyword": "点击",
        "params": "67,700"
    },
    {
        "keyword": "间隔",
        "params": "2000"
    },
    # 分支2: 如果找到，直接执行下面的指令
    # 点击坐标36,522 (8次)
    {
        "keyword": "点击",
        "params": "36,522"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    {
        "keyword": "点击",
        "params": "36,522"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    {
        "keyword": "点击",
        "params": "36,522"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    {
        "keyword": "点击",
        "params": "36,522"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    {
        "keyword": "点击",
        "params": "36,522"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    {
        "keyword": "点击",
        "params": "36,522"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    {
        "keyword": "点击",
        "params": "36,522"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    {
        "keyword": "点击",
        "params": "36,522"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 点击坐标978,718
    {
        "keyword": "点击",
        "params": "978,718"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 输入关键参数 (用户设置)
    {
        "keyword": "键盘输入",
        "params": "${坐标参数}"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 点击坐标1240,708
    {
        "keyword": "点击",
        "params": "1240,708"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 点击坐标1158,718
    {
        "keyword": "点击",
        "params": "1158,718"
    },
    {
        "keyword": "间隔",
        "params": "2000"
    },
    # 点击坐标666,386
    {
        "keyword": "点击",
        "params": "666,386"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 步骤8: 如果找到1-DD.png图片文件，就获得坐标，点击该坐标，等待1秒
    {
        "keyword": "找图",
        "params": "1-DD.png"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 步骤9: 等待1秒
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 步骤10: 如果找到1-CZ.png图片文件，就获得坐标，点击该坐标，等待1秒
    {
        "keyword": "找图",
        "params": "1-CZ.png"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 步骤11: 等待1秒
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 步骤12: 如果找到1-CZ.png图片文件，就获得坐标，点击该坐标，等待1秒
    {
        "keyword": "找图",
        "params": "1-CZ.png"
    },
    {
        "keyword": "间隔",
        "params": "1000"
    },
    # 步骤13: 等待1秒
    {
        "keyword": "间隔",
        "params": "1000"
    }
]

def setup_workflow():
    # 1. 创建或更新工作流文件
    project_dir = "e:\\5-ZDZS-TXA5\\3MCWB"
    workflows_file = os.path.join(project_dir, "workflows.json")
    
    # 读取现有工作流
    if os.path.exists(workflows_file):
        with open(workflows_file, 'r', encoding='utf-8') as f:
            workflows = json.load(f)
    else:
        workflows = []
    
    # 检查是否已存在同名工作流
    existing_index = -1
    for i, wf in enumerate(workflows):
        if wf['name'] == WORKFLOW_NAME:
            existing_index = i
            break
    
    # 创建工作流对象
    workflow = {
        "name": WORKFLOW_NAME,
        "description": "调动工作流：按指定流程执行调动操作",
        "steps": workflow_steps,
        "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # 更新或添加工作流
    if existing_index >= 0:
        workflows[existing_index] = workflow
    else:
        workflows.append(workflow)
    
    # 保存工作流
    with open(workflows_file, 'w', encoding='utf-8') as f:
        json.dump(workflows, f, ensure_ascii=False, indent=2)
    
    print(f"工作流 '{WORKFLOW_NAME}' 已成功创建/更新！")
    
    # 2. 更新命令模板
    tabs_file = "e:\\5-ZDZS-TXA5\\tabs.py"
    
    # 读取tabs.py文件
    with open(tabs_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并更新BUILTIN_COMMAND_TEMPLATES中的"调动"模板
    import re
    
    # 定义要替换的内容
    new_template_content = '''    "调动": {
        "type": "march",
        "description": "调动：点击指定坐标并执行工作流",
        "has_multi_coords": True,
        "has_auto_input": True,
        "template": {
            "coords": [{"x": 0, "y": 0, "label": "坐标参数"}],
            "workflows": ["调动"],
            "exec_mode": "immediate"
        }
    }'''    
    
    # 使用正则表达式替换
    pattern = r'    "调动": \{[^}]*\}'
    updated_content = re.sub(pattern, new_template_content, content, flags=re.DOTALL)
    
    # 保存更新后的文件
    with open(tabs_file, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"命令模板 '调动' 已成功更新！")
    
    # 3. 提示用户将图片文件放到正确位置
    print("\n请将以下图片文件放到对应工作组同步目录：")
    print(f"E:\\5-ZDZS-TXA5\\3MCWB\\workgroups\\2\\")
    print("\n需要的图片文件：")
    print("- 1-CC.png")
    print("- 1-TC.png")
    print("- 1-HC.png")
    print("- 1-DD.png")
    print("- 1-CZ.png")

if __name__ == "__main__":
    setup_workflow()