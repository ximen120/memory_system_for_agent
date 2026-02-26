"""
性能监控器

监控记忆系统的性能指标，提供统计分析和告警功能。
"""

import time
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from statistics import mean, median, stdev

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    operation: str                    # 操作名称
    duration_ms: float               # 执行时间（毫秒）
    timestamp: datetime              # 时间戳
    success: bool                    # 是否成功
    error_message: Optional[str]     # 错误信息
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """
    性能监控器
    
    监控记忆系统的性能指标，包括：
    - 检索延迟
    - 存储操作时间
    - 命中率
    - 错误率
    
    使用示例：
        >>> monitor = PerformanceMonitor()
        >>> 
        >>> # 记录操作
        >>> with monitor.record("search"):
        ...     results = vector_search.search("查询")
        >>> 
        >>> # 获取统计
        >>> stats = monitor.get_stats("search")
        >>> print(f"平均延迟: {stats['avg_latency_ms']:.2f}ms")
    """
    
    def __init__(
        self,
        max_history: int = 1000,
        slow_threshold_ms: float = 100.0,
        alert_callback: Optional[Callable] = None
    ):
        """
        初始化性能监控器
        
        Args:
            max_history: 最大历史记录数
            slow_threshold_ms: 慢查询阈值（毫秒）
            alert_callback: 告警回调函数
        """
        self.max_history = max_history
        self.slow_threshold_ms = slow_threshold_ms
        self.alert_callback = alert_callback
        
        # 存储历史记录
        self._metrics: Dict[str, deque] = {}
        self._slow_queries: deque = deque(maxlen=100)
        self._errors: deque = deque(maxlen=100)
        
        logger.info(f"性能监控器初始化: max_history={max_history}")
    
    def record(
        self,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        上下文管理器，用于记录操作性能
        
        Args:
            operation: 操作名称
            metadata: 额外元数据
            
        Returns:
            PerformanceContext: 上下文对象
        """
        return PerformanceContext(self, operation, metadata)
    
    def record_manual(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        手动记录性能指标
        
        Args:
            operation: 操作名称
            duration_ms: 执行时间（毫秒）
            success: 是否成功
            error_message: 错误信息
            metadata: 额外元数据
        """
        metric = PerformanceMetrics(
            operation=operation,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )
        
        # 存储到对应操作的历史记录
        if operation not in self._metrics:
            self._metrics[operation] = deque(maxlen=self.max_history)
        self._metrics[operation].append(metric)
        
        # 记录慢查询
        if duration_ms > self.slow_threshold_ms:
            self._slow_queries.append(metric)
            logger.warning(f"慢查询 detected: {operation} took {duration_ms:.2f}ms")
            
            # 触发告警
            if self.alert_callback:
                self.alert_callback("slow_query", metric)
        
        # 记录错误
        if not success:
            self._errors.append(metric)
            logger.error(f"操作失败: {operation} - {error_message}")
            
            if self.alert_callback:
                self.alert_callback("error", metric)
    
    def get_stats(
        self,
        operation: Optional[str] = None,
        time_window_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取性能统计
        
        Args:
            operation: 操作名称，None返回所有操作统计
            time_window_minutes: 时间窗口（分钟），None表示全部
            
        Returns:
            统计信息字典
        """
        if operation:
            return self._get_operation_stats(operation, time_window_minutes)
        else:
            # 返回所有操作的统计
            all_stats = {}
            for op in self._metrics.keys():
                all_stats[op] = self._get_operation_stats(op, time_window_minutes)
            return all_stats
    
    def _get_operation_stats(
        self,
        operation: str,
        time_window_minutes: Optional[int] = None
    ) -> Dict[str, Any]:
        """获取单个操作的统计"""
        if operation not in self._metrics:
            return {
                'operation': operation,
                'count': 0,
                'error_count': 0,
                'error_rate': 0.0
            }
        
        metrics = self._metrics[operation]
        
        # 时间过滤
        if time_window_minutes:
            cutoff = datetime.now() - timedelta(minutes=time_window_minutes)
            metrics = [m for m in metrics if m.timestamp > cutoff]
        
        if not metrics:
            return {
                'operation': operation,
                'count': 0,
                'error_count': 0,
                'error_rate': 0.0
            }
        
        # 计算统计
        durations = [m.duration_ms for m in metrics]
        errors = [m for m in metrics if not m.success]
        
        stats = {
            'operation': operation,
            'count': len(metrics),
            'error_count': len(errors),
            'error_rate': len(errors) / len(metrics),
            'avg_latency_ms': mean(durations),
            'median_latency_ms': median(durations),
            'min_latency_ms': min(durations),
            'max_latency_ms': max(durations),
            'p95_latency_ms': self._percentile(durations, 95),
            'p99_latency_ms': self._percentile(durations, 99),
        }
        
        # 计算标准差（需要至少2个数据点）
        if len(durations) >= 2:
            stats['std_latency_ms'] = stdev(durations)
        else:
            stats['std_latency_ms'] = 0.0
        
        return stats
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def get_slow_queries(
        self,
        limit: int = 10,
        operation: Optional[str] = None
    ) -> List[PerformanceMetrics]:
        """
        获取慢查询列表
        
        Args:
            limit: 返回数量
            operation: 操作名称过滤
            
        Returns:
            慢查询列表
        """
        queries = list(self._slow_queries)
        
        if operation:
            queries = [q for q in queries if q.operation == operation]
        
        # 按时间倒序
        queries.sort(key=lambda x: x.timestamp, reverse=True)
        
        return queries[:limit]
    
    def get_errors(
        self,
        limit: int = 10,
        operation: Optional[str] = None
    ) -> List[PerformanceMetrics]:
        """
        获取错误列表
        
        Args:
            limit: 返回数量
            operation: 操作名称过滤
            
        Returns:
            错误列表
        """
        errors = list(self._errors)
        
        if operation:
            errors = [e for e in errors if e.operation == operation]
        
        # 按时间倒序
        errors.sort(key=lambda x: x.timestamp, reverse=True)
        
        return errors[:limit]
    
    def reset(self):
        """重置所有监控数据"""
        self._metrics.clear()
        self._slow_queries.clear()
        self._errors.clear()
        logger.info("性能监控器已重置")
    
    def get_summary(self) -> str:
        """
        获取性能摘要（用于显示）
        
        Returns:
            格式化的摘要字符串
        """
        lines = ["性能监控摘要", "=" * 40]
        
        all_stats = self.get_stats()
        
        for operation, stats in all_stats.items():
            if stats['count'] == 0:
                continue
            
            lines.append(f"\n{operation}:")
            lines.append(f"  调用次数: {stats['count']}")
            lines.append(f"  平均延迟: {stats['avg_latency_ms']:.2f}ms")
            lines.append(f"  P95延迟: {stats['p95_latency_ms']:.2f}ms")
            lines.append(f"  错误率: {stats['error_rate']*100:.1f}%")
        
        return "\n".join(lines)


class PerformanceContext:
    """性能记录上下文"""
    
    def __init__(
        self,
        monitor: PerformanceMonitor,
        operation: str,
        metadata: Optional[Dict[str, Any]]
    ):
        self.monitor = monitor
        self.operation = operation
        self.metadata = metadata
        self.start_time = None
        self.error_message = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000
        success = exc_type is None
        
        if not success:
            self.error_message = str(exc_val)
        
        self.monitor.record_manual(
            operation=self.operation,
            duration_ms=duration_ms,
            success=success,
            error_message=self.error_message,
            metadata=self.metadata
        )
        
        # 不抑制异常
        return False


if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("性能监控器测试")
    print("=" * 50)
    
    monitor = PerformanceMonitor(slow_threshold_ms=50)
    
    # 模拟操作
    import random
    
    for i in range(100):
        operation = random.choice(["search", "save", "delete"])
        duration = random.uniform(10, 200)
        success = random.random() > 0.1  # 10%错误率
        
        monitor.record_manual(
            operation=operation,
            duration_ms=duration,
            success=success,
            error_message=None if success else "模拟错误"
        )
    
    # 打印摘要
    print("\n" + monitor.get_summary())
    
    # 打印慢查询
    print("\n慢查询 Top 5:")
    for q in monitor.get_slow_queries(limit=5):
        print(f"  {q.operation}: {q.duration_ms:.2f}ms")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
