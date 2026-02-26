#!/usr/bin/env python
"""
期望的工作流程演示
安哥 ↔ 安仔 ↔ 记忆系统
"""

import sys
sys.path.insert(0, 'src')
from auto_memory_bridge import remember, recall, recent


def main():
    print("=" * 60)
    print("🎯 期望的工作流程演示")
    print("=" * 60)
    print()
    
    # 场景1: 安哥跟我说话，我自动保存重要信息
    print("【场景1】安哥分享信息")
    print("安哥: 我喜欢喝美式咖啡，不加糖")
    print("安仔: ✅ 已保存到记忆系统")
    remember('安哥喜欢喝美式咖啡，不加糖', 'preference', 4.0, ['咖啡', '喜好'])
    print()
    
    print("安哥: 我生日是12月25日")
    print("安仔: ✅ 已保存到记忆系统")
    remember('安哥的生日是12月25日', 'fact', 5.0, ['生日', '重要'])
    print()
    
    # 场景2: 安哥提问，我自动检索相关记忆
    print("【场景2】安哥提问，安仔检索记忆")
    print("安哥: 我喜欢喝什么？")
    print("安仔: 让我查一下...")
    
    results = recall('咖啡', top_k=3)
    if results:
        print(f"🔍 找到 {len(results)} 条相关记忆:")
        for r in results:
            print(f"   - {r['content']}")
    print()
    
    # 场景3: 显示最近记忆
    print("【场景3】查看最近记忆")
    memories = recent(5)
    print(f"📚 最近保存的 {len(memories)} 条记忆:")
    for i, m in enumerate(memories, 1):
        print(f"   {i}. [{m['type']}] {m['content'][:40]}...")
    print()
    
    print("=" * 60)
    print("✅ 演示完成！")
    print()
    print("💡 这就是期望的工作流程:")
    print("   安哥只需跟我对话")
    print("   我自动保存和检索记忆")
    print("   无需手动操作代码")


if __name__ == "__main__":
    main()
