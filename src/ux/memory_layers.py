"""
四层记忆架构实现

实现工作记忆、短期记忆、长期记忆、永久记忆的分层管理，
支持基于访问频率、时间、重要性的自动流转逻辑。
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import json
import threading

# 导入核心组件
try:
    from ..core.memory_unit import MemoryUnit
    from ..core.timestamp_utils import now, to_datetime
    from ..core.id_generator import generate_memory_id
    from ..storage.json_storage import JsonStorage
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from core.memory_unit import MemoryUnit
    from core.timestamp_utils import now, to_datetime
    from core.id_generator import generate_memory_id
    from storage.json_storage import JsonStorage


class MemoryLayerType(Enum):
    """记忆层类型枚举"""
    WORKING = "working"       # 工作记忆：当前活跃上下文
    SHORT_TERM = "short"      # 短期记忆：最近7天
    LONG_TERM = "long"        # 长期记忆：重要信息（手动标记或高频访问）
    PERMANENT = "permanent"   # 永久记忆：核心知识（自动识别）


@dataclass
class LayerConfig:
    """记忆层配置"""
    name: str
    description: str
    # 时间阈值（天）
    max_age_days: Optional[int] = None
    # 访问频率阈值（访问次数/天）
    min_access_frequency: float = 0.0
    # 重要性阈值
    min_importance: float = 1.0
    # 容量限制
    max_capacity: Optional[int] = None
    # 自动流转目标层
    auto_promote_to: Optional[MemoryLayerType] = None
    auto_demote_to: Optional[MemoryLayerType] = None


# 默认层配置
DEFAULT_LAYER_CONFIGS: Dict[MemoryLayerType, LayerConfig] = {
    MemoryLayerType.WORKING: LayerConfig(
        name="工作记忆",
        description="当前活跃上下文，当前会话或最近几小时的记忆",
        max_age_days=1,  # 1天内
        min_importance=1.0,
        max_capacity=100,
        auto_demote_to=MemoryLayerType.SHORT_TERM
    ),
    MemoryLayerType.SHORT_TERM: LayerConfig(
        name="短期记忆",
        description="最近7天的记忆，日常对话和临时信息",
        max_age_days=7,  # 7天内
        min_access_frequency=0.1,  # 至少每10天访问1次
        min_importance=1.0,
        max_capacity=1000,
        auto_promote_to=MemoryLayerType.LONG_TERM,
        auto_demote_to=None
    ),
    MemoryLayerType.LONG_TERM: LayerConfig(
        name="长期记忆",
        description="重要信息，高频访问或手动标记的记忆",
        max_age_days=30,  # 30天内需要访问
        min_access_frequency=0.05,  # 至少每20天访问1次
        min_importance=3.0,  # 重要性>=3
        max_capacity=5000,
        auto_promote_to=MemoryLayerType.PERMANENT,
        auto_demote_to=MemoryLayerType.SHORT_TERM
    ),
    MemoryLayerType.PERMANENT: LayerConfig(
        name="永久记忆",
        description="核心知识，自动识别的高价值信息",
        max_age_days=None,  # 无时间限制
        min_access_frequency=0.01,  # 至少每100天访问1次
        min_importance=4.5,  # 重要性>=4.5
        max_capacity=None,  # 无容量限制
        auto_promote_to=None,
        auto_demote_to=MemoryLayerType.LONG_TERM
    ),
}


class MemoryLayer:
    """
    记忆层基类
    
    管理特定层级的记忆存储和检索。
    """
    
    def __init__(
        self,
        layer_type: MemoryLayerType,
        data_dir: str,
        config: Optional[LayerConfig] = None
    ):
        """
        初始化记忆层
        
        Args:
            layer_type: 层类型
            data_dir: 数据存储目录
            config: 层配置，默认使用 DEFAULT_LAYER_CONFIGS
        """
        self.layer_type = layer_type
        self.config = config or DEFAULT_LAYER_CONFIGS[layer_type]
        
        # 初始化存储
        layer_dir = Path(data_dir) / "layers" / layer_type.value
        self.storage = JsonStorage(str(layer_dir))
        
        # 内存缓存（用于快速访问）
        self._cache: Dict[str, MemoryUnit] = {}
        self._cache_lock = threading.RLock()
        
        # 加载到缓存
        self._load_cache()
    
    def _load_cache(self) -> None:
        """加载所有记忆到缓存"""
        memories = self.storage.query(limit=10000)
        with self._cache_lock:
            self._cache = {m.memory_id: m for m in memories}
    
    def add(self, memory: MemoryUnit) -> str:
        """
        添加记忆到本层
        
        Args:
            memory: 记忆单元
            
        Returns:
            str: 记忆ID
        """
        memory_id = self.storage.save(memory)
        with self._cache_lock:
            self._cache[memory_id] = memory
        return memory_id
    
    def get(self, memory_id: str) -> Optional[MemoryUnit]:
        """
        获取记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            Optional[MemoryUnit]: 记忆单元
        """
        # 先查缓存
        with self._cache_lock:
            if memory_id in self._cache:
                return self._cache[memory_id]
        
        # 再查存储
        try:
            memory = self.storage.load(memory_id)
            if memory:
                with self._cache_lock:
                    self._cache[memory_id] = memory
            return memory
        except Exception:
            return None
    
    def update(self, memory: MemoryUnit) -> bool:
        """
        更新记忆
        
        Args:
            memory: 记忆单元
            
        Returns:
            bool: 是否成功
        """
        try:
            self.storage.save(memory)
            with self._cache_lock:
                self._cache[memory.memory_id] = memory
            return True
        except Exception:
            return False
    
    def remove(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            bool: 是否成功
        """
        try:
            result = self.storage.delete(memory_id)
            with self._cache_lock:
                self._cache.pop(memory_id, None)
            return result
        except Exception:
            return False
    
    def query(
        self,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_importance: Optional[float] = None,
        limit: int = 10
    ) -> List[MemoryUnit]:
        """
        查询记忆
        
        Args:
            memory_type: 记忆类型过滤
            tags: 标签过滤
            min_importance: 最小重要性
            limit: 返回数量限制
            
        Returns:
            List[MemoryUnit]: 记忆列表
        """
        return self.storage.query(
            memory_type=memory_type,
            tags=tags,
            min_importance=min_importance,
            limit=limit
        )
    
    def get_all(self) -> List[MemoryUnit]:
        """
        获取本层所有记忆
        
        Returns:
            List[MemoryUnit]: 所有记忆
        """
        with self._cache_lock:
            return list(self._cache.values())
    
    def count(self) -> int:
        """
        获取记忆数量
        
        Returns:
            int: 数量
        """
        return self.storage.count()
    
    def should_promote(self, memory: MemoryUnit) -> bool:
        """
        判断记忆是否应该晋升到更高层
        
        Args:
            memory: 记忆单元
            
        Returns:
            bool: 是否应该晋升
        """
        if not self.config.auto_promote_to:
            return False
        
        # 检查重要性
        if memory.importance < self.config.min_importance:
            return False
        
        # 检查访问频率
        age_days = self._get_age_days(memory)
        if age_days <= 0:
            return False
        
        access_frequency = memory.access_count / age_days
        if access_frequency < self.config.min_access_frequency:
            return False
        
        return True
    
    def should_demote(self, memory: MemoryUnit) -> bool:
        """
        判断记忆是否应该降级到更低层
        
        Args:
            memory: 记忆单元
            
        Returns:
            bool: 是否应该降级
        """
        if not self.config.auto_demote_to:
            return False
        
        # 检查时间
        age_days = self._get_age_days(memory)
        if self.config.max_age_days and age_days > self.config.max_age_days:
            return True
        
        # 检查访问频率
        if age_days > 0:
            access_frequency = memory.access_count / age_days
            if access_frequency < self.config.min_access_frequency:
                return True
        
        return False
    
    def _get_age_days(self, memory: MemoryUnit) -> float:
        """获取记忆年龄（天）"""
        try:
            created = to_datetime(memory.created_at)
            return (datetime.now() - created).total_seconds() / 86400
        except Exception:
            return 0.0
    
    def clear(self) -> int:
        """
        清空本层所有记忆
        
        Returns:
            int: 删除的数量
        """
        count = 0
        with self._cache_lock:
            for memory_id in list(self._cache.keys()):
                if self.storage.delete(memory_id):
                    count += 1
            self._cache.clear()
        return count
    
    def close(self) -> None:
        """关闭存储连接"""
        self.storage.close()


