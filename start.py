#!/usr/bin/env python
"""
记忆系统 v3.0 启动脚本
最简单的使用方式
"""

import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.memory_unit import MemoryUnit
from storage.json_storage import JsonStorage


def main():
    print("🚀 记忆系统 v3.0")
    print("=" * 60)
    
    # 创建存储
    storage = JsonStorage('./data/my_memories')
    print("✅ 存储已初始化")
    
    # 添加记忆
    print("\n📥 添加记忆...")
    
    m1 = MemoryUnit(
        content="安哥喜欢喝美式咖啡",
        memory_type="preference",
        importance=4.0,
        tags=["咖啡", "喜好"]
    )
    id1 = storage.save(m1)
    print(f"  ✅ {m1.content}")
    
    m2 = MemoryUnit(
        content="今天完成了记忆系统v3.0",
        memory_type="event",
        importance=3.5,
        tags=["项目"]
    )
    id2 = storage.save(m2)
    print(f"  ✅ {m2.content}")
    
    # 列出所有记忆
    print("\n📚 所有记忆:")
    memories = storage.query(limit=100)
    for i, m in enumerate(memories, 1):
        print(f"  {i}. [{m.memory_type}] {m.content}")
    
    # 搜索记忆（简单关键词匹配）
    print("\n🔍 搜索 '咖啡':")
    results = [m for m in memories if "咖啡" in m.content]
    for m in results:
        print(f"  - {m.content}")
    
    print("\n" + "=" * 60)
    print("✅ 演示完成！")
    print(f"📁 数据保存在: ./data/my_memories/")


if __name__ == "__main__":
    main()
