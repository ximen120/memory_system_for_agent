"""
性能监控器单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "optimization"))

import pytest
import time
from performance_monitor import PerformanceMonitor, PerformanceMetrics


class TestPerformanceMonitorCreation:
    """测试性能监控器创建"""
    
    def test_create_default(self):
        """测试默认创建"""
        monitor = PerformanceMonitor()
        
        assert monitor.max_history == 1000
        assert monitor.slow_threshold_ms == 100.0
    
    def test_create_with_custom_params(self):
        """测试自定义参数创建"""
        monitor = PerformanceMonitor(
            max_history=500,
            slow_threshold_ms=50.0
        )
        
        assert monitor.max_history == 500
        assert monitor.slow_threshold_ms == 50.0


class TestPerformanceMonitorRecording:
    """测试性能记录"""
    
    @pytest.fixture
    def monitor(self):
        """提供监控器实例"""
        return PerformanceMonitor()
    
    def test_record_manual(self, monitor):
        """测试手动记录"""
        monitor.record_manual(
            operation="search",
            duration_ms=50.0,
            success=True
        )
        
        stats = monitor.get_stats("search")
        assert stats['count'] == 1
        assert stats['avg_latency_ms'] == 50.0
    
    def test_record_multiple(self, monitor):
        """测试记录多个操作"""
        for i in range(10):
            monitor.record_manual(
                operation="search",
                duration_ms=float(i * 10),
                success=True
            )
        
        stats = monitor.get_stats("search")
        assert stats['count'] == 10
    
    def test_record_with_context(self, monitor):
        """测试上下文记录"""
        with monitor.record("test_operation"):
            time.sleep(0.01)  # 10ms
        
        stats = monitor.get_stats("test_operation")
        assert stats['count'] == 1
        assert stats['avg_latency_ms'] >= 10.0


class TestPerformanceMonitorStats:
    """测试性能统计"""
    
    @pytest.fixture
    def monitor_with_data(self):
        """提供带数据的监控器"""
        monitor = PerformanceMonitor()
        
        # 添加测试数据
        for i in range(10):
            monitor.record_manual(
                operation="search",
                duration_ms=float(i * 10),
                success=i < 8  # 2个错误
            )
        
        return monitor
    
    def test_get_stats(self, monitor_with_data):
        """测试获取统计"""
        stats = monitor_with_data.get_stats("search")
        
        assert stats['count'] == 10
        assert stats['error_count'] == 2
        assert stats['error_rate'] == 0.2
        assert 'avg_latency_ms' in stats
        assert 'p95_latency_ms' in stats
    
    def test_get_all_stats(self, monitor_with_data):
        """测试获取所有统计"""
        all_stats = monitor_with_data.get_stats()
        
        assert 'search' in all_stats


class TestPerformanceMonitorSlowQueries:
    """测试慢查询检测"""
    
    @pytest.fixture
    def monitor(self):
        """提供监控器实例"""
        return PerformanceMonitor(slow_threshold_ms=50.0)
    
    def test_detect_slow_query(self, monitor):
        """测试检测慢查询"""
        monitor.record_manual(
            operation="search",
            duration_ms=100.0,  # 超过阈值
            success=True
        )
        
        slow_queries = monitor.get_slow_queries()
        assert len(slow_queries) == 1
        assert slow_queries[0].operation == "search"
    
    def test_no_slow_query(self, monitor):
        """测试正常查询不被标记"""
        monitor.record_manual(
            operation="search",
            duration_ms=10.0,  # 低于阈值
            success=True
        )
        
        slow_queries = monitor.get_slow_queries()
        assert len(slow_queries) == 0


class TestPerformanceMonitorErrors:
    """测试错误记录"""
    
    @pytest.fixture
    def monitor(self):
        """提供监控器实例"""
        return PerformanceMonitor()
    
    def test_record_error(self, monitor):
        """测试记录错误"""
        monitor.record_manual(
            operation="search",
            duration_ms=10.0,
            success=False,
            error_message="连接超时"
        )
        
        errors = monitor.get_errors()
        assert len(errors) == 1
        assert errors[0].error_message == "连接超时"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
