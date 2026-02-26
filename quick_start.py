#!/usr/bin/env python
"""
记忆系统 v3.0 快速启动（内存模式）
无需加载大模型，启动更快
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.memory_api import MemoryAPI


def main():
    print("🚀 记忆系统 v3.0 快速启动（内存模式）")
    print("=" * 60)
    
    try:
        # 创建API实例（内存模式，不加载大模型）
        api = MemoryAPI()
        print("✅ API实例创建成功（内存模式）")
        
        # 测试1: 保存记忆
        memory_id = api.add_memory(
            content='安哥喜欢喝美式咖啡',
            importance=4.0,
            tags=['咖啡', '喜好']
        )
        print(f"✅ 保存记忆: {memory_id[:8]}...")
        
        # 测试2: 查询记忆
        results = api.search_memories('咖啡')
        print(f"✅ 查询记忆: 找到 {len(results)} 条")
        for r in results[:3]:
            print(f"   - {r.get('content', '')[:30]}...")
        
        # 测试3: 查看统计
        stats = api.get_stats()
        print(f"✅ 系统统计: 共 {stats.get('total_memories', 0)} 条记忆")
        
        print("=" * 60)
        print("🎉 系统启动成功！")
        print()
        print("💡 提示: 这是内存模式，数据保存在内存中")
        print("   如需持久化存储，请使用完整模式")
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
