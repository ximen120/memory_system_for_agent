"""
ChromaDB 存储单元测试（Windows文件锁定问题修复版）

使用内存模式运行测试，避免Windows文件锁定问题
"""

import os
# 强制使用内存模式，避免Windows文件锁定
os.environ['TEST_MODE'] = 'true'

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "storage"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

import pytest
import tempfile
import shutil
from chroma_storage import ChromaStorage, chroma_storage_context
from base_storage import StorageError, MemoryNotFoundError
from memory_unit import MemoryUnit


# 测试配置
USE_MEMORY_MODE = True  # 始终使用内存模式运行测试
print(f"[ChromaDB测试] 使用内存模式: {USE_MEMORY_MODE}")


class TestChromaStorageCreation:
    """测试 ChromaStorage 创建"""
    
    def test_create_with_default_path(self):
        """测试使用默认参数创建"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        with chroma_storage_context(f"./test_chroma_{unique_id}", f"test_collection_{unique_id}", use_memory_mode=True) as storage:
            assert storage.storage_name == "chroma"
            assert storage.collection_name == f"test_collection_{unique_id}"
    
    def test_create_creates_directory(self):
        """测试创建时自动创建目录（内存模式下无实际目录）"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        with chroma_storage_context(f"./test_chroma_{unique_id}", f"test_{unique_id}", use_memory_mode=True) as storage:
            # 内存模式下不创建实际目录
            assert storage.use_memory_mode is True


class TestChromaStorageSave:
    """测试 save 方法"""
    
    @pytest.fixture
    def storage(self):
        """提供临时存储（使用内存模式，唯一集合名）"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        with chroma_storage_context(f"./test_save_{unique_id}", f"test_save_{unique_id}", use_memory_mode=True) as storage:
            yield storage
    
    def test_save_returns_memory_id(self, storage):
        """测试保存返回 memory_id"""
        memory = MemoryUnit(content="测试内容", memory_type="fact", importance=3)
        result = storage.save(memory)
        assert result == memory.memory_id
    
    def test_save_increases_count(self, storage):
        """测试保存后计数增加"""
        initial_count = storage.count()
        memory = MemoryUnit(content="测试内容", memory_type="fact", importance=3)
        storage.save(memory)
        
        assert storage.count() == initial_count + 1
    
    def test_save_with_embedding(self, storage):
        """测试保存带向量的记忆"""
        memory = MemoryUnit(
            content="测试内容",
            memory_type="fact",
            importance=3,
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5]
        )
        storage.save(memory)
        
        loaded = storage.load(memory.memory_id)
        assert loaded.embedding is not None
        assert len(loaded.embedding) == 5


class TestChromaStorageLoad:
    """测试 load 方法"""
    
    @pytest.fixture
    def storage_with_memory(self):
        """提供带有一条记忆的临时存储（使用内存模式，唯一集合名）"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        with chroma_storage_context(f"./test_load_{unique_id}", f"test_load_{unique_id}", use_memory_mode=True) as storage:
            memory = MemoryUnit(
                content="原始内容",
                memory_type="preference",
                importance=4.5,
                tags=["标签1", "标签2"],
                source="test_source",
                embedding=[0.1, 0.2, 0.3]
            )
            storage.save(memory)
            yield storage, memory
            # 上下文管理器会自动关闭连接
        
    def test_load_returns_memory_unit(self, storage_with_memory):
        """测试加载返回 MemoryUnit"""
        storage, original = storage_with_memory
        loaded = storage.get(original.memory_id)
        
        assert isinstance(loaded, MemoryUnit)
        assert loaded.memory_id == original.memory_id
        assert loaded.content == original.content
    
    def test_load_restores_all_fields(self, storage_with_memory):
        """测试加载恢复所有字段"""
        storage, original = storage_with_memory
        loaded = storage.get(original.memory_id)
        
        assert loaded.memory_type == original.memory_type
        assert loaded.importance == original.importance
        assert loaded.source == original.source
        assert set(loaded.tags) == set(original.tags)
    
    def test_load_restores_embedding(self, storage_with_memory):
        """测试加载恢复向量"""
        storage, original = storage_with_memory
        loaded = storage.get(original.memory_id)
        
        assert loaded.embedding is not None
        assert len(loaded.embedding) == len(original.embedding)
    
    def test_load_not_found_raises_error(self, storage_with_memory):
        """测试加载不存在抛出 MemoryNotFoundError"""
        storage, _ = storage_with_memory
        
        with pytest.raises(MemoryNotFoundError):
            storage.load("nonexistent_id")
    
    def test_load_returns_memory_unit(self, storage_with_memory):
        """测试加载返回 MemoryUnit"""
        storage, original = storage_with_memory
        loaded = storage.load(original.memory_id)
        
        assert isinstance(loaded, MemoryUnit)
        assert loaded.memory_id == original.memory_id
        assert loaded.content == original.content
    
    def test_load_restores_all_fields(self, storage_with_memory):
        """测试加载恢复所有字段"""
        storage, original = storage_with_memory
        loaded = storage.load(original.memory_id)
        
        assert loaded.memory_type == original.memory_type
        assert loaded.importance == original.importance
        assert loaded.source == original.source
        assert set(loaded.tags) == set(original.tags)
    
    def test_load_restores_embedding(self, storage_with_memory):
        """测试加载恢复向量"""
        storage, original = storage_with_memory
        loaded = storage.load(original.memory_id)
        
        assert loaded.embedding is not None
        assert len(loaded.embedding) == len(original.embedding)
    
    def test_load_not_found_raises_error(self, storage_with_memory):
        """测试加载不存在抛出 MemoryNotFoundError"""
        storage, _ = storage_with_memory
        
        with pytest.raises(MemoryNotFoundError):
            storage.load("nonexistent_id")


