"""
JSON 文件存储单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "storage"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

import pytest
import tempfile
import shutil
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "storage"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

from json_storage import JsonStorage
from base_storage import StorageError, MemoryNotFoundError
from memory_unit import MemoryUnit


class TestJsonStorageCreation:
    """测试 JsonStorage 创建"""
    
    def test_create_with_default_path(self):
        """测试使用默认路径创建"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JsonStorage(tmpdir)
            assert storage.storage_name == "json"
            assert storage.storage_dir == Path(tmpdir)
            assert storage.storage_dir.exists()
    
    def test_create_creates_directory(self):
        """测试创建时自动创建目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "new" / "nested" / "dir"
            storage = JsonStorage(str(new_dir))
            assert new_dir.exists()


class TestJsonStorageSave:
    """测试 save 方法"""
    
    @pytest.fixture
    def storage(self):
        """提供临时存储"""
        tmpdir = tempfile.mkdtemp()
        storage = JsonStorage(tmpdir)
        yield storage
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_save_returns_memory_id(self, storage):
        """测试保存返回 memory_id"""
        memory = MemoryUnit(content="测试内容", memory_type="fact", importance=3)
        result = storage.save(memory)
        assert result == memory.memory_id
    
    def test_save_creates_json_file(self, storage):
        """测试保存创建 JSON 文件"""
        memory = MemoryUnit(content="测试内容", memory_type="fact", importance=3)
        storage.save(memory)
        
        file_path = storage._get_file_path(memory.memory_id)
        assert file_path.exists()
        assert file_path.suffix == ".json"
    
    def test_save_file_is_valid_json(self, storage):
        """测试保存的文件是有效 JSON"""
        import json
        
        memory = MemoryUnit(content="测试内容", memory_type="fact", importance=3)
        storage.save(memory)
        
        file_path = storage._get_file_path(memory.memory_id)
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["content"] == "测试内容"
        assert data["memory_type"] == "fact"


class TestJsonStorageLoad:
    """测试 load 方法"""
    
    @pytest.fixture
    def storage_with_memory(self):
        """提供带有一条记忆的临时存储"""
        tmpdir = tempfile.mkdtemp()
        storage = JsonStorage(tmpdir)
        memory = MemoryUnit(
            content="原始内容",
            memory_type="preference",
            importance=4.5,
            tags=["标签1", "标签2"],
            source="test_source"
        )
        storage.save(memory)
        yield storage, memory
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_load_returns_memory_unit(self, storage_with_memory):
        """测试加载返回 MemoryUnit"""
        storage, original = storage_with_memory
        loaded = storage.load(original.memory_id)
        
        assert isinstance(loaded, MemoryUnit)
        assert loaded.memory_id == original.memory_id
        assert loaded.content == original.content
        assert loaded.memory_type == original.memory_type
        assert loaded.importance == original.importance
    
    def test_load_restores_all_fields(self, storage_with_memory):
        """测试加载恢复所有字段"""
        storage, original = storage_with_memory
        loaded = storage.load(original.memory_id)
        
        assert loaded.source == original.source
        assert set(loaded.tags) == set(original.tags)
    
    def test_load_not_found_raises_error(self, storage_with_memory):
        """测试加载不存在抛出 MemoryNotFoundError"""
        storage, _ = storage_with_memory
        
        with pytest.raises(MemoryNotFoundError):
            storage.load("nonexistent_id")


class TestJsonStorageDelete:
    """测试 delete 方法"""
    
    @pytest.fixture
    def storage_with_memory(self):
        """提供带有一条记忆的临时存储"""
        tmpdir = tempfile.mkdtemp()
        storage = JsonStorage(tmpdir)
        memory = MemoryUnit(content="测试内容", memory_type="fact", importance=3)
        storage.save(memory)
        yield storage, memory
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_delete_returns_true_when_exists(self, storage_with_memory):
        """测试删除存在记忆返回 True"""
        storage, memory = storage_with_memory
        result = storage.delete(memory.memory_id)
        assert result is True
    
    def test_delete_removes_file(self, storage_with_memory):
        """测试删除移除文件"""
        storage, memory = storage_with_memory
        file_path = storage._get_file_path(memory.memory_id)
        
        storage.delete(memory.memory_id)
        assert not file_path.exists()
    
    def test_delete_returns_false_when_not_exists(self, storage_with_memory):
        """测试删除不存在返回 False"""
        storage, _ = storage_with_memory
        result = storage.delete("nonexistent_id")
        assert result is False


class TestJsonStorageQuery:
    """测试 query 方法"""
    
    @pytest.fixture
    def storage_with_memories(self):
        """提供带有多条记忆的临时存储"""
        tmpdir = tempfile.mkdtemp()
        storage = JsonStorage(tmpdir)
        
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
        shutil.rmtree(tmpdir, ignore_errors=True)
    
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
        
        assert len(results) == 2  # 事实1 和 偏好1
    
    def test_query_by_min_importance(self, storage_with_memories):
        """测试按最小重要度查询"""
        storage, _ = storage_with_memories
        results = storage.query(min_importance=4)
        
        assert len(results) == 2  # 事实2(importance=4) 和 偏好1(importance=5)
    
    def test_query_with_limit(self, storage_with_memories):
        """测试限制返回数量"""
        storage, _ = storage_with_memories
        results = storage.query(limit=2)
        
        assert len(results) <= 2
    
    def test_query_combined_conditions(self, storage_with_memories):
        """测试组合条件查询"""
        storage, _ = storage_with_memories
        results = storage.query(memory_type="fact", min_importance=4)
        
        assert len(results) == 1  # 只有 事实2
        assert results[0].content == "事实2"


class TestJsonStorageExistsAndCount:
    """测试 exists 和 count 方法"""
    
    @pytest.fixture
    def storage(self):
        """提供临时存储"""
        tmpdir = tempfile.mkdtemp()
        storage = JsonStorage(tmpdir)
        yield storage
        shutil.rmtree(tmpdir, ignore_errors=True)
    
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
    
    def test_count_decreases_after_delete(self, storage):
        """测试删除后计数减少"""
        memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
        storage.save(memory)
        storage.delete(memory.memory_id)
        
        assert storage.count() == 0


class TestJsonStorageContextManager:
    """测试上下文管理器"""
    
    def test_context_manager_works(self):
        """测试上下文管理器正常工作"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with JsonStorage(tmpdir) as storage:
                memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
                storage.save(memory)
                assert storage.count() == 1
            # 退出上下文后存储仍然可用
            assert storage.count() == 1


