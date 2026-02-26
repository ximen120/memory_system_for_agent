"""
自动优化模块 (M3)

提供记忆系统的自动优化功能：
- 性能监控
- 索引优化
- 缓存管理
- 自动调参
"""

from .performance_monitor import PerformanceMonitor, PerformanceMetrics
from .index_optimizer import IndexOptimizer
from .cache_manager import CacheManager
from .auto_optimizer import AutoOptimizer

__all__ = [
    'PerformanceMonitor',
    'PerformanceMetrics',
    'IndexOptimizer',
    'CacheManager',
    'AutoOptimizer'
]
