"""
缓存管理器单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "optimization"))

import pytest
import time
from cache_manager import CacheManager, MultiLevelCache


class TestCacheManagerCreation:
    """测试缓存管理器创建"""
    
    def test_create_default(self):
        """测试默认创建"""
        cache = CacheManager()
        
        assert cache.max_size == 1000
        assert cache.ttl_seconds is None
    
    def test_create_with_params(self):
        """测试带参数创建"""
        cache = CacheManager(
            max_size=100,
            ttl_seconds=3600,
            max_memory_mb=100.0
        )
        
        assert cache.max_size == 100
        assert cache.ttl_seconds == 3600
        assert cache.max_memory_bytes == 100.0 * 1024 * 1024


class TestCacheManagerBasic:
    """测试基本缓存操作"""
    
    @pytest.fixture
    def cache(self):
        """提供缓存实例"""
        return CacheManager(max_size=10)
    
    def test_set_and_get(self, cache):
        """测试设置和获取"""
        cache.set("key1", "value1")
        
        value = cache.get("key1")
        
        assert value == "value1"
    
    def test_get_nonexistent(self, cache):
        """测试获取不存在的键"""
        value = cache.get("nonexistent")
        
        assert value is None
    
    def test_delete(self, cache):
        """测试删除"""
        cache.set("key1", "value1")
        
        result = cache.delete("key1")
        
        assert result is True
        assert cache.get("key1") is None
    
    def test_delete_nonexistent(self, cache):
        """测试删除不存在的键"""
        result = cache.delete("nonexistent")
        
        assert result is False


class TestCacheManagerLRU:
    """测试LRU淘汰策略"""
    
    @pytest.fixture
    def cache(self):
        """提供小容量缓存"""
        return CacheManager(max_size=3)
    
    def test_lru_eviction(self, cache):
        """测试LRU淘汰"""
        # 添加3个条目
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        # 访问key1，使其变为最新
        cache.get("key1")
        
        # 添加第4个，应该淘汰key2
        cache.set("key4", "value4")
        
        assert cache.get("key1") is not None  # 最近访问，保留
        assert cache.get("key2") is None      # 最久未访问，淘汰
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None


class TestCacheManagerTTL:
    """测试TTL过期"""
    
    @pytest.fixture
    def cache(self):
        """提供带TTL的缓存"""
        return CacheManager(max_size=10, ttl_seconds=1)
    
    def test_ttl_expiration(self, cache):
        """测试TTL过期"""
        cache.set("key1", "value1")
        
        # 立即获取，应该存在
        assert cache.get("key1") == "value1"
        
        # 等待过期
        time.sleep(1.1)
        
        # 再次获取，应该过期
        assert cache.get("key1") is None


class TestCacheManagerStats:
    """测试缓存统计"""
    
    @pytest.fixture
    def cache(self):
        """提供缓存实例"""
        return CacheManager(max_size=10)
    
    def test_stats_initial(self, cache):
        """测试初始统计"""
        stats = cache.get_stats()
        
        assert stats['size'] == 0
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['hit_rate'] == 0.0
    
    def test_stats_after_operations(self, cache):
        """测试操作后统计"""
        # 设置
        cache.set("key1", "value1")
        
        # 命中
        cache.get("key1")
        cache.get("key1")
        
        # 未命中
        cache.get("nonexistent")
        
        stats = cache.get_stats()
        
        assert stats['size'] == 1
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 2/3


class TestMultiLevelCache:
    """测试多级缓存"""
    
    @pytest.fixture
    def cache(self):
        """提供多级缓存实例"""
        return MultiLevelCache(l1_size=5, l2_size=10)
    
    def test_set_and_get(self, cache):
        """测试设置和获取"""
        cache.set("key1", "value1")
        
        value = cache.get("key1")
        
        assert value == "value1"
    
    def test_l1_l2_interaction(self, cache):
        """测试L1和L2交互"""
        # 设置
        cache.set("key1", "value1")
        
        # 从L1获取
        value1 = cache.l1.get("key1")
        assert value1 == "value1"
        
        # 从L2获取
        value2 = cache.l2.get("key1")
        assert value2 == "value1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
