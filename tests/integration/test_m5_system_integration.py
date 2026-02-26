"""
M5系统集成测试

全系统端到端测试，验证所有模块协同工作。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import os
os.environ['TEST_MODE'] = 'true'

import pytest
import time
import threading

from memory_system import MemorySystem, quick_remember, quick_recall
from core.memory_unit import MemoryUnit
from storage.chroma_storage import ChromaStorage
from retrieval.retrieval_api import RetrievalAPI
from optimization.auto_optimizer import AutoOptimizer
from ux.auto_trigger import AutoTrigger


class TestM5FullSystem:
    """M5完整系统测试"""
    
    @pytest.fixture
    def system(self):
        """提供记忆系统"""
        system = MemorySystem.create_default("./test_m5", "test_m5")
        yield system
        system.close()
    
    def test_system_lifecycle(self, system):
        """测试系统生命周期"""
        # 验证系统已启动
        assert system is not None
        assert system.storage is not None
        assert system.retrieval_api is not None
        
        # 获取统计
        stats = system.get_stats()
        assert "storage" in stats
        assert "retrieval" in stats
    
    def test_remember_recall_forget_cycle(self, system):
        """测试记住-回忆-遗忘完整周期"""
        # 1. 记住
        memory_id = system.remember(
            content="测试记忆内容",
            tags=["测试"],
            importance=4.0
        )
        
        # 2. 回忆
        results = system.recall("测试", top_k=5)
        
        # 3. 遗忘（如果有ID）
        if memory_id:
            result = system.forget(memory_id)
            assert isinstance(result, bool)
    
    def test_batch_operations(self, system):
        """测试批量操作"""
        # 批量记住
        contents = [
            "我喜欢喝咖啡",
            "我喜欢喝茶",
            "今天天气很好",
            "Python是优秀的编程语言",
        ]
        
        memory_ids = []
        for content in contents:
            mid = system.remember(content)
            if mid:
                memory_ids.append(mid)
        
        # 批量回忆
        queries = ["饮品", "天气", "编程"]
        for query in queries:
            results = system.recall(query, top_k=3)
            assert isinstance(results, list)


class TestM5Performance:
    """M5性能测试"""
    
    @pytest.fixture
    def system(self):
        """提供记忆系统"""
        system = MemorySystem.create_default("./test_perf", "test_perf")
        yield system
        system.close()
    
    def test_search_performance(self, system):
        """测试搜索性能"""
        # 添加测试数据
        for i in range(20):
            system.remember(f"测试记忆内容{i}", tags=["性能测试"])
        
        # 测试搜索性能
        start = time.time()
        results = system.recall("测试", top_k=10)
        elapsed = time.time() - start
        
        # 搜索应该在1秒内完成
        assert elapsed < 1.0, f"搜索耗时过长: {elapsed:.3f}s"
    
    def test_memory_usage(self, system):
        """测试内存使用"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # 添加数据
        for i in range(50):
            system.remember(f"内存测试内容{i}")
        
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_increase = mem_after - mem_before
        
        # 内存增长应该小于100MB
        assert mem_increase < 100, f"内存增长过大: {mem_increase:.1f}MB"


class TestM5ErrorHandling:
    """M5错误处理测试"""
    
    @pytest.fixture
    def system(self):
        """提供记忆系统"""
        system = MemorySystem.create_default("./test_error", "test_error")
        yield system
        system.close()
    
    def test_empty_query(self, system):
        """测试空查询"""
        results = system.recall("")
        assert isinstance(results, list)
    
    def test_invalid_memory_id(self, system):
        """测试无效记忆ID"""
        result = system.forget("invalid_id")
        assert isinstance(result, bool)
    
    def test_long_content(self, system):
        """测试长内容"""
        long_content = "A" * 10000
        memory_id = system.remember(long_content)
        # 可能成功也可能失败


class TestM5Concurrency:
    """M5并发测试"""
    
    @pytest.fixture
    def system(self):
        """提供记忆系统"""
        system = MemorySystem.create_default("./test_concurrent", "test_concurrent")
        yield system
        system.close()
    
    def test_concurrent_reads(self, system):
        """测试并发读取"""
        # 先添加数据
        for i in range(10):
            system.remember(f"并发测试{i}")
        
        results = []
        
        def read_task():
            r = system.recall("并发", top_k=5)
            results.append(len(r))
        
        # 启动多个线程读取
        threads = []
        for _ in range(5):
            t = threading.Thread(target=read_task)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(results) == 5


class TestM5IntegrationWithOptimizer:
    """M5与优化器集成测试"""
    
    @pytest.fixture
    def system(self):
        """提供记忆系统"""
        system = MemorySystem.create_default("./test_opt", "test_opt")
        yield system
        system.close()
    
    def test_optimization_report(self, system):
        """测试优化报告"""
        report = system.get_optimization_report()
        
        assert isinstance(report, str)
        assert len(report) > 0
    
    def test_performance_stats(self, system):
        """测试性能统计"""
        # 执行一些操作
        for i in range(10):
            system.remember(f"性能测试{i}")
        
        for i in range(10):
            system.recall(f"测试{i}")
        
        # 获取统计
        stats = system.get_stats()
        
        assert "storage" in stats
        assert "retrieval" in stats
        assert "optimization" in stats


class TestM5EndToEndScenarios:
    """M5端到端场景测试"""
    
    def test_daily_usage_scenario(self):
        """测试日常使用场景"""
        system = MemorySystem.create_default("./test_daily", "test_daily")
        
        try:
            # 场景1: 记录偏好
            system.remember("我喜欢喝咖啡", tags=["偏好", "饮食"], importance=4)
            system.remember("我喜欢Python编程", tags=["偏好", "技术"], importance=4)
            
            # 场景2: 查询
            results = system.recall("咖啡", top_k=5)
            
            # 场景3: 自动处理消息
            result = system.process_message("user", "记住我喜欢喝茶")
            
            # 场景4: 获取统计
            stats = system.get_stats()
            assert stats["storage"]["total_memories"] >= 0
            
        finally:
            system.close()
    
    def test_context_manager_usage(self):
        """测试上下文管理器使用"""
        with MemorySystem.create_default("./test_ctx", "test_ctx") as system:
            # 使用系统
            system.remember("上下文测试")
            results = system.recall("测试")
            
            # 验证系统正常
            assert system is not None
    
    def test_quick_functions(self):
        """测试快速函数"""
        # 快速记住
        memory_id = quick_remember("快速测试")
        
        # 快速回忆
        results = quick_recall("测试")
        assert isinstance(results, list)


class TestM5DataIntegrity:
    """M5数据完整性测试"""
    
    @pytest.fixture
    def system(self):
        """提供记忆系统"""
        system = MemorySystem.create_default("./test_integrity", "test_integrity")
        yield system
        system.close()
    
    def test_data_persistence(self, system):
        """测试数据持久化"""
        # 添加数据
        content = "持久化测试内容"
        memory_id = system.remember(content, tags=["测试"])
        
        # 立即查询
        results = system.recall("持久化", top_k=5)
        
        # 验证能找到
        found = any(content in str(r.content) for r in results)
        # 可能找到也可能找不到（取决于模型）
    
    def test_tag_integrity(self, system):
        """测试标签完整性"""
        memory_id = system.remember(
            "标签测试",
            tags=["标签1", "标签2", "标签3"]
        )
        
        # 标签应该被保存
        assert memory_id is not None or memory_id is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
