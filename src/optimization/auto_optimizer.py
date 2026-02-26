"""
自动优化器

自动监控和优化记忆系统性能。
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta

try:
    from .performance_monitor import PerformanceMonitor
    from .index_optimizer import IndexOptimizer
    from .cache_manager import CacheManager
except ImportError:
    from performance_monitor import PerformanceMonitor
    from index_optimizer import IndexOptimizer
    from cache_manager import CacheManager

logger = logging.getLogger(__name__)


class AutoOptimizer:
    """
    自动优化器
    
    自动监控记忆系统性能，执行优化策略：
    - 性能监控
    - 自动调参
    - 索引优化
    - 缓存管理
    
    使用示例：
        >>> optimizer = AutoOptimizer(storage)
        >>> optimizer.start()
        >>> 
        >>> # 运行一段时间后
        >>> report = optimizer.get_optimization_report()
        >>> print(report)
    """
    
    def __init__(
        self,
        storage=None,
        enable_monitoring: bool = True,
        enable_auto_optimize: bool = True,
        optimize_interval_minutes: int = 60,
        slow_query_threshold_ms: float = 100.0,
        cache_size: int = 1000
    ):
        """
        初始化自动优化器
        
        Args:
            storage: 存储后端
            enable_monitoring: 启用监控
            enable_auto_optimize: 启用自动优化
            optimize_interval_minutes: 优化间隔（分钟）
            slow_query_threshold_ms: 慢查询阈值
            cache_size: 缓存大小
        """
        self.storage = storage
        self.enable_monitoring = enable_monitoring
        self.enable_auto_optimize = enable_auto_optimize
        self.optimize_interval = timedelta(minutes=optimize_interval_minutes)
        
        # 初始化组件
        self.monitor = PerformanceMonitor(
            slow_threshold_ms=slow_query_threshold_ms,
            alert_callback=self._on_performance_alert
        ) if enable_monitoring else None
        
        self.index_optimizer = IndexOptimizer(storage) if storage else None
        self.cache = CacheManager(max_size=cache_size) if cache_size > 0 else None
        
        # 运行状态
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_optimize_time: Optional[datetime] = None
        self._optimization_count = 0
        
        logger.info("自动优化器初始化完成")
    
    def start(self):
        """启动自动优化器"""
        if self._running:
            logger.warning("自动优化器已在运行")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
        logger.info("自动优化器已启动")
    
    def stop(self):
        """停止自动优化器"""
        self._running = False
        
        if self._thread:
            self._thread.join(timeout=5.0)
        
        logger.info("自动优化器已停止")
    
    def _run_loop(self):
        """运行循环"""
        while self._running:
            try:
                # 检查是否需要优化
                if self.enable_auto_optimize:
                    self._check_and_optimize()
                
                # 清理过期缓存
                if self.cache:
                    self.cache.cleanup_expired()
                
                # 休眠1分钟
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"自动优化循环出错: {e}")
                time.sleep(60)
    
    def _check_and_optimize(self):
        """检查并执行优化"""
        now = datetime.now()
        
        # 检查优化间隔
        if self._last_optimize_time:
            if now - self._last_optimize_time < self.optimize_interval:
                return
        
        logger.info("开始自动优化...")
        
        try:
            # 1. 索引优化
            if self.index_optimizer:
                result = self.index_optimizer.optimize()
                if result['optimized']:
                    logger.info(f"索引优化完成: {result}")
            
            # 2. 缓存预热（根据热门数据）
            if self.cache:
                popular_keys = self.cache.get_popular_keys(top_n=100)
                logger.info(f"缓存统计: {len(popular_keys)} 热门键")
            
            self._last_optimize_time = now
            self._optimization_count += 1
            
            logger.info("自动优化完成")
            
        except Exception as e:
            logger.error(f"自动优化失败: {e}")
    
    def _on_performance_alert(self, alert_type: str, metric):
        """性能告警回调"""
        if alert_type == "slow_query":
            logger.warning(f"慢查询告警: {metric.operation} took {metric.duration_ms:.2f}ms")
            
            # 可以触发自动调优
            if self.enable_auto_optimize:
                self._auto_tune(metric)
        
        elif alert_type == "error":
            logger.error(f"错误告警: {metric.operation} failed - {metric.error_message}")
    
    def _auto_tune(self, metric):
        """自动调优"""
        logger.info(f"自动调优: {metric.operation}")
        
        # 根据性能指标调整参数
        if metric.operation == "search" and metric.duration_ms > 200:
            # 搜索太慢，可能需要优化索引
            if self.index_optimizer:
                logger.info("触发索引优化")
                self.index_optimizer.optimize()
    
    def record_operation(self, operation: str, metadata: Optional[Dict] = None):
        """
        记录操作（用于监控）
        
        Args:
            operation: 操作名称
            metadata: 元数据
        """
        if self.monitor:
            return self.monitor.record(operation, metadata)
        return None
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if not self.monitor:
            return {}
        
        return self.monitor.get_stats()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        if not self.cache:
            return {}
        
        return self.cache.get_stats()
    
    def get_optimization_report(self) -> str:
        """
        获取优化报告
        
        Returns:
            格式化的报告字符串
        """
        lines = ["=" * 50]
        lines.append("自动优化报告")
        lines.append("=" * 50)
        lines.append(f"生成时间: {datetime.now().isoformat()}")
        lines.append(f"优化次数: {self._optimization_count}")
        lines.append("")
        
        # 性能统计
        if self.monitor:
            lines.append("性能统计:")
            lines.append(self.monitor.get_summary())
            lines.append("")
        
        # 缓存统计
        if self.cache:
            cache_stats = self.cache.get_stats()
            lines.append("缓存统计:")
            lines.append(f"  大小: {cache_stats['size']}/{cache_stats['max_size']}")
            lines.append(f"  命中率: {cache_stats['hit_rate']:.2%}")
            lines.append(f"  内存: {cache_stats['memory_bytes'] / 1024 / 1024:.2f}MB")
            lines.append("")
        
        # 索引建议
        if self.index_optimizer:
            lines.append("索引优化建议:")
            for rec in self.index_optimizer.get_recommendations():
                lines.append(f"  - {rec}")
            lines.append("")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def cache_get(self, key: str) -> Optional[Any]:
        """从缓存获取"""
        if self.cache:
            return self.cache.get(key)
        return None
    
    def cache_set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """设置缓存"""
        if self.cache:
            self.cache.set(key, value, ttl_seconds)
    
    def cache_delete(self, key: str):
        """删除缓存"""
        if self.cache:
            self.cache.delete(key)


if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("自动优化器测试")
    print("=" * 50)
    
    optimizer = AutoOptimizer(enable_auto_optimize=False)
    
    # 模拟操作
    import random
    
    for i in range(50):
        operation = random.choice(["search", "save", "delete"])
        
        with optimizer.record_operation(operation):
            # 模拟操作耗时
            time.sleep(random.uniform(0.001, 0.1))
    
    # 打印报告
    print("\n" + optimizer.get_optimization_report())
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
