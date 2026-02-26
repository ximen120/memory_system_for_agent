"""
混合检索引擎

结合向量检索和关键词检索的优势，使用RRF算法融合结果。
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

try:
    from .vector_search import VectorSearch, VectorSearchResult
    from .keyword_search import KeywordSearch, KeywordSearchResult
except ImportError:
    from vector_search import VectorSearch, VectorSearchResult
    from keyword_search import KeywordSearch, KeywordSearchResult

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    """混合搜索结果"""
    memory_id: str
    content: str
    score: float  # 融合分数
    vector_score: Optional[float]  # 向量检索分数
    keyword_score: Optional[float]  # 关键词检索分数
    vector_rank: Optional[int]  # 向量检索排名
    keyword_rank: Optional[int]  # 关键词检索排名
    memory_type: str
    created_at: str
    metadata: Dict[str, Any]


class HybridSearch:
    """
    混合检索引擎
    
    结合向量检索和关键词检索的优势，使用RRF (Reciprocal Rank Fusion)算法融合结果。
    
    RRF公式: score = Σ(weight_i / (k + rank_i))
    其中 k=60 是常数，rank是排名（从0开始）
    
    使用示例：
        >>> from retrieval import HybridSearch, VectorSearch, KeywordSearch
        >>> 
        >>> vector_search = VectorSearch(embedding_service)
        >>> keyword_search = KeywordSearch()
        >>> hybrid = HybridSearch(vector_search, keyword_search)
        >>> 
        >>> results = hybrid.search("查询文本")
    """
    
    def __init__(
        self,
        vector_search: VectorSearch,
        keyword_search: Optional[KeywordSearch] = None,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        rrf_k: int = 60
    ):
        """
        初始化混合检索引擎
        
        Args:
            vector_search: 向量检索引擎
            keyword_search: 关键词检索引擎（可选）
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
            rrf_k: RRF算法常数
        """
        self.vector_search = vector_search
        self.keyword_search = keyword_search or KeywordSearch()
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
        self.rrf_k = rrf_k
        
        logger.info(
            f"混合检索引擎初始化: "
            f"vector_weight={vector_weight}, "
            f"keyword_weight={keyword_weight}, "
            f"rrf_k={rrf_k}"
        )
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.1,
        use_vector: bool = True,
        use_keyword: bool = True
    ) -> List[HybridSearchResult]:
        """
        混合搜索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            min_score: 最小融合分数
            use_vector: 是否使用向量检索
            use_keyword: 是否使用关键词检索
            
        Returns:
            混合搜索结果列表
        """
        if not query or not query.strip():
            logger.warning("查询文本为空")
            return []
        
        try:
            # 执行向量检索
            vector_results = []
            if use_vector:
                vector_results = self.vector_search.search(
                    query=query,
                    top_k=top_k * 2,  # 多取一些用于融合
                    min_similarity=0.0  # 不过滤，让融合算法决定
                )
            
            # 执行关键词检索
            keyword_results = []
            if use_keyword and self.keyword_search:
                keyword_results = self.keyword_search.search(
                    query=query,
                    top_k=top_k * 2,
                    min_score=0.0
                )
            
            # 融合结果
            fused_results = self._fuse_results(
                vector_results,
                keyword_results,
                top_k=top_k,
                min_score=min_score
            )
            
            logger.info(f"混合搜索完成: 返回{len(fused_results)}条结果")
            return fused_results
            
        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            return []
    
    def _fuse_results(
        self,
        vector_results: List[VectorSearchResult],
        keyword_results: List[KeywordSearchResult],
        top_k: int,
        min_score: float
    ) -> List[HybridSearchResult]:
        """
        使用RRF算法融合结果
        
        Args:
            vector_results: 向量检索结果
            keyword_results: 关键词检索结果
            top_k: 返回数量
            min_score: 最小分数
            
        Returns:
            融合后的结果列表
        """
        # 构建ID到排名的映射
        vector_ranks = {r.memory_id: i for i, r in enumerate(vector_results)}
        keyword_ranks = {r.memory_id: i for i, r in enumerate(keyword_results)}
        
        # 收集所有文档ID
        all_ids = set(vector_ranks.keys()) | set(keyword_ranks.keys())
        
        # 计算RRF分数
        fused_scores = {}
        for memory_id in all_ids:
            score = 0.0
            vector_rank = None
            keyword_rank = None
            vector_score = None
            keyword_score = None
            
            # 向量检索分数
            if memory_id in vector_ranks:
                vector_rank = vector_ranks[memory_id]
                vector_score = vector_results[vector_rank].score
                score += self.vector_weight / (self.rrf_k + vector_rank)
            
            # 关键词检索分数
            if memory_id in keyword_ranks:
                keyword_rank = keyword_ranks[memory_id]
                keyword_score = keyword_results[keyword_rank].score
                score += self.keyword_weight / (self.rrf_k + keyword_rank)
            
            fused_scores[memory_id] = {
                'score': score,
                'vector_rank': vector_rank,
                'keyword_rank': keyword_rank,
                'vector_score': vector_score,
                'keyword_score': keyword_score
            }
        
        # 过滤并排序
        filtered_results = [
            (mid, data) for mid, data in fused_scores.items()
            if data['score'] >= min_score
        ]
        filtered_results.sort(key=lambda x: x[1]['score'], reverse=True)
        
        # 构建结果对象
        results = []
        for memory_id, data in filtered_results[:top_k]:
            # 获取文档内容（优先从vector_results）
            content = ""
            memory_type = "unknown"
            created_at = ""
            metadata = {}
            
            if memory_id in vector_ranks:
                vec_result = vector_results[vector_ranks[memory_id]]
                content = vec_result.content
                memory_type = vec_result.memory_type
                created_at = vec_result.created_at
                metadata = vec_result.metadata
            elif memory_id in keyword_ranks:
                key_result = keyword_results[keyword_ranks[memory_id]]
                content = key_result.content
                memory_type = key_result.memory_type
                created_at = key_result.created_at
                metadata = key_result.metadata
            
            results.append(HybridSearchResult(
                memory_id=memory_id,
                content=content,
                score=data['score'],
                vector_score=data['vector_score'],
                keyword_score=data['keyword_score'],
                vector_rank=data['vector_rank'],
                keyword_rank=data['keyword_rank'],
                memory_type=memory_type,
                created_at=created_at,
                metadata=metadata
            ))
        
        return results
    
    def add_document(
        self,
        memory_id: str,
        content: str,
        embedding: Optional[List[float]] = None,
        memory_type: str = "fact",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加文档到索引
        
        Args:
            memory_id: 记忆ID
            content: 文档内容
            embedding: 向量（可选）
            memory_type: 记忆类型
            metadata: 元数据
            
        Returns:
            是否成功
        """
        success = True
        
        # 添加到向量检索
        if embedding:
            try:
                self.vector_search.add_document(
                    memory_id=memory_id,
                    content=content,
                    embedding=embedding,
                    memory_type=memory_type,
                    metadata=metadata
                )
            except Exception as e:
                logger.warning(f"添加到向量检索失败: {e}")
                success = False
        
        # 添加到关键词检索
        try:
            self.keyword_search.add_document(
                memory_id=memory_id,
                content=content,
                memory_type=memory_type,
                metadata=metadata
            )
        except Exception as e:
            logger.warning(f"添加到关键词检索失败: {e}")
            success = False
        
        return success
    
    def remove_document(self, memory_id: str) -> bool:
        """
        从索引中移除文档
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否成功
        """
        success = True
        
        # 从向量检索移除
        try:
            self.vector_search.remove_document(memory_id)
        except Exception as e:
            logger.warning(f"从向量检索移除失败: {e}")
            success = False
        
        # 从关键词检索移除
        try:
            self.keyword_search.remove_document(memory_id)
        except Exception as e:
            logger.warning(f"从关键词检索移除失败: {e}")
            success = False
        
        return success
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'vector_search': self.vector_search.get_stats(),
            'keyword_search': self.keyword_search.get_stats() if self.keyword_search else None,
            'vector_weight': self.vector_weight,
            'keyword_weight': self.keyword_weight,
            'rrf_k': self.rrf_k
        }


