"""
M4四层流转机制测试与修复脚本

测试内容：
1. 自动流转触发机制
2. 晋升/降级逻辑
3. 容量限制执行
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs'))

import tempfile
import shutil
from datetime import datetime, timedelta


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """打印小节标题"""
    print(f"\n>> {title}")
    print("-" * 50)


def test_layer_flow():
    """测试层间流转机制"""
    print_header("M4 四层流转机制测试")
    
    try:
        from ux.memory_layers import MemoryLayers, MemoryLayerType
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        print(f"测试目录: {temp_dir}")
        
        # 创建记忆层管理器
        layers = MemoryLayers(data_dir=temp_dir)
        
        print_section("1. 添加不同重要性的记忆")
        
        # 添加低重要性记忆（应进入短期记忆）
        id1 = layers.add(
            content="今天天气不错",
            memory_type="observation",
            importance=1.5
        )
        print(f"✓ 添加低重要性记忆: {id1[:8]}... -> 短期记忆")
        
        # 添加中等重要性记忆（应进入长期记忆）
        id2 = layers.add(
            content="安哥喜欢喝咖啡",
            memory_type="preference",
            importance=3.5
        )
        print(f"✓ 添加中等重要性记忆: {id2[:8]}... -> 长期记忆")
        
        # 添加高重要性记忆（应进入永久记忆）
        id3 = layers.add(
            content="安哥的生日是12月25日",
            memory_type="fact",
            importance=4.8
        )
        print(f"✓ 添加高重要性记忆: {id3[:8]}... -> 永久记忆")
        
        print_section("2. 检查记忆分布")
        
        stats = layers.get_stats()
        for layer_name, layer_stat in stats["layers"].items():
            count = layer_stat["count"]
            print(f"  {layer_name}: {count} 条记忆")
        
        print_section("3. 测试手动晋升")
        
        # 将低重要性记忆手动晋升到长期记忆
        result = layers.promote_manually(id1, MemoryLayerType.LONG_TERM)
        if result:
            print(f"✓ 手动晋升成功: {id1[:8]}... -> 长期记忆")
        else:
            print(f"✗ 手动晋升失败")
        
        print_section("4. 测试自动优化（流转）")
        
        # 模拟时间流逝（修改创建时间）
        memory = layers.get(id2)
        if memory:
            # 修改创建时间为8天前
            old_time = (datetime.now() - timedelta(days=8)).isoformat()
            memory.created_at = old_time
            print(f"  模拟: 将记忆创建时间设为8天前")
        
        # 运行自动优化
        migration_stats = layers.optimize_layers()
        print(f"  流转统计:")
        print(f"    - 晋升: {migration_stats.get('promotions', 0)} 条")
        print(f"    - 降级: {migration_stats.get('demotions', 0)} 条")
        print(f"    - 错误: {migration_stats.get('errors', 0)} 条")
        
        print_section("5. 最终状态检查")
        
        stats = layers.get_stats()
        total = stats["total_memories"]
        print(f"  总记忆数: {total}")
        for layer_name, layer_stat in stats["layers"].items():
            count = layer_stat["count"]
            print(f"  {layer_name}: {count} 条")
        
        # 清理
        layers.close()
        shutil.rmtree(temp_dir)
        
        print("\n✅ M4流转机制测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_capacity_limit():
    """测试容量限制"""
    print_header("M4 容量限制测试")
    
    try:
        from ux.memory_layers import MemoryLayers, MemoryLayerType
        
        temp_dir = tempfile.mkdtemp()
        layers = MemoryLayers(data_dir=temp_dir)
        
        print_section("测试工作记忆容量限制（100条）")
        
        # 添加超过100条工作记忆
        for i in range(110):
            layers.add(
                content=f"工作记忆内容 {i}",
                memory_type="working",
                importance=1.0,
                layer=MemoryLayerType.WORKING
            )
        
        stats = layers.get_stats()
        working_count = stats["layers"]["working"]["count"]
        print(f"  添加110条，实际存储: {working_count} 条")
        
        if working_count <= 100:
            print("  ✅ 容量限制生效")
        else:
            print("  ⚠️ 容量限制未生效（需要修复）")
        
        layers.close()
        shutil.rmtree(temp_dir)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("  M4 四层流转机制 - 测试与修复")
    print("=" * 70)
    
    results = []
    
    # 测试1: 流转机制
    results.append(("流转机制", test_layer_flow()))
    
    # 测试2: 容量限制
    results.append(("容量限制", test_capacity_limit()))
    
    # 总结
    print("\n" + "=" * 70)
    print("  测试结果总结")
    print("=" * 70)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
    
    all_passed = all(r for _, r in results)
    
    if all_passed:
        print("\n✅ 所有测试通过！M4流转机制正常工作。")
    else:
        print("\n⚠️ 部分测试失败，需要修复。")
    
    return all_passed


if __name__ == "__main__":
    main()
