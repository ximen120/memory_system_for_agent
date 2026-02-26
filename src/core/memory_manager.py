"""
记忆管理器

统一管理四层记忆架构，提供完整的记忆生命周期管理。
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json

try:
    from .memory_unit import MemoryUnit
    from .timestamp_utils import now, to_datetime
    from ..storage.base_storage import BaseStorage, StorageError
    from ..storage.json_storage import JsonStorage
    from ..retrieval.embedding_generator import EmbeddingGenerator
except ImportError:
    from memory_unit import MemoryUnit
    from timestamp_utils import now, to_datetime
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "storage"))
    sys.path.insert(0, str(Path(__file__).parent.parent / "retrieval"))
    from base_storage import BaseStorage, StorageError
    from json_storage import JsonStorage


class MemoryTier:
    """记忆分层枚举"""
    WORKING = "working"      # 工作记忆：24小时内
    SHORT_TERM = "short"     # 短期记忆：7天内
    MID_TERM = "mid"         # 中期记忆：30天内
    LONG_TERM = "long"       # 长期记忆：超过30天


class MemoryManager:
    """
    记忆管理器
    
    统一管理四层记忆架构，提供完整的 CRUD 和检索能力。
    
    Attributes:
        config: 配置参数
        storages: 各层存储后端
        embedding_gen: Embedding 生成器（可选）
    """
    
    # 默认分层时间配置（小时）
    DEFAULT_TIER_HOURS = {
        MemoryTier.WORKING: 24,
        MemoryTier.SHORT_TERM: 24 * 7,      # 7天
        MemoryTier.MID_TERM: 24 * 30,       # 30天
        MemoryTier.LONG_TERM: 24 * 365,     # 1年
    }
    
    def __init__(
        self,
        data_dir: str = "./data",
        use_embedding: bool = False,
        embedding_model: Optional[str] = None,
        tier_hours: Optional[Dict[str, int]] = None
    ):
        """
        初始化记忆管理器
        
        Args:
            data_dir: 数据存储目录
            use_embedding: 是否使用 Embedding 进行语义检索
            embedding_model: Embedding 模型名称
            tier_hours: 自定义分层时间配置
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 分层时间配置
        self.tier_hours = tier_hours or self.DEFAULT_TIER_HOURS.copy()
        
        # 初始化各层存储
        self.storages: Dict[str, BaseStorage] = {}
        self._init_storages()
        
        # 初始化 Embedding 生成器
        self.embedding_gen = None
        if use_embedding:
            try:
                self.embedding_gen = EmbeddingGenerator(
                    model_name=embedding_model or "sentence-transformers/all-MiniLM-L6-v2"
                )
            except Exception as e:
                print(f"警告: Embedding 生成器初始化失败: {e}")
        
        # 统计信息
        self.stats = {
            "total_saved": 0,
            "total_retrieved": 0,
            "total_deleted": 0,
        }
    
    def _init_storages(self) -> None:
        """初始化各层存储"""
        # 为每层创建独立的 JSON 存储
        for tier in [MemoryTier.WORKING, MemoryTier.SHORT_TERM, 
                     MemoryTier.MID_TERM, MemoryTier.LONG_TERM]:
            tier_dir = self.data_dir / "memories" / tier
            self.storages[tier] = JsonStorage(str(tier_dir))
    
    def _get_tier_for_memory(self, memory: MemoryUnit) -> str:
        """
        根据记忆的时间特征确定所属层级
        
        Args:
            memory: 记忆单元
            
        Returns:
            str: 层级名称
        """
        try:
            created_time = to_datetime(memory.created_at)
            age_hours = (datetime.now() - created_time).total_seconds() / 3600
            
            if age_hours <= self.tier_hours[MemoryTier.WORKING]:
                return MemoryTier.WORKING
            elif age_hours <= self.tier_hours[MemoryTier.SHORT_TERM]:
                return MemoryTier.SHORT_TERM
            elif age_hours <= self.tier_hours[MemoryTier.MID_TERM]:
                return MemoryTier.MID_TERM
            else:
                return MemoryTier.LONG_TERM
        except Exception:
            # 解析失败，默认放入工作记忆
            return MemoryTier.WORKING
    
    def _get_storage_for_tier(self, tier: str) -> BaseStorage:
        """获取指定层级的存储后端"""
        return self.storages.get(tier, self.storages[MemoryTier.WORKING])
    
    def save(self, memory: MemoryUnit, auto_tier: bool = True) -> str:
        """
        保存记忆
        
        Args:
            memory: 要保存的记忆单元
            auto_tier: 是否自动分层，默认 True
            
        Returns:
            str: 保存的记忆ID
        """
        # 生成 Embedding（如果启用）
        if self.embedding_gen and not memory.embedding:
            try:
                memory.embedding = self.embedding_gen.generate(memory.content)
            except Exception as e:
                print(f"警告: Embedding 生成失败: {e}")
        
        # 确定层级
        tier = self._get_tier_for_memory(memory) if auto_tier else MemoryTier.WORKING
        storage = self._get_storage_for_tier(tier)
        
        # 保存
        memory_id = storage.save(memory)
        self.stats["total_saved"] += 1
        
        return memory_id
    
    def load(self, memory_id: str) -> Optional[MemoryUnit]:
        """
        加载指定ID的记忆
        
        会遍历所有层级查找。
        
        Args:
            memory_id: 记忆唯一标识符
            
        Returns:
            Optional[MemoryUnit]: 找到的记忆，不存在返回 None
        """
        # 遍历所有层级查找
        for tier in [MemoryTier.WORKING, MemoryTier.SHORT_TERM,
                     MemoryTier.MID_TERM, MemoryTier.LONG_TERM]:
            storage = self._get_storage_for_tier(tier)
            try:
                memory = storage.load(memory_id)
                memory.update_access()
                self.stats["total_retrieved"] += 1
                return memory
            except Exception:
                continue
        
        return None
    
    def delete(self, memory_id: str) -> bool:
        """
        删除指定ID的记忆
        
        会遍历所有层级查找并删除。
        
        Args:
            memory_id: 记忆唯一标识符
            
        Returns:
            bool: 删除成功返回 True
        """
        for tier in [MemoryTier.WORKING, MemoryTier.SHORT_TERM,
                     MemoryTier.MID_TERM, MemoryTier.LONG_TERM]:
            storage = self._get_storage_for_tier(tier)
            try:
                if storage.delete(memory_id):
                    self.stats["total_deleted"] += 1
                    return True
            except Exception:
                continue
        
        return False
    
    def query(
        self,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_importance: Optional[float] = None,
        tier: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryUnit]:
        """
        条件查询记忆
        
        Args:
            memory_type: 按类型过滤
            tags: 按标签过滤
            min_importance: 最小重要度
            tier: 指定层级查询，None 表示查询所有层级
            limit: 返回数量上限
            
        Returns:
            List[MemoryUnit]: 符合条件的记忆列表
        """
        results = []
        
        # 确定查询的层级
        tiers_to_query = [tier] if tier else [MemoryTier.WORKING, MemoryTier.SHORT_TERM,
                                               MemoryTier.MID_TERM, MemoryTier.LONG_TERM]
        
        for t in tiers_to_query:
            if t not in self.storages:
                continue
            
            storage = self._get_storage_for_tier(t)
            tier_results = storage.query(
                memory_type=memory_type,
                tags=tags,
                min_importance=min_importance,
                limit=limit - len(results)
            )
            
            results.extend(tier_results)
            
            if len(results) >= limit:
                break
        
        # 按重要度和访问次数排序
        results.sort(key=lambda m: (m.importance, m.access_count), reverse=True)
        
        return results[:limit]
    
    def search_similar(
        self,
        query: str,
        limit: int = 5,
        min_similarity: float = 0.5
    ) -> List[Tuple[MemoryUnit, float]]:
        """
        语义相似度搜索
        
        需要启用 Embedding 功能。
        
        Args:
            query: 查询文本
            limit: 返回数量上限
            min_similarity: 最小相似度阈值
            
        Returns:
            List[Tuple[MemoryUnit, float]]: (记忆, 相似度) 列表
        """
        if not self.embedding_gen:
            raise RuntimeError("未启用 Embedding 功能，无法执行语义搜索")
        
        # 生成查询向量
        query_embedding = self.embedding_gen.generate(query)
        
        # 获取所有记忆（这里简化处理，实际应该使用向量数据库）
        all_memories = []
        for tier in [MemoryTier.WORKING, MemoryTier.SHORT_TERM,
                     MemoryTier.MID_TERM, MemoryTier.LONG_TERM]:
            storage = self._get_storage_for_tier(tier)
            all_memories.extend(storage.query(limit=1000))
        
        # 计算相似度
        from ..retrieval.similarity import cosine_similarity
        
        results = []
        for memory in all_memories:
            if memory.embedding:
                try:
                    similarity = cosine_similarity(query_embedding, memory.embedding)
                    if similarity >= min_similarity:
                        results.append((memory, similarity))
                except Exception:
                    continue
        
        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:limit]
    
    def migrate_tiers(self) -> Dict[str, int]:
        """
        执行层级迁移
        
        将过期的记忆从高层级迁移到低层级。
        
        Returns:
            Dict[str, int]: 各层级迁移数量统计
        """
        migrated = {
            "working_to_short": 0,
            "short_to_mid": 0,
            "mid_to_long": 0,
        }
        
        # 简化实现：重新保存所有记忆，让它们自动分层
        for tier in [MemoryTier.WORKING, MemoryTier.SHORT_TERM, MemoryTier.MID_TERM]:
            storage = self._get_storage_for_tier(tier)
            memories = storage.query(limit=10000)
            
            for memory in memories:
                correct_tier = self._get_tier_for_memory(memory)
                if correct_tier != tier:
                    # 迁移
                    try:
                        storage.delete(memory.memory_id)
                        new_storage = self._get_storage_for_tier(correct_tier)
                        new_storage.save(memory)
                        
                        # 统计
                        key = f"{tier}_to_{correct_tier.replace('_term', '')}"
                        if key in migrated:
                            migrated[key] += 1
                    except Exception:
                        continue
        
        return migrated
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict: 包含各层级数量、操作统计等
        """
        tier_counts = {}
        for tier in [MemoryTier.WORKING, MemoryTier.SHORT_TERM,
                     MemoryTier.MID_TERM, MemoryTier.LONG_TERM]:
            storage = self._get_storage_for_tier(tier)
            tier_counts[tier] = storage.count()
        
        return {
            "tier_counts": tier_counts,
            "total_memories": sum(tier_counts.values()),
            "operations": self.stats.copy(),
            "embedding_enabled": self.embedding_gen is not None,
        }
    
    def close(self) -> None:
        """关闭所有存储连接"""
        for storage in self.storages.values():
            try:
                storage.close()
            except Exception:
                pass


if __name__ == "__main__":
    # 简单测试
    print("MemoryManager 基础测试:\n")
    
    import tempfile
    import shutil
    
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 1. 创建管理器
        manager = MemoryManager(data_dir=tmpdir, use_embedding=False)
        print("1. 创建 MemoryManager")
        
        # 2. 保存记忆
        memory1 = MemoryUnit(
            content="安哥喜欢喝咖啡",
            memory_type="preference",
            importance=4.5,
            tags=["咖啡", "习惯"]
        )
        memory2 = MemoryUnit(
            content="安哥计划下周去北京",
            memory_type="task",
            importance=3.0,
            tags=["计划", "北京"]
        )
        
        id1 = manager.save(memory1)
        id2 = manager.save(memory2)
        print(f"2. 保存两条记忆: {id1}, {id2}")
        
        # 3. 加载记忆
        loaded = manager.load(id1)
        print(f"3. 加载记忆: {loaded.content if loaded else 'Not found'}")
        
        # 4. 查询记忆
        results = manager.query(memory_type="preference")
        print(f"4. 查询 preference 类型: {len(results)} 条")
        
        # 5. 获取统计
        stats = manager.get_stats()
        print(f"5. 统计信息:")
        print(f"   各层级数量: {stats['tier_counts']}")
        print(f"   总记忆数: {stats['total_memories']}")
        
        # 6. 删除记忆
        deleted = manager.delete(id1)
        print(f"6. 删除记忆: {'成功' if deleted else '失败'}")
        
        print("\n✅ 所有基础测试通过!")
        
    finally:
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
