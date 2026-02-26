"""
四层记忆架构测试脚本

测试 M6 傻瓜层最后一个功能：四层记忆架构 + 自动流转逻辑
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

import tempfile
import shutil
from datetime import datetime, timedelta

# 导入测试组件
from ux.memory_layers import (
    MemoryLayerManager,
    MemoryLayerType,
    LayerConfig,
    create_memory_layers,
    DEFAULT_LAYER_CONFIGS
)


def test_basic_structure():
    """测试基本结构"""
    print("\n" + "="*60)
    print("测试1: 四层记忆架构基本结构")
    print("="*60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        # 创建管理器
        manager = create_memory_layers(data_dir=tmpdir, auto_migrate=False)
        
        # 验证四层都存在
        layers = [MemoryLayerType.WORKING, MemoryLayerType.SHORT_TERM, 
                  MemoryLayerType.LONG_TERM, MemoryLayerType.PERMANENT]
        
        for layer_type in layers:
            assert layer_type in manager.layers, f"缺少层: {layer_type}"
            print(f"  ✓ {layer_type.value} 层已创建")
        
        # 验证配置
        for layer_type in layers:
            config = manager.configs[layer_type]
            print(f"  ✓ {layer_type.value}: {config.name}")
            print(f"    - 描述: {config.description}")
            print(f"    - 最大年龄: {config.max_age_days} 天")
            print(f"    - 最小重要性: {config.min_importance}")
            print(f"    - 最小访问频率: {config.min_access_frequency}/天")
        
        print("\n✅ 测试1通过: 四层架构结构正确")
        return True
    finally:
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_auto_layer_assignment():
    """测试自动分层"""
    print("\n" + "="*60)
    print("测试2: 自动分层逻辑")
    print("="*60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        manager = create_memory_layers(data_dir=tmpdir, auto_migrate=False)
        
        # 添加不同重要性的记忆
        perm_id = manager.add(
            content="安哥是Simon，安仔的哥哥",
            memory_type="fact",
            importance=5.0,
            tags=["身份", "核心"]
        )
        
        long_id = manager.add(
            content="安哥喜欢喝咖啡",
            memory_type="preference",
            importance=4.0,
            tags=["咖啡"]
        )
        
        short_id = manager.add(
            content="今天天气不错",
            memory_type="context",
            importance=2.0,
            tags=["天气"]
        )
        
        # 验证分层
        stats = manager.get_stats()
        print(f"  永久记忆层: {stats['layers']['permanent']['count']} 条")
        print(f"  长期记忆层: {stats['layers']['long']['count']} 条")
        print(f"  短期记忆层: {stats['layers']['short']['count']} 条")
        print(f"  工作记忆层: {stats['layers']['working']['count']} 条")
        
        # 验证高重要性记忆在永久层
        assert stats['layers']['permanent']['count'] >= 1, "永久记忆层应该有内容"
        assert stats['layers']['long']['count'] >= 1, "长期记忆层应该有内容"
        assert stats['layers']['short']['count'] >= 1, "短期记忆层应该有内容"
        
        print("\n✅ 测试2通过: 自动分层逻辑正确")
        return True
    finally:
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_cross_layer_retrieval():
    """测试跨层检索"""
    print("\n" + "="*60)
    print("测试3: 跨层检索")
    print("="*60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        manager = create_memory_layers(data_dir=tmpdir, auto_migrate=False)
        
        # 添加测试数据
        id1 = manager.add("安哥喜欢喝咖啡", "preference", 4.0, ["咖啡"])
        id2 = manager.add("安哥喜欢喝茶", "preference", 3.5, ["茶"])
        id3 = manager.add("安哥是程序员", "fact", 4.5, ["职业"])
        
        # 测试跨层获取
        memory = manager.get(id1)
        assert memory is not None, "应该能找到记忆"
        assert memory.content == "安哥喜欢喝咖啡", "内容应该匹配"
        print(f"  ✓ 成功获取记忆: {memory.content}")
        print(f"  ✓ 访问次数: {memory.access_count}")
        
        # 测试关键词搜索
        results = manager.search_by_keywords(["安哥"], limit=10)
        assert len(results) >= 3, f"应该找到至少3条，实际找到{len(results)}条"
        print(f"  ✓ 关键词搜索 '安哥' 找到 {len(results)} 条")
        
        # 测试按类型查询
        results = manager.query(memory_type="preference", limit=10)
        assert len(results) >= 2, f"应该找到至少2条preference"
        print(f"  ✓ 按类型查询找到 {len(results)} 条 preference")
        
        print("\n✅ 测试3通过: 跨层检索功能正常")
        return True
    finally:
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_timeline_view():
    """测试时间线视图"""
    print("\n" + "="*60)
    print("测试4: 时间线视图")
    print("="*60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        manager = create_memory_layers(data_dir=tmpdir, auto_migrate=False)
        
        # 添加测试数据
        manager.add("记忆1", "fact", 3.0)
        manager.add("记忆2", "context", 2.0)
        manager.add("记忆3", "preference", 4.0)
        
        # 获取时间线
        timeline = manager.get_timeline(days=7)
        assert len(timeline) >= 3, f"时间线应该有至少3条，实际{len(timeline)}条"
        print(f"  ✓ 时间线包含 {len(timeline)} 条记录")
        
        # 验证时间线格式
        for item in timeline[:3]:
            assert "memory_id" in item, "应该有memory_id"
            assert "content" in item, "应该有content"
            assert "created_at" in item, "应该有created_at"
            assert "layer" in item, "应该有layer"
            print(f"  ✓ 记录: {item['content'][:20]}... (层: {item['layer']})")
        
        print("\n✅ 测试4通过: 时间线视图功能正常")
        return True
    finally:
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_migration_logic():
    """测试自动流转逻辑"""
    print("\n" + "="*60)
    print("测试5: 自动流转逻辑")
    print("="*60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        manager = create_memory_layers(data_dir=tmpdir, auto_migrate=True)
        
        # 添加测试数据
        manager.add("高频访问记忆", "fact", 3.0)
        manager.add("普通记忆", "context", 2.0)
        
        # 模拟多次访问
        memories = manager.query(limit=10)
        for memory in memories:
            for _ in range(5):  # 访问5次
                m = manager.get(memory.memory_id)
        
        print(f"  ✓ 模拟访问完成")
        
        # 执行迁移
        migration_stats = manager.run_migration()
        print(f"  ✓ 迁移统计:")
        print(f"    - 晋升: {migration_stats['promotions']} 条")
        print(f"    - 降级: {migration_stats['demotions']} 条")
        
        # 验证迁移逻辑存在
        assert "promotions" in migration_stats, "应该有promotions统计"
        assert "demotions" in migration_stats, "应该有demotions统计"
        
        print("\n✅ 测试5通过: 自动流转逻辑正常")
        return True
    finally:
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_layer_config():
    """测试层配置"""
    print("\n" + "="*60)
    print("测试6: 层配置验证")
    print("="*60)
    
    # 验证默认配置
    configs = DEFAULT_LAYER_CONFIGS
    
    # 工作记忆配置
    work_config = configs[MemoryLayerType.WORKING]
    assert work_config.max_age_days == 1, "工作记忆应该是1天"
    assert work_config.min_importance == 1.0, "工作记忆最小重要性是1.0"
    print(f"  ✓ 工作记忆: 最大{work_config.max_age_days}天, 最小重要性{work_config.min_importance}")
    
    # 短期记忆配置
    short_config = configs[MemoryLayerType.SHORT_TERM]
    assert short_config.max_age_days == 7, "短期记忆应该是7天"
    print(f"  ✓ 短期记忆: 最大{short_config.max_age_days}天")
    
    # 长期记忆配置
    long_config = configs[MemoryLayerType.LONG_TERM]
    assert long_config.max_age_days == 30, "长期记忆应该是30天"
    assert long_config.min_importance == 3.0, "长期记忆最小重要性是3.0"
    print(f"  ✓ 长期记忆: 最大{long_config.max_age_days}天, 最小重要性{long_config.min_importance}")
    
    # 永久记忆配置
    perm_config = configs[MemoryLayerType.PERMANENT]
    assert perm_config.max_age_days is None, "永久记忆无时间限制"
    assert perm_config.min_importance == 4.5, "永久记忆最小重要性是4.5"
    print(f"  ✓ 永久记忆: 无时间限制, 最小重要性{perm_config.min_importance}")
    
    print("\n✅ 测试6通过: 层配置正确")
    return True


def test_stats():
    """测试统计功能"""
    print("\n" + "="*60)
    print("测试7: 统计功能")
    print("="*60)
    
    tmpdir = tempfile.mkdtemp()
    try:
        manager = create_memory_layers(data_dir=tmpdir, auto_migrate=False)
        
        # 添加数据
        manager.add("测试1", "fact", 3.0)
        manager.add("测试2", "context", 2.0)
        
        # 获取统计
        stats = manager.get_stats()
        
        assert "layers" in stats, "应该有layers统计"
        assert "operations" in stats, "应该有operations统计"
        assert "total_memories" in stats, "应该有total_memories"
        
        print(f"  ✓ 总记忆数: {stats['total_memories']}")
        print(f"  ✓ 添加操作数: {stats['operations']['total_added']}")
        
        for layer_name, layer_stat in stats['layers'].items():
            print(f"  ✓ {layer_name}: {layer_stat['count']} 条")
        
        print("\n✅ 测试7通过: 统计功能正常")
        return True
    finally:
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    """主测试函数"""
    print("="*60)
    print("四层记忆架构测试套件")
    print("="*60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        test_basic_structure,
        test_layer_config,
        test_auto_layer_assignment,
        test_cross_layer_retrieval,
        test_timeline_view,
        test_migration_logic,
        test_stats,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ 测试失败: {test.__name__}")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    print(f"通过: {passed}/{len(tests)}")
    print(f"失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 所有测试通过!")
        return 0
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
