"""
缓存管理器

智能管理记忆系统的缓存，提高访问效率。
"""

import time
import logging
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    size_bytes: int = 0


class CacheManager:
    """
    缓存管理器
    
    提供智能缓存功能：
    - LRU淘汰策略
    - TTL过期
    - 大小限制
    - 命中率统计
    
    使用示例：
        >>> cache = CacheManager(max_size=1000, ttl_seconds=3600)
        >>> 
        >>> # 设置缓存
        >>> cache.set("key1", value)
        >>> 
        >>> # 获取缓存
        >>> value = cache.get("key1")
        >>> 
        >>> # 获取统计
        >>> stats = cache.get_stats()
        >>> print(f"命中率: {stats['hit_rate']:.2%}")
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: Optional[int] = None,
        max_memory_mb: Optional[float] = None,
        eviction_callback: Optional[Callable] = None
    ):
        """
        初始化缓存管理器
        
        Args:
            max_size: 最大条目数
            ttl_seconds: TTL（秒）
            max_memory_mb: 最大内存（MB）
            eviction_callback: 淘汰回调
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.max_memory_bytes = max_memory_mb * 1024 * 1024 if max_memory_mb else None
        self.eviction_callback = eviction_callback
        
        # 使用OrderedDict实现LRU
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
        # 统计
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        
        logger.info(f"缓存管理器初始化: max_size={max_size}, ttl={ttl_seconds}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值或None
        """
        entry = self._cache.get(key)
        
        if entry is None:
            self._misses += 1
            return None
        
        # 检查TTL
        if self.ttl_seconds:
            age = (datetime.now() - entry.created_at).total_seconds()
            if age > self.ttl_seconds:
                # 过期，删除
                del self._cache[key]
                self._misses += 1
                return None
        
        # 更新访问信息
        entry.accessed_at = datetime.now()
        entry.access_count += 1
        
        # 移动到末尾（LRU）
        self._cache.move_to_end(key)
        
        self._hits += 1
        return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl_seconds: 自定义TTL
            
        Returns:
            是否成功
        """
        try:
            # 检查是否需要淘汰
            self._evict_if_needed()
            
            # 创建条目
            now = datetime.now()
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                accessed_at=now,
                size_bytes=self._estimate_size(value)
            )
            
            # 如果key已存在，先删除
            if key in self._cache:
                del self._cache[key]
            
            # 添加新条目
            self._cache[key] = entry
            
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功
        """
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        logger.info("缓存已清空")
    
    def _evict_if_needed(self):
        """检查并执行淘汰"""
        # 检查条目数
        while len(self._cache) >= self.max_size:
            self._evict_one()
        
        # 检查内存
        if self.max_memory_bytes:
            while self._get_total_size() > self.max_memory_bytes and self._cache:
                self._evict_one()
    
    def _evict_one(self):
        """淘汰一个条目（LRU）"""
        if not self._cache:
            return
        
        # 淘汰最久未访问的（OrderedDict的第一个）
        key, entry = self._cache.popitem(last=False)
        self._evictions += 1
        
        if self.eviction_callback:
            self.eviction_callback(key, entry.value)
        
        logger.debug(f"淘汰缓存: {key}")
    
    def _estimate_size(self, value: Any) -> int:
        """估算值的大小（字节）"""
        try:
            import sys
            return sys.getsizeof(value)
        except:
            return 0
    
    def _get_total_size(self) -> int:
        """获取总大小"""
        return sum(entry.size_bytes for entry in self._cache.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计
        
        Returns:
            统计信息字典
        """
        total_requests = self._hits + self._misses
        hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
        
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'memory_bytes': self._get_total_size(),
            'hits': self._hits,
            'misses': self._misses,
            'evictions': self._evictions,
            'hit_rate': hit_rate,
            'miss_rate': 1 - hit_rate
        }
    
    def get_keys(self) -> List[str]:
        """获取所有缓存键"""
        return list(self._cache.keys())
    
    def contains(self, key: str) -> bool:
        """检查是否包含键"""
        return key in self._cache
    
    def get_expired_keys(self) -> List[str]:
        """获取已过期的键"""
        if not self.ttl_seconds:
            return []
        
        expired = []
        now = datetime.now()
        
        for key, entry in self._cache.items():
            age = (now - entry.created_at).total_seconds()
            if age > self.ttl_seconds:
                expired.append(key)
        
        return expired
    
    def cleanup_expired(self) -> int:
        """
        清理过期条目
        
        Returns:
            清理数量
        """
        expired_keys = self.get_expired_keys()
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"清理 {len(expired_keys)} 条过期缓存")
        
        return len(expired_keys)
    
    def get_popular_keys(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        获取热门键
        
        Args:
            top_n: 返回数量
            
        Returns:
            [(key, access_count), ...]
        """
        items = [(entry.key, entry.access_count) for entry in self._cache.values()]
        items.sort(key=lambda x: x[1], reverse=True)
        return items[:top_n]


class MultiLevelCache:
    """
    多级缓存
    
    L1: 内存缓存（最快）
    L2: 本地存储（较快）
    """
    
    def __init__(
        self,
        l1_size: int = 100,
        l2_size: int = 1000
    ):
        """
        初始化多级缓存
        
        Args:
            l1_size: L1缓存大小
            l2_size: L2缓存大小
        """
        self.l1 = CacheManager(max_size=l1_size, ttl_seconds=300)  # 5分钟TTL
        self.l2 = CacheManager(max_size=l2_size, ttl_seconds=3600)  # 1小时TTL
        
        logger.info(f"多级缓存初始化: L1={l1_size}, L2={l2_size}")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        # 先查L1
        value = self.l1.get(key)
        if value is not None:
            return value
        
        # 再查L2
        value = self.l2.get(key)
        if value is not None:
            # 回填L1
            self.l1.set(key, value)
            return value
        
        return None
    
    def set(self, key: str, value: Any):
        """设置缓存值"""
        self.l1.set(key, value)
        self.l2.set(key, value)
    
    def delete(self, key: str):
        """删除缓存"""
        self.l1.delete(key)
        self.l2.delete(key)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'l1': self.l1.get_stats(),
            'l2': self.l2.get_stats()
        }


if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("缓存管理器测试")
    print("=" * 50)
    
    cache = CacheManager(max_size=5, ttl_seconds=10)
    
    # 设置缓存
    for i in range(7):
        cache.set(f"key{i}", f"value{i}")
        print(f"设置 key{i}")
    
    print(f"\n缓存大小: {len(cache._cache)}")
    
    # 访问缓存
    for i in range(5):
        value = cache.get(f"key{i}")
        print(f"获取 key{i}: {value}")
    
    # 统计
    stats = cache.get_stats()
    print(f"\n统计:")
    print(f"  大小: {stats['size']}")
    print(f"  命中: {stats['hits']}")
    print(f"  未命中: {stats['misses']}")
    print(f"  命中率: {stats['hit_rate']:.2%}")
    print(f"  淘汰: {stats['evictions']}")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
