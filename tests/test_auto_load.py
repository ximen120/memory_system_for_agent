"""
测试自动加载上下文功能
"""
import sys
import os

# 添加项目路径
project_dir = r"D:\projects\memory_system_v3"
sys.path.insert(0, os.path.join(project_dir, 'src'))

# 清除可能的环境变量
if 'MEMORY_AUTO_LOAD_DONE' in os.environ:
    del os.environ['MEMORY_AUTO_LOAD_DONE']

# 测试CoreMemoryManager
print("=" * 60)
print("测试 CoreMemoryManager")
print("=" * 60)

try:
    from core.core_memory_manager import CoreMemoryManager
    
    # 创建管理器
    manager = CoreMemoryManager()
    print(f"✅ CoreMemoryManager 创建成功")
    print(f"   基础路径: {manager.base_path}")
    
    # 获取最近记忆
    memories = manager.get_recent_memories(limit=5, tier="core")
    print(f"\n✅ 找到 {len(memories)} 条核心记忆")
    
    # 测试markdown格式
    print("\n" + "=" * 60)
    print("Markdown 格式输出:")
    print("=" * 60)
    markdown_output = manager.format_markdown(memories)
    print(markdown_output)
    
    # 测试json格式
    print("\n" + "=" * 60)
    print("JSON 格式输出:")
    print("=" * 60)
    json_output = manager.format_json(memories)
    print(json_output)
    
except Exception as e:
    print(f"❌ CoreMemoryManager 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试MemorySystem的auto_load_context
print("\n" + "=" * 60)
print("测试 MemorySystem.auto_load_context()")
print("=" * 60)

try:
    # 清除环境变量
    if 'MEMORY_AUTO_LOAD_DONE' in os.environ:
        del os.environ['MEMORY_AUTO_LOAD_DONE']
    
    from memory_system import MemorySystem
    
    # 创建系统
    system = MemorySystem.create_default()
    print("✅ MemorySystem 创建成功")
    
    # 测试自动加载
    context = system.auto_load_context(limit=5)
    print("\n✅ auto_load_context() 返回:")
    print(context)
    
    # 再次调用（应该返回空字符串，因为已标记加载完成）
    print("\n" + "=" * 60)
    print("再次调用 auto_load_context() (应该返回空):")
    print("=" * 60)
    context2 = system.auto_load_context(limit=5)
    print(f"返回内容长度: {len(context2)}")
    print(f"内容: '{context2}'")
    
    # 关闭系统
    system.close()
    
except Exception as e:
    print(f"❌ MemorySystem 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成!")
print("=" * 60)
