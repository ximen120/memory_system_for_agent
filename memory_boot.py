#!/usr/bin/env python
"""
记忆系统启动器 - 全局可用版本

使用方法:
    1. 直接运行: python D:\wordir\memory_system_v3\memory_boot.py
    2. Python导入: from memory_boot import boot_memory
    
功能: 无论从哪里调用，都能正确启动记忆系统
"""

import sys
import os

# 自动设置正确的路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, os.path.join(SCRIPT_DIR, 'src'))

# 设置工作目录为脚本所在目录（确保数据路径正确）
os.chdir(SCRIPT_DIR)

def boot_memory():
    """
    启动记忆系统
    
    Returns:
        dict: 启动结果
    """
    try:
        from memory_initializer import load_memory
        result = load_memory()
        
        if result['ready']:
            print("✅ 记忆系统启动成功")
            total = result['stats'].get('total_memories', 0)
            recent = result['stats'].get('recent_memories', 0)
            print(f"📚 共 {total} 条记忆 | 最近 {recent} 条已加载")
            return True
        else:
            print(f"❌ 启动失败: {result['status']}")
            return False
            
    except Exception as e:
        print(f"❌ 启动异常: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_memory_bridge():
    """获取记忆桥梁实例"""
    from memory_initializer import MemoryInitializer
    return MemoryInitializer.get_bridge()


def remember(content, memory_type='context', importance=3.0, tags=None):
    """保存记忆"""
    from auto_memory_bridge import remember as _remember
    return _remember(content, memory_type, importance, tags)


def recall(query, top_k=5):
    """检索记忆"""
    from auto_memory_bridge import recall as _recall
    return _recall(query, top_k)


if __name__ == "__main__":
    # 直接运行时启动记忆系统
    success = boot_memory()
    sys.exit(0 if success else 1)
