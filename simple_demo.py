#!/usr/bin/env python
"""
记忆系统 v3.0 简单演示
完全绕过模型加载，使用纯关键词检索
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.memory_unit import MemoryUnit
from storage.json_storage import JsonStorage
from retrieval.keyword_search import KeywordSearch


def main():
    print("🚀 记忆系统 v3.0 简单演示")
    print("=" * 60)
    
    # 创建存储
    storage = JsonStorage('./data/demo')
    keyword_search = KeywordSearch()  
    
    print("✅ 存储和检索引擎初始化成功")
    print()
    
    # 添加一些记忆
    print("📥 添加记忆...")
    memories = [
        MemoryUnit(content="安哥喜欢喝美式咖啡", memory_type="preference", importance=4.0, tags=["咖啡", "喜好"]),
        MemoryUnit(content="今天完成了记忆系统v3.0", memory_type="event", importance=3.5, tags=["项目", "完成"]),
        MemoryUnit(content="安哥的生日是12月25日", memory_type="fact", importance=5.0, tags=["生日", "重要"]),
    ]
    
    for memory in memories:
        memory_id = storage.save(memory)
        keyword_search.add_document(memory_id, memory.content, memory_type=memory.memory_type, importance=memory.importance)
        print(f"  ✅ {memory.content[:20]}... (ID: {memory_id[:8]})")
    
    print()
    print("🔍 搜索记忆...")
    
    # 搜索
    query = "咖啡"
    results = keyword_search.search(query, top_k=5)
    print(f"  查询 '{query}' 找到 {len(results)} 条:")
    for r in results:
        print(f"    - {r['content'][:30]}... (相关度: {r['score']:.2f})")
    
    print()
    print("📊 统计信息:")
    all_memories = storage.get_all()
    print(f"  总记忆数: {len(all_memories)}")
    
    print()
    print("=" * 60)
    print("🎉 演示完成！")
    print()
    print("💡 说明:")
    print("  - 数据保存在: ./data/demo/")
    print("  - 使用关键词检索（无需模型）")
    print("  - 可以在此基础上扩展更多功能")


if __name__ == "__main__":
    main()
