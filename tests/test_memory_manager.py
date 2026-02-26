"""
记忆管理器单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

import pytest
import tempfile
import shutil
from memory_manager import MemoryManager, MemoryTier
from memory_unit import MemoryUnit


class TestMemoryManagerCreation:
    """测试 MemoryManager 创建"""
    
    def test_default_creation(self):
        """测试默认参数创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MemoryManager(data_dir=tmpdir)
            assert manager.data_dir == Path(tmpdir)
            assert manager.embedding_gen is None
            assert len(manager.storages) == 4
    
    def test_custom_tier_hours(self):
        """测试自定义分层时间"""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_hours = {
                MemoryTier.WORKING: 12,
                MemoryTier.SHORT_TERM: 48,
            }
            manager = MemoryManager(data_dir=tmpdir, tier_hours=custom_hours)
            assert manager.tier_hours[MemoryTier.WORKING] == 12
            assert manager.tier_hours[MemoryTier.SHORT_TERM] == 48


class TestMemorySave:
    """测试 save 方法"""
    
    @pytest.fixture
    def manager(self):
        """提供临时管理器"""
        tmpdir = tempfile.mkdtemp()
        manager = MemoryManager(data_dir=tmpdir)
        yield manager
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_save_returns_memory_id(self, manager):
        """测试保存返回 memory_id"""
        memory = MemoryUnit(content="测试内容", memory_type="fact", importance=3)
        result = manager.save(memory)
        assert result == memory.memory_id
    
    def test_save_increases_stats(self, manager):
        """测试保存增加统计"""
        initial = manager.stats["total_saved"]
        memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
        manager.save(memory)
        assert manager.stats["total_saved"] == initial + 1
    
    def test_save_without_embedding(self, manager):
        """测试保存不生成 embedding"""
        memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
        manager.save(memory)
        assert memory.embedding is None


class TestMemoryLoad:
    """测试 load 方法"""
    
    @pytest.fixture
    def manager_with_memory(self):
        """提供带有一条记忆的管理器"""
        tmpdir = tempfile.mkdtemp()
        manager = MemoryManager(data_dir=tmpdir)
        memory = MemoryUnit(content="原始内容", memory_type="fact", importance=3)
        manager.save(memory)
        yield manager, memory
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_load_returns_memory_unit(self, manager_with_memory):
        """测试加载返回 MemoryUnit"""
        manager, original = manager_with_memory
        loaded = manager.load(original.memory_id)
        
        assert isinstance(loaded, MemoryUnit)
        assert loaded.memory_id == original.memory_id
        assert loaded.content == original.content
    
    def test_load_updates_access_count(self, manager_with_memory):
        """测试加载更新访问计数"""
        manager, original = manager_with_memory
        loaded = manager.load(original.memory_id)
        
        assert loaded.access_count == 1
    
    def test_load_not_found_returns_none(self, manager_with_memory):
        """测试加载不存在返回 None"""
        manager, _ = manager_with_memory
        result = manager.load("nonexistent_id")
        assert result is None


class TestMemoryDelete:
    """测试 delete 方法"""
    
    @pytest.fixture
    def manager_with_memory(self):
        """提供带有一条记忆的管理器"""
        tmpdir = tempfile.mkdtemp()
        manager = MemoryManager(data_dir=tmpdir)
        memory = MemoryUnit(content="测试内容", memory_type="fact", importance=3)
        manager.save(memory)
        yield manager, memory
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_delete_returns_true_when_exists(self, manager_with_memory):
        """测试删除存在记忆返回 True"""
        manager, memory = manager_with_memory
        result = manager.delete(memory.memory_id)
        assert result is True
    
    def test_delete_removes_memory(self, manager_with_memory):
        """测试删除后记忆不存在"""
        manager, memory = manager_with_memory
        manager.delete(memory.memory_id)
        assert manager.load(memory.memory_id) is None
    
    def test_delete_increases_stats(self, manager_with_memory):
        """测试删除增加统计"""
        manager, memory = manager_with_memory
        initial = manager.stats["total_deleted"]
        manager.delete(memory.memory_id)
        assert manager.stats["total_deleted"] == initial + 1
    
    def test_delete_returns_false_when_not_exists(self, manager_with_memory):
        """测试删除不存在返回 False"""
        manager, _ = manager_with_memory
        result = manager.delete("nonexistent_id")
        assert result is False


