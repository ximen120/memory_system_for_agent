#!/usr/bin/env python
"""
记忆系统 v3.0 启动脚本

使用方法:
    python start_memory_system.py
"""

import sys
import os

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from api.unified_api import UnifiedAPI


def main():
    """主函数"""
    print("🚀 记忆系统 v3.0 启动")
    print("=" * 60)
    
    # 创建API实例
    api = UnifiedAPI()
    
    print("✅ 系统启动成功！")
    print()
    
    # 显示菜单
    while True:
        print("\n📋 功能菜单:")
        print("  1. 保存记忆 (remember)")
        print("  2. 查询记忆 (recall)")
        print("  3. 删除记忆 (forget)")
        print("  4. 更新记忆 (update)")
        print("  5. 列出所有 (list)")
        print("  6. 系统统计 (stats)")
        print("  0. 退出")
        print()
        
        choice = input("请选择功能 (0-6): ").strip()
        
        if choice == "1":
            content = input("请输入记忆内容: ")
            importance = float(input("重要性 (1.0-5.0, 默认3.0): ") or "3.0")
            memory_id = api.remember(content, importance=importance)
            print(f"✅ 记忆已保存: {memory_id}")
            
        elif choice == "2":
            query = input("请输入查询关键词: ")
            results = api.recall(query)
            print(f"\n🔍 找到 {len(results)} 条相关记忆:")
            for i, result in enumerate(results, 1):
                print(f"  {i}. {result}")
                
        elif choice == "3":
            memory_id = input("请输入记忆ID: ")
            if api.forget(memory_id):
                print("✅ 记忆已删除")
            else:
                print("❌ 删除失败")
                
        elif choice == "4":
            memory_id = input("请输入记忆ID: ")
            content = input("请输入新内容: ")
            if api.update(memory_id, content=content):
                print("✅ 记忆已更新")
            else:
                print("❌ 更新失败")
                
        elif choice == "5":
            memories = api.list_all()
            print(f"\n📚 共 {len(memories)} 条记忆:")
            for m in memories[:10]:  # 只显示前10条
                print(f"  - [{m.get('memory_id', 'N/A')[:8]}] {m.get('content', '')[:30]}...")
            if len(memories) > 10:
                print(f"  ... 还有 {len(memories) - 10} 条")
                
        elif choice == "6":
            stats = api.get_stats()
            print(f"\n📊 系统统计:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
                
        elif choice == "0":
            print("\n👋 再见！")
            break
            
        else:
            print("❌ 无效选择，请重试")


if __name__ == "__main__":
    main()