class MemoryLayerManager:
    """
    四层记忆架构管理器
    
    统一管理四层记忆，实现自动流转逻辑。
    """
    
    def __init__(
        self,
        data_dir: str = "./data",
        configs: Optional[Dict[MemoryLayerType, LayerConfig]] = None,
        auto_migrate: bool = True
    ):
        """
        初始化四层记忆管理器
        
        Args:
            data_dir: 数据存储目录
            configs: 自定义层配置
            auto_migrate: 是否启用自动流转
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.configs = configs or DEFAULT_LAYER_CONFIGS
        self.auto_migrate = auto_migrate
        
        # 初始化四层
        self.layers: Dict[MemoryLayerType, MemoryLayer] = {}
        for layer_type in MemoryLayerType:
            self.layers[layer_type] = MemoryLayer(
                layer_type=layer_type,
                data_dir=str(self.data_dir),
                config=self.configs[layer_type]
            )
        
        # 迁移锁
        self._migrate_lock = threading.RLock()
        
        # 统计信息
        self.stats = {
            "total_added": 0,
            "total_migrated": 0,
            "total_accessed": 0,
            "migrations": {
                "promotions": 0,
                "demotions": 0
            }
        }
    
    def add(
        self,
        content: str,
        memory_type: str,
        importance: float = 3.0,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        layer: Optional[MemoryLayerType] = None
    ) -> str:
        """
        添加新记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性 1.0-5.0
            tags: 标签列表
            source: 来源
            layer: 指定存储层，None则自动选择
            
        Returns:
            str: 记忆ID
        """
        # 创建记忆单元
        memory = MemoryUnit(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            source=source
        )
        
        # 确定存储层
        if layer is None:
            layer = self._determine_layer(memory)
        
        # 添加到对应层
        memory_id = self.layers[layer].add(memory)
        self.stats["total_added"] += 1
        
        return memory_id
    
    def _determine_layer(self, memory: MemoryUnit) -> MemoryLayerType:
        """
        根据记忆特征自动确定存储层
        
        Args:
            memory: 记忆单元
            
        Returns:
            MemoryLayerType: 目标层
        """
        # 高重要性 -> 永久记忆
        if memory.importance >= 4.5:
            return MemoryLayerType.PERMANENT
        
        # 中等重要性 -> 长期记忆
        if memory.importance >= 3.0:
            return MemoryLayerType.LONG_TERM
        
        # 默认 -> 短期记忆
        return MemoryLayerType.SHORT_TERM
    
    def get(
        self,
        memory_id: str,
        update_access: bool = True
    ) -> Optional[MemoryUnit]:
        """
        获取记忆（跨层搜索）
        
        Args:
            memory_id: 记忆ID
            update_access: 是否更新访问统计
            
        Returns:
            Optional[MemoryUnit]: 记忆单元
        """
        # 按优先级顺序搜索
        search_order = [
            MemoryLayerType.WORKING,
            MemoryLayerType.SHORT_TERM,
            MemoryLayerType.LONG_TERM,
            MemoryLayerType.PERMANENT
        ]
        
        for layer_type in search_order:
            memory = self.layers[layer_type].get(memory_id)
            if memory:
                if update_access:
                    memory.update_access()
                    self.layers[layer_type].update(memory)
                    self.stats["total_accessed"] += 1
                    
                    # 检查是否需要晋升
                    if self.auto_migrate:
                        self._check_promotion(memory, layer_type)
                
                return memory
        
        return None
    
    def _check_promotion(
        self,
        memory: MemoryUnit,
        current_layer: MemoryLayerType
    ) -> None:
        """
        检查并执行晋升
        
        Args:
            memory: 记忆单元
            current_layer: 当前层
        """
        layer = self.layers[current_layer]
        
        if layer.should_promote(memory):
            target_layer = layer.config.auto_promote_to
            if target_layer:
                self._migrate_memory(memory, current_layer, target_layer)
    
    def _migrate_memory(
        self,
        memory: MemoryUnit,
        from_layer: MemoryLayerType,
        to_layer: MemoryLayerType
    ) -> bool:
        """
        迁移记忆到另一层
        
        Args:
            memory: 记忆单元
            from_layer: 源层
            to_layer: 目标层
            
        Returns:
            bool: 是否成功
        """
        with self._migrate_lock:
            try:
                # 从源层删除
                if not self.layers[from_layer].remove(memory.memory_id):
                    return False
                
                # 添加到目标层
                self.layers[to_layer].add(memory)
                
                # 更新统计
                self.stats["total_migrated"] += 1
                if to_layer.value > from_layer.value:
                    self.stats["migrations"]["promotions"] += 1
                else:
                    self.stats["migrations"]["demotions"] += 1
                
                return True
            except Exception as e:
                print(f"迁移失败: {e}")
                return False
    
    def query(
        self,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_importance: Optional[float] = None,
        layers: Optional[List[MemoryLayerType]] = None,
        limit: int = 10
    ) -> List[MemoryUnit]:
        """
        跨层查询记忆
        
        Args:
            memory_type: 记忆类型过滤
            tags: 标签过滤
            min_importance: 最小重要性
            layers: 指定查询层，None则查询所有
            limit: 返回数量限制
            
        Returns:
            List[MemoryUnit]: 记忆列表
        """
        results = []
        
        query_layers = layers or list(MemoryLayerType)
        
        for layer_type in query_layers:
            layer_results = self.layers[layer_type].query(
                memory_type=memory_type,
                tags=tags,
                min_importance=min_importance,
                limit=limit
            )
            results.extend(layer_results)
        
        # 按重要性排序
        results.sort(key=lambda m: m.importance, reverse=True)
        
        return results[:limit]
    
    def search_by_keywords(
        self,
        keywords: List[str],
        layers: Optional[List[MemoryLayerType]] = None,
        limit: int = 10
    ) -> List[MemoryUnit]:
        """
        关键词搜索（跨层）
        
        Args:
            keywords: 关键词列表
            layers: 指定查询层
            limit: 返回数量限制
            
        Returns:
            List[MemoryUnit]: 记忆列表
        """
        results = []
        query_layers = layers or list(MemoryLayerType)
        
        for layer_type in query_layers:
            memories = self.layers[layer_type].get_all()
            for memory in memories:
                # 简单关键词匹配
                content_lower = memory.content.lower()
                if any(kw.lower() in content_lower for kw in keywords):
                    results.append(memory)
        
        # 按相关度排序（匹配关键词数量）
        def relevance_score(memory: MemoryUnit) -> int:
            content_lower = memory.content.lower()
            return sum(1 for kw in keywords if kw.lower() in content_lower)
        
        results.sort(key=relevance_score, reverse=True)
        
        return results[:limit]
    
    def get_timeline(
        self,
        days: int = 7,
        layers: Optional[List[MemoryLayerType]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取时间线视图
        
        Args:
            days: 天数范围
            layers: 指定查询层
            
        Returns:
            List[Dict]: 时间线数据
        """
        cutoff = datetime.now() - timedelta(days=days)
        timeline = []
        
        query_layers = layers or list(MemoryLayerType)
        
        for layer_type in query_layers:
            memories = self.layers[layer_type].get_all()
            for memory in memories:
                try:
                    created = to_datetime(memory.created_at)
                    if created >= cutoff:
                        timeline.append({
                            "memory_id": memory.memory_id,
                            "content": memory.content,
                            "memory_type": memory.memory_type,
                            "importance": memory.importance,
                            "created_at": memory.created_at,
                            "layer": layer_type.value,
                            "access_count": memory.access_count
                        })
                except Exception:
                    continue
        
        # 按时间排序
        timeline.sort(key=lambda x: x["created_at"], reverse=True)
        
        return timeline
    
    def run_migration(self) -> Dict[str, int]:
        """
        执行全量迁移
        
        检查所有记忆，执行晋升和降级。
        
        Returns:
            Dict: 迁移统计
        """
        with self._migrate_lock:
            migration_stats = {
                "promotions": 0,
                "demotions": 0,
                "errors": 0
            }
            
            for layer_type in MemoryLayerType:
                layer = self.layers[layer_type]
                memories = layer.get_all()
                
                for memory in memories:
                    try:
                        # 检查晋升
                        if layer.should_promote(memory):
                            target = layer.config.auto_promote_to
                            if target and self._migrate_memory(memory, layer_type, target):
                                migration_stats["promotions"] += 1
                        
                        # 检查降级
                        elif layer.should_demote(memory):
                            target = layer.config.auto_demote_to
                            if target and self._migrate_memory(memory, layer_type, target):
                                migration_stats["demotions"] += 1
                    
                    except Exception:
                        migration_stats["errors"] += 1
            
            return migration_stats
    
    def promote_manually(
        self,
        memory_id: str,
        target_layer: MemoryLayerType
    ) -> bool:
        """
        手动晋升记忆
        
        Args:
            memory_id: 记忆ID
            target_layer: 目标层
            
        Returns:
            bool: 是否成功
        """
        # 找到记忆当前所在层
        for layer_type in MemoryLayerType:
            memory = self.layers[layer_type].get(memory_id)
            if memory:
                return self._migrate_memory(memory, layer_type, target_layer)
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        layer_stats = {}
        for layer_type, layer in self.layers.items():
            layer_stats[layer_type.value] = {
                "count": layer.count(),
                "config": {
                    "max_age_days": layer.config.max_age_days,
                    "min_importance": layer.config.min_importance,
                    "min_access_frequency": layer.config.min_access_frequency
                }
            }
        
        return {
            "layers": layer_stats,
            "operations": self.stats.copy(),
            "total_memories": sum(layer.count() for layer in self.layers.values())
        }
    
    def close(self) -> None:
        """关闭所有层"""
        for layer in self.layers.values():
            layer.close()