class TestChromaStorageDelete:
    """测试 delete 方法"""
    
    @pytest.fixture
    def storage_with_memory(self):
        """提供带有一条记忆的临时存储（使用内存模式，唯一集合名）"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        with chroma_storage_context(f"./test_delete_{unique_id}", f"test_delete_{unique_id}", use_memory_mode=True) as storage:
            memory = MemoryUnit(content="测试内容", memory_type="fact", importance=3)
            storage.save(memory)
            yield storage, memory
    
    def test_delete_returns_true_when_exists(self, storage_with_memory):
        """测试删除存在记忆返回 True"""
        storage, memory = storage_with_memory
        result = storage.delete(memory.memory_id)
        assert result is True
    
    def test_delete_removes_memory(self, storage_with_memory):
        """测试删除后记忆不存在"""
        storage, memory = storage_with_memory
        storage.delete(memory.memory_id)
        
        assert not storage.exists(memory.memory_id)
    
    def test_delete_decreases_count(self, storage_with_memory):
        """测试删除后计数减少"""
        storage, memory = storage_with_memory
        count_before = storage.count()
        
        storage.delete(memory.memory_id)
        
        assert storage.count() == count_before - 1
    
    def test_delete_returns_false_when_not_exists(self, storage_with_memory):
        """测试删除不存在返回 False"""
        storage, _ = storage_with_memory
        result = storage.delete("nonexistent_id")
        assert result is False


class TestChromaStorageQuery:
    """测试 query 方法"""
    
    @pytest.fixture
    def storage_with_memories(self):
        """提供带有多条记忆的临时存储（使用内存模式，唯一集合名）"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        with chroma_storage_context(f"./test_query_{unique_id}", f"test_query_{unique_id}", use_memory_mode=True) as storage:
            # 创建不同类型的记忆
            memories = [
                MemoryUnit(content="事实1", memory_type="fact", importance=3, tags=["A"]),
                MemoryUnit(content="事实2", memory_type="fact", importance=4, tags=["B"]),
                MemoryUnit(content="偏好1", memory_type="preference", importance=5, tags=["A", "B"]),
                MemoryUnit(content="任务1", memory_type="task", importance=2, tags=["C"]),
            ]
            
            for memory in memories:
                storage.save(memory)
            
            yield storage, memories
    
    def test_query_by_type(self, storage_with_memories):
        """测试按类型查询"""
        storage, _ = storage_with_memories
        results = storage.query(memory_type="fact")
        
        assert len(results) == 2
        for memory in results:
            assert memory.memory_type == "fact"
    
    def test_query_by_tags(self, storage_with_memories):
        """测试按标签查询"""
        storage, _ = storage_with_memories
        results = storage.query(tags=["A"])
        
        assert len(results) == 2
    
    def test_query_by_min_importance(self, storage_with_memories):
        """测试按最小重要度查询"""
        storage, _ = storage_with_memories
        results = storage.query(min_importance=4)
        
        assert len(results) == 2
    
    def test_query_with_limit(self, storage_with_memories):
        """测试限制返回数量"""
        storage, _ = storage_with_memories
        results = storage.query(limit=2)
        
        assert len(results) <= 2


class TestChromaStorageExistsAndCount:
    """测试 exists 和 count 方法"""
    
    @pytest.fixture
    def storage(self):
        """提供临时存储（使用内存模式，唯一集合名）"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        with chroma_storage_context(f"./test_exists_{unique_id}", f"test_exists_count_{unique_id}", use_memory_mode=True) as storage:
            yield storage
    
    def test_exists_returns_true_for_existing(self, storage):
        """测试 exists 对存在的记忆返回 True"""
        memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
        storage.save(memory)
        
        assert storage.exists(memory.memory_id) is True
    
    def test_exists_returns_false_for_nonexisting(self, storage):
        """测试 exists 对不存在的记忆返回 False"""
        assert storage.exists("nonexistent") is False
    
    def test_count_returns_zero_initially(self, storage):
        """测试初始计数为 0"""
        assert storage.count() == 0
    
    def test_count_increases_after_save(self, storage):
        """测试保存后计数增加"""
        memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
        storage.save(memory)
        
        assert storage.count() == 1


class TestChromaStorageContextManager:
    """测试上下文管理器"""
    
    def test_context_manager_works(self):
        """测试上下文管理器正常工作（使用内存模式）"""
        import uuid
        unique_id = uuid.uuid4().hex[:8]
        with chroma_storage_context(f"./test_context_{unique_id}", f"test_context_{unique_id}", use_memory_mode=True) as storage:
            memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
            storage.save(memory)
            assert storage.count() == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