class TestMemoryQuery:
    """测试 query 方法"""
    
    @pytest.fixture
    def manager_with_memories(self):
        """提供带有多条记忆的管理器"""
        tmpdir = tempfile.mkdtemp()
        manager = MemoryManager(data_dir=tmpdir)
        
        memories = [
            MemoryUnit(content="事实1", memory_type="fact", importance=3, tags=["A"]),
            MemoryUnit(content="事实2", memory_type="fact", importance=4, tags=["B"]),
            MemoryUnit(content="偏好1", memory_type="preference", importance=5, tags=["A", "B"]),
        ]
        
        for memory in memories:
            manager.save(memory)
        
        yield manager, memories
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_query_by_type(self, manager_with_memories):
        """测试按类型查询"""
        manager, _ = manager_with_memories
        results = manager.query(memory_type="fact")
        
        assert len(results) == 2
        for memory in results:
            assert memory.memory_type == "fact"
    
    def test_query_by_tags(self, manager_with_memories):
        """测试按标签查询"""
        manager, _ = manager_with_memories
        results = manager.query(tags=["A"])
        
        assert len(results) == 2
    
    def test_query_by_min_importance(self, manager_with_memories):
        """测试按最小重要度查询"""
        manager, _ = manager_with_memories
        results = manager.query(min_importance=4)
        
        assert len(results) == 2
    
    def test_query_with_limit(self, manager_with_memories):
        """测试限制返回数量"""
        manager, _ = manager_with_memories
        results = manager.query(limit=2)
        
        assert len(results) <= 2
    
    def test_query_sorted_by_importance(self, manager_with_memories):
        """测试结果按重要度排序"""
        manager, _ = manager_with_memories
        results = manager.query(limit=3)
        
        # 应该按重要度降序
        for i in range(len(results) - 1):
            assert results[i].importance >= results[i + 1].importance


class TestMemoryStats:
    """测试统计功能"""
    
    @pytest.fixture
    def manager(self):
        """提供临时管理器"""
        tmpdir = tempfile.mkdtemp()
        manager = MemoryManager(data_dir=tmpdir)
        yield manager
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_get_stats_returns_dict(self, manager):
        """测试 get_stats 返回字典"""
        stats = manager.get_stats()
        
        assert isinstance(stats, dict)
        assert "tier_counts" in stats
        assert "total_memories" in stats
        assert "operations" in stats
        assert "embedding_enabled" in stats
    
    def test_stats_initially_zero(self, manager):
        """测试初始统计为0"""
        stats = manager.get_stats()
        
        assert stats["total_memories"] == 0
        assert stats["tier_counts"][MemoryTier.WORKING] == 0
    
    def test_stats_after_save(self, manager):
        """测试保存后统计更新"""
        memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
        manager.save(memory)
        
        stats = manager.get_stats()
        assert stats["total_memories"] == 1
        assert stats["operations"]["total_saved"] == 1


class TestMemoryTierLogic:
    """测试分层逻辑"""
    
    @pytest.fixture
    def manager(self):
        """提供临时管理器"""
        tmpdir = tempfile.mkdtemp()
        manager = MemoryManager(data_dir=tmpdir)
        yield manager
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_tier_constants(self):
        """测试层级常量"""
        assert MemoryTier.WORKING == "working"
        assert MemoryTier.SHORT_TERM == "short"
        assert MemoryTier.MID_TERM == "mid"
        assert MemoryTier.LONG_TERM == "long"
    
    def test_default_tier_hours(self, manager):
        """测试默认分层时间"""
        assert manager.tier_hours[MemoryTier.WORKING] == 24
        assert manager.tier_hours[MemoryTier.SHORT_TERM] == 24 * 7
        assert manager.tier_hours[MemoryTier.MID_TERM] == 24 * 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
