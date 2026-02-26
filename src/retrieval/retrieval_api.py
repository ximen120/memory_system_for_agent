"""
向量检索API封装

提供统一的检索接口，整合向量检索、关键词检索和混合检索。

使用示例：
    >>> from retrieval import RetrievalAPI
    >>> 
    >>> # 创建API实例
    >>> api = RetrievalAPI.create_default("./data", "memories")
    >>> 
    >>> # 向量搜索
    >>> results = api.vector_search("查询文本", top_k=10)
    >>> 
    >>> # 混合搜索
    >>> results = api.hybrid_search("查询文本", top_k=10)
"""

import logging
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum

try:
    from .embedding_service import EmbeddingService
    from .vector_search import VectorSearch, VectorSearchResult
    from .hybrid_search import HybridSearch, HybridSearchResult
except ImportError:
    from embedding_service import EmbeddingService
    from vector_search import VectorSearch, VectorSearchResult
    from hybrid_search import HybridSearch, HybridSearchResult

# 配置日志
logger = logging.getLogger(__name__)


class SearchMode(Enum):
    """搜索模式"""
    VECTOR = "vector"      # 纯向量检索
    KEYWORD = "keyword"    # 纯关键词检索
    HYBRID = "hybrid"      # 混合检索


@dataclass
class SearchRequest:
    """搜索请求"""
    query: str
    mode: SearchMode = SearchMode.HYBRID
    top_k: int = 10
    min_score: float = 0.7
    filters: Optional[Dict[str, Any]] = None
    memory_types: Optional[List[str]] = None
    tags: Optional[List[str]] = None


@dataclass
class SearchResponse:
    """搜索响应"""
    results: List[Union[VectorSearchResult, HybridSearchResult]]
    total: int
    query: str
    mode: SearchMode
    search_time_ms: float


