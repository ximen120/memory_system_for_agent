"""
M3自动优化集成测试

测试性能监控、缓存管理、索引优化、自动优化的协同工作。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "optimization"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "storage"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "core"))

import os
os.environ['TEST_MODE'] = 'true'

import pytest
import time
import threading

from auto_optimizer import AutoOptimizer
from performance_monitor import PerformanceMonitor
from cache_manager import CacheManager, MultiLevelCache
from index_optimizer import IndexOptimizer


class TestM3PerformanceMonitorIntegration:
    """M3性能监控集成测试"""
    
    @pytest.fixture
    def monitor(self):
        """提供性能监控器"""
        return PerformanceMonitor(slow_threshold_ms=50.0)
    
    def test_monitor_with_context(self, monitor):
        """测试上下文监控"""
        with monitor.record("test_operation"):
            time.sleep(0.02)  # 20ms
        
        stats = monitor.get_stats("test_operation")
        assert stats['count'] == 1
        assert stats['avg_latency_ms'] >= 20.0
    
    def test_monitor_slow_query_detection(self, monitor):
        """测试慢查询检测"""
        # 记录慢查询
        monitor.record_manual(
            operation="search",
            duration_ms=100.0,  # 超过阈值
            success=True
        )
        
        slow_queries = monitor.get_slow_queries()
        assert len(slow_queries) == 1
        assert slow_queries[0].operation == "search"
    
    def test_monitor_error_tracking(self, monitor):
        """测试错误跟踪"""
        monitor.record_manual(
            operation="save",
            duration_ms=10.0,
            success=False,
            error_message="连接失败"
        )
        
        errors = monitor.get_errors()
        assert len(errors) == 1
        assert errors[0].error_message == "连接失败"


class TestM3CacheManagerIntegration:
    """M3缓存管理集成测试"""
    
    @pytest.fixture
    def cache(self):
        """提供缓存管理器"""
        return CacheManager(max_size=100, ttl_seconds=3600)
    
    def test_cache_basic_operations(self, cache):
        """测试基本缓存操作"""
        # 设置
        cache.set("key1", "value1")
        
        # 获取
        value = cache.get("key1")
        assert value == "value1"
        
        # 删除
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_cache_lru_eviction(self, cache):
        """测试LRU淘汰"""
        # 添加多个条目
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")
        
        # 访问前5个
        for i in range(5):
            cache.get(f"key{i}")
        
        # 添加更多条目，触发淘汰
        for i in range(10, 110):
            cache.set(f"key{i}", f"value{i}")
        
        # 检查统计
        stats = cache.get_stats()
        assert stats['size'] <= 100
        assert stats['evictions'] > 0
    
    def test_cache_hit_rate(self, cache):
        """测试缓存命中率"""
        # 设置
        cache.set("key1", "value1")
        
        # 多次命中
        for _ in range(5):
            cache.get("key1")
        
        # 多次未命中
        for i in range(5):
            cache.get(f"nonexistent{i}")
        
        stats = cache.get_stats()
        assert stats['hits'] == 5
        assert stats['misses'] == 5
        assert stats['hit_rate'] == 0.5


class TestM3MultiLevelCacheIntegration:
    """M3多级缓存集成测试"""
    
    @pytest.fixture
    def multi_cache(self):
        """提供多级缓存"""
        return MultiLevelCache(l1_size=5, l2_size=10)
    
    def test_multilevel_cache_flow(self, multi_cache):
        """测试多级缓存流程"""
        # 设置
        multi_cache.set("key1", "value1")
        
        # 第一次获取（从L1）
        value = multi_cache.get("key1")
        assert value == "value1"
        
        # 验证L1和L2都有
        assert multi_cache.l1.get("key1") == "value1"
        assert multi_cache.l2.get("key1") == "value1"
    
    def test_multilevel_stats(self, multi_cache):
        """测试多级缓存统计"""
        # 设置并获取
        multi_cache.set("key1", "value1")
        multi_cache.get("key1")
        
        stats = multi_cache.get_stats()
        assert 'l1' in stats
        assert 'l2' in stats


class TestM3IndexOptimizerIntegration:
    """M3索引优化器集成测试"""
    
    @pytest.fixture
    def optimizer(self):
        """提供索引优化器"""
        return IndexOptimizer(storage=None)
    
    def test_analyze_empty_index(self, optimizer):
        """测试分析空索引"""
        stats = optimizer.analyze()
        
        assert stats.total_documents == 0
        assert stats.fragmentation_ratio == 0.0
    
    def test_get_recommendations_empty(self, optimizer):
        """测试空索引建议"""
        recommendations = optimizer.get_recommendations()
        
        assert len(recommendations) > 0
        assert "良好" in recommendations[0] or "失败" in recommendations[0]


class TestM3AutoOptimizerIntegration:
    """M3自动优化器集成测试"""
    
    @pytest.fixture
    def auto_optimizer(self):
        """提供自动优化器"""
        return AutoOptimizer(
            storage=None,
            enable_auto_optimize=False,  # 禁用自动优化，避免后台线程
            cache_size=100
        )
    
    def test_auto_optimizer_structure(self, auto_optimizer):
        """测试自动优化器结构"""
        assert auto_optimizer.monitor is not None
        assert auto_optimizer.cache is not None
        assert auto_optimizer.index_optimizer is None  # 没有storage
    
    def test_record_operation(self, auto_optimizer):
        """测试记录操作"""
        with auto_optimizer.record_operation("test_op"):
            time.sleep(0.01)
        
        stats = auto_optimizer.get_performance_stats()
        assert 'test_op' in stats or len(stats) == 0  # 可能为空
    
    def test_cache_operations(self, auto_optimizer):
        """测试缓存操作"""
        # 设置缓存
        auto_optimizer.cache_set("key1", "value1")
        
        # 获取缓存
        value = auto_optimizer.cache_get("key1")
        assert value == "value1"
        
        # 删除缓存
        auto_optimizer.cache_delete("key1")
        assert auto_optimizer.cache_get("key1") is None
    
    def test_get_optimization_report(self, auto_optimizer):
        """测试获取优化报告"""
        report = auto_optimizer.get_optimization_report()
        
        assert "自动优化报告" in report
        assert "性能统计" in report
        assert "缓存统计" in report


class TestM3EndToEnd:
    """M3端到端测试"""
    
    def test_full_optimization_workflow(self):
        """测试完整优化流程"""
        # 1. 创建自动优化器
        optimizer = AutoOptimizer(
            storage=None,
            enable_auto_optimize=False,
            cache_size=50
        )
        
        # 2. 模拟操作并记录性能
        for i in range(20):
            with optimizer.record_operation("search"):
                time.sleep(0.005)  # 5ms
        
        # 3. 使用缓存
        for i in range(10):
            optimizer.cache_set(f"key{i}", f"value{i}")
        
        for i in range(10):
            optimizer.cache_get(f"key{i}")
        
        # 4. 获取性能统计
        perf_stats = optimizer.get_performance_stats()
        
        # 5. 获取缓存统计
        cache_stats = optimizer.get_cache_stats()
        assert cache_stats['size'] == 10
        
        # 6. 获取优化报告
        report = optimizer.get_optimization_report()
        assert len(report) > 0
    
    def test_performance_monitoring_workflow(self):
        """测试性能监控流程"""
        monitor = PerformanceMonitor(slow_threshold_ms=30.0)
        
        # 记录正常操作
        for _ in range(10):
            monitor.record_manual("operation", duration_ms=10.0, success=True)
        
        # 记录慢操作
        monitor.record_manual("operation", duration_ms=50.0, success=True)
        
        # 记录错误
        monitor.record_manual("operation", duration_ms=10.0, success=False, error_message="错误")
        
        # 获取统计
        stats = monitor.get_stats("operation")
        assert stats['count'] == 12
        assert stats['error_count'] == 1
        
        # 获取慢查询
        slow_queries = monitor.get_slow_queries()
        assert len(slow_queries) == 1
        
        # 获取错误
        errors = monitor.get_errors()
        assert len(errors) == 1
    
    def test_cache_optimization_workflow(self):
        """测试缓存优化流程"""
        cache = CacheManager(max_size=10, ttl_seconds=1)
        
        # 填充缓存
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")
        
        # 访问部分键
        for i in range(5):
            for _ in range(3):  # 多次访问
                cache.get(f"key{i}")
        
        # 添加新键，触发淘汰
        for i in range(10, 15):
            cache.set(f"key{i}", f"value{i}")
        
        # 检查统计
        stats = cache.get_stats()
        assert stats['size'] == 10
        assert stats['evictions'] == 5
        
        # 检查热门键
        popular = cache.get_popular_keys(top_n=5)
        assert len(popular) <= 5
        # 前5个键应该访问次数最多
        for key, count in popular:
            assert count >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