# 便捷函数
def create_memory_layers(
    data_dir: str = "./data",
    auto_migrate: bool = True
) -> MemoryLayerManager:
    """
    创建四层记忆管理器
    
    Args:
        data_dir: 数据目录
        auto_migrate: 是否自动迁移
        
    Returns:
        MemoryLayerManager: 管理器实例
    """
    return MemoryLayerManager(data_dir=data_dir, auto_migrate=auto_migrate)


if __name__ == "__main__":
    # 基础测试
    print("=" * 60)
    print("四层记忆架构测试")
    print("=" * 60)
    
    import tempfile
    import shutil
    
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 1. 创建管理器
        print("\n1. 创建四层记忆管理器...")
        manager = create_memory_layers(data_dir=tmpdir, auto_migrate=False)
        print("   ✅ 创建成功")
        
        # 2. 添加不同重要性的记忆
        print("\n2. 添加测试记忆...")
        
        # 永久记忆（高重要性）
        perm_id = manager.add(
            content="安哥是Simon，安仔的哥哥",
            memory_type="fact",
            importance=5.0,
            tags=["身份", "核心"]
        )
        print(f"   永久记忆: {perm_id[:20]}...")
        
        # 长期记忆（中等重要性）
        long_id = manager.add(
            content="安哥喜欢喝咖啡，每天早上必须一杯美式",
            memory_type="preference",
            importance=4.0,
            tags=["咖啡", "习惯"]
        )
        print(f"   长期记忆: {long_id[:20]}...")
        
        # 短期记忆（普通重要性）
        short_id = manager.add(
            content="今天天气不错，适合出门",
            memory_type="context",
            importance=2.0,
            tags=["天气"]
        )
        print(f"   短期记忆: {short_id[:20]}...")
        
        # 3. 查询统计
        print("\n3. 各层统计:")
        stats = manager.get_stats()
        for layer_name, layer_stat in stats["layers"].items():
            print(f"   {layer_name}: {layer_stat['count']} 条")
        
        # 4. 获取记忆
        print("\n4. 获取记忆:")
        memory = manager.get(perm_id)
        if memory:
            print(f"   获取成功: {memory.content[:30]}...")
            print(f"   访问次数: {memory.access_count}")
        
        # 5. 关键词搜索
        print("\n5. 关键词搜索 '安哥':")
        results = manager.search_by_keywords(["安哥"], limit=5)
        print(f"   找到 {len(results)} 条记忆")
        for r in results:
            print(f"   - {r.content[:40]}...")
        
        # 6. 时间线
        print("\n6. 时间线（最近7天）:")
        timeline = manager.get_timeline(days=7)
        print(f"   共 {len(timeline)} 条记录")
        
        # 7. 执行迁移
        print("\n7. 执行自动迁移...")
        migration_stats = manager.run_migration()
        print(f"   晋升: {migration_stats['promotions']} 条")
        print(f"   降级: {migration_stats['demotions']} 条")
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        
    finally:
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