class RetrievalAPI:
    """
    检索API封装
    
    提供统一的检索接口，整合多种检索方式。
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_search: VectorSearch,
        hybrid_search: Optional[HybridSearch] = None
    ):
        """
        初始化检索API
        
        Args:
            embedding_service: Embedding服务
            vector_search: 向量检索引擎
            hybrid_search: 混合检索引擎（可选）
        """
        self.embedding_service = embedding_service
        self._vector_search = vector_search
        self._hybrid_search = hybrid_search
        
        # 提供便捷的访问方式
        self.vector_search_engine = vector_search
        self.hybrid_search_engine = hybrid_search
        
        logger.info("检索API初始化完成")
        
        logger.info("检索API初始化完成")
    
    @classmethod
    def create_default(
        cls,
        storage_path: str = "./data/vector_db",
        collection_name: str = "memories",
        model_name: str = "all-MiniLM-L6-v2"
    ) -> "RetrievalAPI":
        """
        创建默认配置的检索API
        
        Args:
            storage_path: 存储路径
            collection_name: 集合名称
            model_name: Embedding模型名称
            
        Returns:
            RetrievalAPI实例
        """
        import sys
        from pathlib import Path
        
        # 添加必要的路径
        base_path = Path(__file__).parent.parent
        sys.path.insert(0, str(base_path / "storage"))
        sys.path.insert(0, str(base_path / "core"))
        
        from chroma_storage import ChromaStorage
        
        # 创建服务
        embedding_service = EmbeddingService(model_name=model_name)
        storage = ChromaStorage(storage_path, collection_name)
        vector_search = VectorSearch(embedding_service, storage, collection_name)
        
        # 创建混合检索（如果有关键词检索）
        hybrid_search = None
        try:
            hybrid_search = HybridSearch(vector_search)
        except Exception as e:
            logger.warning(f"混合检索初始化失败: {e}")
        
        return cls(embedding_service, vector_search, hybrid_search)
    
    def search(self, request: SearchRequest) -> SearchResponse:
        """
        统一搜索接口
        
        Args:
            request: 搜索请求
            
        Returns:
            搜索响应
        """
        import time
        
        start_time = time.time()
        
        if request.mode == SearchMode.VECTOR:
            results = self._vector_search.search(
                query=request.query,
                top_k=request.top_k,
                min_similarity=request.min_score,
                filters=request.filters
            )
        elif request.mode == SearchMode.HYBRID and self._hybrid_search:
            results = self._hybrid_search.search(
                query=request.query,
                top_k=request.top_k,
                min_score=request.min_score
            )
        else:
            # 默认使用向量搜索
            results = self._vector_search.search(
                query=request.query,
                top_k=request.top_k,
                min_similarity=request.min_score,
                filters=request.filters
            )
        
        search_time_ms = (time.time() - start_time) * 1000
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=request.query,
            mode=request.mode,
            search_time_ms=search_time_ms
        )
    
    def vector_search(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> SearchResponse:
        """
        向量搜索（便捷方法）
        
        Args:
            query: 查询文本
            top_k: 返回数量
            min_similarity: 最小相似度
            filters: 过滤条件
            
        Returns:
            搜索结果
        """
        request = SearchRequest(
            query=query,
            mode=SearchMode.VECTOR,
            top_k=top_k,
            min_score=min_similarity,
            filters=filters
        )
        return self.search(request)
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.7
    ) -> SearchResponse:
        """
        混合搜索（便捷方法）
        
        Args:
            query: 查询文本
            top_k: 返回数量
            min_score: 最小分数
            
        Returns:
            搜索结果
        """
        request = SearchRequest(
            query=query,
            mode=SearchMode.HYBRID,
            top_k=top_k,
            min_score=min_score
        )
        return self.search(request)
    
    def add_memory(
        self,
        content: str,
        memory_type: str = "fact",
        tags: Optional[List[str]] = None,
        importance: float = 3.0,
        source: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        添加记忆到索引
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            tags: 标签列表
            importance: 重要度
            source: 来源
            metadata: 额外元数据
            
        Returns:
            记忆ID，失败返回None
        """
        try:
            # 生成向量
            embedding = self.embedding_service.generate(content)
            if embedding is None:
                logger.error("生成向量失败")
                return None
            
            # 创建完整元数据
            full_metadata = {
                'tags': tags or [],
                'importance': importance,
                'source': source,
                **(metadata or {})
            }
            
            # 添加到向量搜索
            import uuid
            memory_id = f"mem_{uuid.uuid4().hex[:16]}"
            
            success = self._vector_search.add_document(
                memory_id=memory_id,
                content=content,
                embedding=embedding,
                memory_type=memory_type,
                metadata=full_metadata
            )
            
            if success:
                logger.info(f"记忆已添加: {memory_id}")
                return memory_id
            else:
                return None
                
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            return None
    
    def remove_memory(self, memory_id: str) -> bool:
        """
        移除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否成功
        """
        return self._vector_search.remove_document(memory_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        return {
            'vector_search': self._vector_search.get_stats(),
            'embedding_service': {
                'model_name': self.embedding_service.config.model_name,
                'is_loaded': self.embedding_service._is_loaded
            }
        }


# 便捷函数
def quick_search(
    query: str,
    storage_path: str = "./data/vector_db",
    top_k: int = 10
) -> SearchResponse:
    """
    快速搜索（无需预先创建API实例）
    
    Args:
        query: 查询文本
        storage_path: 存储路径
        top_k: 返回数量
        
    Returns:
        搜索结果
    """
    api = RetrievalAPI.create_default(storage_path)
    return api.vector_search(query, top_k=top_k)


if __name__ == "__main__":
    # 测试代码
    print("检索API测试")
    
    # 创建API实例
    api = RetrievalAPI.create_default("./test_data", "test_memories")
    
    print(f"统计信息: {api.get_stats()}")
    
    # 添加测试记忆
    memory_id = api.add_memory(
        content="我喜欢喝咖啡",
        memory_type="preference",
        tags=["饮食", "偏好"],
        importance=4.0
    )
    print(f"添加记忆: {memory_id}")
    
    # 搜索
    if memory_id:
        response = api.vector_search("咖啡", top_k=5)
        print(f"搜索结果: {response.total}条")
        for result in response.results:
            print(f"  - {result.content[:30]}... (score: {result.score:.3f})")
    
    print("\n测试完成!")
