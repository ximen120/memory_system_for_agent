"""
索引优化器

自动优化记忆索引，提高检索效率。
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class IndexStats:
    """索引统计信息"""
    total_documents: int
    total_size_mb: float
    avg_document_size: float
    fragmentation_ratio: float  # 碎片率
    last_optimized: Optional[datetime]


class IndexOptimizer:
    """
    索引优化器
    
    提供索引优化功能：
    - 碎片整理
    - 重复检测
    - 冷数据归档
    - 索引重建
    
    使用示例：
        >>> optimizer = IndexOptimizer(storage)
        >>> 
        >>> # 分析索引
        >>> stats = optimizer.analyze()
        >>> print(f"碎片率: {stats.fragmentation_ratio:.2%}")
        >>> 
        >>> # 优化索引
        >>> result = optimizer.optimize()
        >>> print(f"优化完成，释放空间: {result['space_saved_mb']:.2f}MB")
    """
    
    def __init__(
        self,
        storage=None,
        fragmentation_threshold: float = 0.3,
        duplicate_threshold: float = 0.95,
        cold_data_days: int = 90
    ):
        """
        初始化索引优化器
        
        Args:
            storage: 存储后端
            fragmentation_threshold: 碎片率阈值
            duplicate_threshold: 重复检测阈值
            cold_data_days: 冷数据天数
        """
        self.storage = storage
        self.fragmentation_threshold = fragmentation_threshold
        self.duplicate_threshold = duplicate_threshold
        self.cold_data_days = cold_data_days
        
        logger.info(f"索引优化器初始化: fragmentation_threshold={fragmentation_threshold}")
    
    def analyze(self) -> IndexStats:
        """
        分析索引状态
        
        Returns:
            IndexStats: 索引统计信息
        """
        try:
            if self.storage:
                # 从存储获取统计
                total_docs = self.storage.count()
                # 这里可以根据实际存储实现更多统计
                
                return IndexStats(
                    total_documents=total_docs,
                    total_size_mb=0.0,  # 需要存储支持
                    avg_document_size=0.0,
                    fragmentation_ratio=0.0,
                    last_optimized=None
                )
            else:
                return IndexStats(
                    total_documents=0,
                    total_size_mb=0.0,
                    avg_document_size=0.0,
                    fragmentation_ratio=0.0,
                    last_optimized=None
                )
        except Exception as e:
            logger.error(f"分析索引失败: {e}")
            return IndexStats(
                total_documents=0,
                total_size_mb=0.0,
                avg_document_size=0.0,
                fragmentation_ratio=0.0,
                last_optimized=None
            )
    
    def find_duplicates(
        self,
        similarity_threshold: Optional[float] = None
    ) -> List[Tuple[str, str, float]]:
        """
        查找重复或相似的记忆
        
        Args:
            similarity_threshold: 相似度阈值
            
        Returns:
            List[Tuple[id1, id2, similarity]]: 重复记忆对
        """
        threshold = similarity_threshold or self.duplicate_threshold
        duplicates = []
        
        try:
            if not self.storage:
                return duplicates
            
            # 获取所有记忆
            all_memories = self.storage.list_all()
            
            # 两两比较（简单实现，大数据量需要优化）
            from retrieval import SimilarityService
            similarity_service = SimilarityService()
            
            for i, mem1 in enumerate(all_memories):
                for mem2 in all_memories[i+1:]:
                    # 比较内容相似度
                    if hasattr(mem1, 'embedding') and hasattr(mem2, 'embedding'):
                        if mem1.embedding and mem2.embedding:
                            result = similarity_service.compute(
                                mem1.embedding,
                                mem2.embedding
                            )
                            if result.normalized_score >= threshold:
                                duplicates.append((
                                    mem1.memory_id,
                                    mem2.memory_id,
                                    result.normalized_score
                                ))
            
            logger.info(f"发现 {len(duplicates)} 对重复记忆")
            return duplicates
            
        except Exception as e:
            logger.error(f"查找重复失败: {e}")
            return []
    
    def find_cold_data(
        self,
        days: Optional[int] = None
    ) -> List[str]:
        """
        查找冷数据（长期未访问）
        
        Args:
            days: 天数阈值
            
        Returns:
            List[str]: 冷数据记忆ID列表
        """
        threshold_days = days or self.cold_data_days
        cold_ids = []
        
        try:
            if not self.storage:
                return cold_ids
            
            cutoff = datetime.now() - timedelta(days=threshold_days)
            
            # 获取所有记忆
            all_memories = self.storage.list_all()
            
            for memory in all_memories:
                # 检查最后访问时间
                last_accessed = getattr(memory, 'last_accessed_at', None)
                if last_accessed:
                    if isinstance(last_accessed, str):
                        last_accessed = datetime.fromisoformat(last_accessed)
                    if last_accessed < cutoff:
                        cold_ids.append(memory.memory_id)
            
            logger.info(f"发现 {len(cold_ids)} 条冷数据")
            return cold_ids
            
        except Exception as e:
            logger.error(f"查找冷数据失败: {e}")
            return []
    
    def optimize(self) -> Dict[str, Any]:
        """
        执行索引优化
        
        Returns:
            优化结果
        """
        result = {
            'optimized': False,
            'duplicates_removed': 0,
            'cold_data_archived': 0,
            'space_saved_mb': 0.0,
            'errors': []
        }
        
        try:
            # 1. 分析索引
            stats = self.analyze()
            logger.info(f"索引分析: {stats.total_documents} 文档")
            
            # 2. 处理重复
            duplicates = self.find_duplicates()
            if duplicates:
                removed = self._remove_duplicates(duplicates)
                result['duplicates_removed'] = removed
                logger.info(f"移除 {removed} 条重复记忆")
            
            # 3. 处理冷数据
            cold_ids = self.find_cold_data()
            if cold_ids:
                archived = self._archive_cold_data(cold_ids)
                result['cold_data_archived'] = archived
                logger.info(f"归档 {archived} 条冷数据")
            
            result['optimized'] = True
            
        except Exception as e:
            logger.error(f"优化失败: {e}")
            result['errors'].append(str(e))
        
        return result
    
    def _remove_duplicates(
        self,
        duplicates: List[Tuple[str, str, float]]
    ) -> int:
        """移除重复记忆"""
        removed = 0
        
        try:
            for id1, id2, similarity in duplicates:
                # 保留第一个，删除第二个
                if self.storage:
                    self.storage.delete(id2)
                    removed += 1
        except Exception as e:
            logger.error(f"移除重复失败: {e}")
        
        return removed
    
    def _archive_cold_data(self, cold_ids: List[str]) -> int:
        """归档冷数据"""
        # 这里可以实现归档逻辑
        # 例如移动到归档存储或压缩
        logger.info(f"归档 {len(cold_ids)} 条冷数据（待实现）")
        return 0
    
    def get_recommendations(self) -> List[str]:
        """
        获取优化建议
        
        Returns:
            建议列表
        """
        recommendations = []
        
        try:
            stats = self.analyze()
            
            # 检查碎片率
            if stats.fragmentation_ratio > self.fragmentation_threshold:
                recommendations.append(
                    f"索引碎片率过高 ({stats.fragmentation_ratio:.1%})，建议优化"
                )
            
            # 检查重复
            duplicates = self.find_duplicates()
            if duplicates:
                recommendations.append(
                    f"发现 {len(duplicates)} 对重复记忆，建议清理"
                )
            
            # 检查冷数据
            cold_ids = self.find_cold_data()
            if cold_ids:
                recommendations.append(
                    f"发现 {len(cold_ids)} 条冷数据，建议归档"
                )
            
            if not recommendations:
                recommendations.append("索引状态良好，无需优化")
            
        except Exception as e:
            recommendations.append(f"分析失败: {e}")
        
        return recommendations


if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("索引优化器测试")
    print("=" * 50)
    
    optimizer = IndexOptimizer()
    
    # 分析索引
    stats = optimizer.analyze()
    print(f"\n索引统计:")
    print(f"  文档数: {stats.total_documents}")
    print(f"  碎片率: {stats.fragmentation_ratio:.2%}")
    
    # 获取建议
    print("\n优化建议:")
    for rec in optimizer.get_recommendations():
        print(f"  - {rec}")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