# 便捷函数
def create_hybrid_search(
    storage_path: str = "./data/vector_db",
    collection_name: str = "memories",
    model_name: str = "all-MiniLM-L6-v2",
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3
) -> HybridSearch:
    """
    创建混合检索引擎（便捷函数）
    
    Args:
        storage_path: 存储路径
        collection_name: 集合名称
        model_name: Embedding模型名称
        vector_weight: 向量检索权重
        keyword_weight: 关键词检索权重
        
    Returns:
        HybridSearch实例
    """
    import sys
    from pathlib import Path
    
    # 添加必要的路径
    base_path = Path(__file__).parent.parent
    sys.path.insert(0, str(base_path / "storage"))
    sys.path.insert(0, str(base_path / "core"))
    
    from chroma_storage import ChromaStorage
    from embedding_service import EmbeddingService
    
    # 创建服务
    embedding_service = EmbeddingService(model_name=model_name)
    storage = ChromaStorage(storage_path, collection_name)
    vector_search = VectorSearch(embedding_service, storage, collection_name)
    keyword_search = KeywordSearch()
    
    return HybridSearch(
        vector_search=vector_search,
        keyword_search=keyword_search,
        vector_weight=vector_weight,
        keyword_weight=keyword_weight
    )


if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("混合检索引擎测试")
    print("=" * 50)
    
    # 创建服务
    from embedding_service import EmbeddingService
    from vector_search import VectorSearch
    
    embedding_service = EmbeddingService()
    vector_search = VectorSearch(embedding_service)
    keyword_search = KeywordSearch()
    
    hybrid = HybridSearch(
        vector_search=vector_search,
        keyword_search=keyword_search,
        vector_weight=0.7,
        keyword_weight=0.3
    )
    
    print(f"\n统计信息: {hybrid.get_stats()}")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
