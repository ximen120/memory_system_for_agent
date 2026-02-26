#!/usr/bin/env python
"""
记忆系统暗号验证

使用方式:
    安哥说: "天王盖地虎"
    安仔回: "宝塔镇河妖"
    
    对上了 = 记忆系统已启动
"""

import sys
sys.path.insert(0, 'src')

from memory_initializer import load_memory, is_memory_ready

# 暗号配置
CODE_QUESTION = "天王盖地虎"
CODE_ANSWER = "宝塔镇河妖"


def verify_code(user_input: str) -> dict:
    """
    验证暗号
    
    Args:
        user_input: 用户输入
        
    Returns:
        {
            'matched': 是否对上暗号,
            'response': 回应,
            'memory_ready': 记忆系统是否就绪
        }
    """
    user_input = user_input.strip()
    
    # 检查是否是暗号
    if CODE_QUESTION in user_input:
        # 先确保记忆系统启动
        if not is_memory_ready():
            load_memory()
        
        return {
            'matched': True,
            'response': CODE_ANSWER,
            'memory_ready': is_memory_ready()
        }
    
    # 如果不是暗号，正常处理
    return {
        'matched': False,
        'response': None,
        'memory_ready': is_memory_ready()
    }


def simple_check() -> str:
    """
    简单检查记忆系统状态
    
    Returns:
        状态字符串
    """
    if is_memory_ready():
        return "🧠 记忆系统运行中"
    else:
        return "💤 记忆系统未启动"


# 测试
if __name__ == "__main__":
    print("🎭 暗号验证测试")
    print("=" * 40)
    print()
    
    # 测试1: 对暗号
    print("安哥: 天王盖地虎")
    result = verify_code("天王盖地虎")
    print(f"安仔: {result['response']}")
    print(f"状态: {'✅ 记忆系统已启动' if result['memory_ready'] else '❌ 未启动'}")
    print()
    
    # 测试2: 检查状态
    print(f"系统状态: {simple_check()}")
