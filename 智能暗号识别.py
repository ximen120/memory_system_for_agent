#!/usr/bin/env python
"""
智能暗号识别系统

功能：识别安哥的指令并自动执行
"""

import sys
import os
import subprocess

# 暗号库
COMMANDS = {
    "记忆3.0": {
        "description": "启动记忆系统v3.0",
        "action": r"C:\Users\Simon\.conda\envs\memory_v3\python.exe D:\wordir\memory_system_v3\记忆3_0启动器.py",
        "response": "🧠 记忆3.0 启动成功！"
    },
    "加载记忆": {
        "description": "完整加载记忆系统并生成报告",
        "action": r"C:\Users\Simon\.conda\envs\memory_v3\python.exe D:\wordir\memory_system_v3\LOAD_MEMORY.py",
        "response": "📋 记忆系统加载完成，执行报告已生成"
    },
    "天王盖地虎": {
        "description": "验证记忆系统状态",
        "action": None,  # 特殊处理
        "response": "宝塔镇河妖 - 记忆系统已就绪！"
    }
}


def detect_and_execute(user_input: str) -> dict:
    """
    检测用户输入中的暗号并执行
    
    Args:
        user_input: 用户输入的文本
        
    Returns:
        {
            'detected': 是否检测到暗号,
            'command': 检测到的指令,
            'executed': 是否执行成功,
            'output': 执行输出,
            'response': 回复内容
        }
    """
    result = {
        'detected': False,
        'command': None,
        'executed': False,
        'output': '',
        'response': ''
    }
    
    # 检测暗号
    for keyword, config in COMMANDS.items():
        if keyword in user_input:
            result['detected'] = True
            result['command'] = keyword
            
            # 特殊处理：天王盖地虎
            if keyword == "天王盖地虎":
                result['response'] = config['response']
                result['executed'] = True
                return result
            
            # 执行命令
            try:
                process = subprocess.run(
                    config['action'],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                result['output'] = process.stdout
                result['executed'] = process.returncode == 0
                
                if result['executed']:
                    result['response'] = config['response'] + "\n\n" + process.stdout
                else:
                    result['response'] = f"❌ 执行失败:\n{process.stderr}"
                    
            except Exception as e:
                result['response'] = f"❌ 执行异常: {str(e)}"
            
            return result
    
    # 没有检测到暗号
    return result


if __name__ == "__main__":
    # 测试
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        result = detect_and_execute(user_input)
        
        if result['detected']:
            print(result['response'])
        else:
            print("未检测到暗号")
    else:
        # 默认测试
        test_inputs = [
            "记忆3.0",
            "天王盖地虎",
            "加载记忆"
        ]
        
        for test in test_inputs:
            print(f"\n测试: {test}")
            print("-" * 40)
            result = detect_and_execute(test)
            if result['detected']:
                print(f"✅ 检测到: {result['command']}")
                print(f"回复: {result['response'][:100]}...")
            else:
                print("❌ 未检测到")
