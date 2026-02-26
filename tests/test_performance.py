"""
性能基准测试

测试系统性能是否达到基准要求。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "storage"))

import pytest
import tempfile
import shutil
import time
from memory_manager import MemoryManager
from memory_unit import MemoryUnit
from json_storage import JsonStorage


class TestPerformanceBenchmarks:
    """性能基准测试"""
    
    # 性能基准
    SAVE_MAX_MS = 100
    QUERY_MAX_MS = 500
    LOAD_MAX_MS = 50
    
    @pytest.fixture
    def manager(self):
        """提供临时管理器"""
        tmpdir = tempfile.mkdtemp()
        manager = MemoryManager(data_dir=tmpdir)
        yield manager
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_save_performance(self, manager):
        """测试保存性能 < 100ms"""
        memory = MemoryUnit(
            content="测试保存性能",
            memory_type="fact",
            importance=3.0
        )
        
        start = time.time()
        manager.save(memory)
        elapsed_ms = (time.time() - start) * 1000
        
        print(f"\n保存耗时: {elapsed_ms:.2f}ms")
        assert elapsed_ms < self.SAVE_MAX_MS, f"保存太慢: {elapsed_ms:.2f}ms > {self.SAVE_MAX_MS}ms"
    
    def test_load_performance(self, manager):
        """测试加载性能 < 50ms"""
        # 先保存一条
        memory = MemoryUnit(
            content="测试加载性能",
            memory_type="fact",
            importance=3.0
        )
        memory_id = manager.save(memory)
        
        # 测试加载
        start = time.time()
        manager.load(memory_id)
        elapsed_ms = (time.time() - start) * 1000
        
        print(f"\n加载耗时: {elapsed_ms:.2f}ms")
        assert elapsed_ms < self.LOAD_MAX_MS, f"加载太慢: {elapsed_ms:.2f}ms > {self.LOAD_MAX_MS}ms"
    
    def test_query_performance_with_100_memories(self, manager):
        """测试100条记忆的查询性能 < 500ms"""
        # 准备100条记忆
        for i in range(100):
            memory = MemoryUnit(
                content=f"测试内容{i}",
                memory_type="fact" if i % 2 == 0 else "preference",
                importance=3.0,
                tags=[f"标签{i % 10}"]
            )
            manager.save(memory)
        
        # 测试查询
        start = time.time()
        results = manager.query(memory_type="fact", limit=10)
        elapsed_ms = (time.time() - start) * 1000
        
        print(f"\n查询100条记忆耗时: {elapsed_ms:.2f}ms, 返回{len(results)}条")
        assert elapsed_ms < self.QUERY_MAX_MS, f"查询太慢: {elapsed_ms:.2f}ms > {self.QUERY_MAX_MS}ms"
    
    def test_batch_save_performance(self, manager):
        """测试批量保存性能"""
        memories = []
        for i in range(50):
            memory = MemoryUnit(
                content=f"批量测试{i}",
                memory_type="fact",
                importance=3.0
            )
            memories.append(memory)
        
        start = time.time()
        for memory in memories:
            manager.save(memory)
        elapsed_ms = (time.time() - start) * 1000
        
        avg_ms = elapsed_ms / len(memories)
        print(f"\n批量保存50条: 总耗时{elapsed_ms:.2f}ms, 平均{avg_ms:.2f}ms/条")
        
        # 平均每条应该 < 100ms
        assert avg_ms < self.SAVE_MAX_MS


class TestScalability:
    """可扩展性测试"""
    
    def test_storage_with_1000_memories(self):
        """测试存储1000条记忆"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MemoryManager(data_dir=tmpdir)
            
            # 保存1000条
            start = time.time()
            for i in range(1000):
                memory = MemoryUnit(
                    content=f"大规模测试内容{i}",
                    memory_type="fact" if i % 3 == 0 else "preference",
                    importance=3.0 + (i % 3),
                    tags=[f"标签{i % 20}"]
                )
                manager.save(memory)
            
            save_time = time.time() - start
            
            # 验证数量
            stats = manager.get_stats()
            assert stats["total_memories"] == 1000
            
            # 查询测试
            start = time.time()
            results = manager.query(limit=100)
            query_time = time.time() - start
            
            print(f"\n1000条记忆:")
            print(f"  保存耗时: {save_time:.2f}s ({save_time/1000*1000:.2f}ms/条)")
            print(f"  查询耗时: {query_time*1000:.2f}ms")
            
            manager.close()
    
    def test_json_storage_file_count(self):
        """测试 JSON 存储文件数量"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = JsonStorage(tmpdir)
            
            # 保存100条
            for i in range(100):
                memory = MemoryUnit(
                    content=f"文件测试{i}",
                    memory_type="fact",
                    importance=3.0
                )
                storage.save(memory)
            
            # 检查文件数量
            json_files = list(Path(tmpdir).glob("*.json"))
            assert len(json_files) == 100
            
            storage.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