class TestJsonStorageClearAll:
    """测试 clear_all 方法"""
    
    def test_clear_all_removes_all_files(self):
        """测试清空所有文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JsonStorage(tmpdir)
            
            # 保存多条记忆
            for i in range(5):
                memory = MemoryUnit(content=f"测试{i}", memory_type="fact", importance=3)
                storage.save(memory)
            
            assert storage.count() == 5
            
            # 清空
            storage.clear_all()
            
            assert storage.count() == 0
    
    def test_clear_all_empty_storage(self):
        """测试清空空存储"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JsonStorage(tmpdir)
            
            storage.clear_all()
            
            assert storage.count() == 0


class TestJsonStorageEdgeCases:
    """测试边界情况"""
    
    def test_query_with_corrupted_file(self):
        """测试查询时跳过损坏的文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JsonStorage(tmpdir)
            
            # 保存有效记忆
            memory = MemoryUnit(content="有效内容", memory_type="fact", importance=3)
            storage.save(memory)
            
            # 创建损坏的 JSON 文件
            corrupted_file = storage.storage_dir / "corrupted.json"
            with open(corrupted_file, 'w') as f:
                f.write("这不是有效的 JSON")
            
            # 查询应该跳过损坏文件
            results = storage.query(limit=10)
            assert len(results) == 1  # 只返回有效记忆
    
    def test_load_corrupted_file_raises_error(self):
        """测试加载损坏文件抛出错误"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JsonStorage(tmpdir)
            
            # 创建损坏的 JSON 文件
            corrupted_file = storage.storage_dir / "corrupted.json"
            with open(corrupted_file, 'w') as f:
                f.write("这不是有效的 JSON")
            
            from base_storage import StorageError
            with pytest.raises(StorageError):
                storage.load("corrupted")
    
    def test_save_creates_directory_if_not_exists(self):
        """测试保存时创建目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_dir = Path(tmpdir) / "nested" / "storage"
            storage = JsonStorage(str(nested_dir))
            
            memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
            storage.save(memory)
            
            assert nested_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
