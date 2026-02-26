"""
混合检索API

提供混合检索（向量+关键词）的RESTful API端点。
"""

import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from retrieval import EmbeddingService, VectorSearch, HybridSearch

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchRequest:
    """混合搜索请求"""
    query: str
    top_k: int = 10
    min_score: float = 0.05
    vector_weight: float = 0.7
    keyword_weight: float = 0.3
    use_vector: bool = True
    use_keyword: bool = True
    filters: Optional[Dict[str, Any]] = None


@dataclass
class HybridSearchResponse:
    """混合搜索响应"""
    success: bool
    results: List[Dict[str, Any]]
    total: int
    time_ms: float
    query: str
    search_method: str  # "hybrid" | "vector_only" | "keyword_only"
    error: Optional[str] = None


class HybridAPI:
    """
    混合检索API
    
    提供向量+关键词混合搜索功能。
    
    使用示例：
        >>> api = HybridAPI()
        >>> response = api.search({
        ...     "query": "咖啡",
        ...     "top_k": 10,
        ...     "vector_weight": 0.7
        ... })
    """
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_search: Optional[VectorSearch] = None,
        hybrid_search: Optional[HybridSearch] = None
    ):
        """
        初始化混合检索API
        
        Args:
            embedding_service: Embedding服务（可选）
            vector_search: 向量检索引擎（可选）
            hybrid_search: 混合检索引擎（可选）
        """
        self.embedding_service = embedding_service or EmbeddingService()
        
        if vector_search:
            self.vector_search = vector_search
        else:
            self.vector_search = VectorSearch(self.embedding_service)
        
        if hybrid_search:
            self.hybrid_search = hybrid_search
        else:
            self.hybrid_search = HybridSearch(self.vector_search)
        
        logger.info("混合检索API初始化完成")
    
    def search(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        混合搜索
        
        Args:
            request_data: 请求数据
                - query: 查询文本（必需）
                - top_k: 返回数量（默认10）
                - min_score: 最小融合分数（默认0.05）
                - vector_weight: 向量检索权重（默认0.7）
                - keyword_weight: 关键词检索权重（默认0.3）
                - use_vector: 是否使用向量检索（默认True）
                - use_keyword: 是否使用关键词检索（默认True）
                - filters: 过滤条件（可选）
        
        Returns:
            响应数据
                - success: 是否成功
                - results: 搜索结果列表
                - total: 结果数量
                - time_ms: 耗时（毫秒）
                - query: 查询文本
                - search_method: 实际使用的搜索方法
                - error: 错误信息（如有）
        
        示例：
            >>> request = {
            ...     "query": "Python编程",
            ...     "top_k": 10,
            ...     "vector_weight": 0.8
            ... }
            >>> response = api.search(request)
            >>> print(response["total"])
        """
        start_time = time.time()
        
        try:
            # 1. 验证请求
            validation_error = self._validate_search_request(request_data)
            if validation_error:
                return self._error_response(
                    query=request_data.get("query", ""),
                    error=validation_error,
                    start_time=start_time
                )
            
            # 2. 解析请求
            query = request_data["query"]
            top_k = request_data.get("top_k", 10)
            min_score = request_data.get("min_score", 0.05)
            use_vector = request_data.get("use_vector", True)
            use_keyword = request_data.get("use_keyword", True)
            filters = request_data.get("filters")
            
            # 3. 动态调整权重（如果提供）
            vector_weight = request_data.get("vector_weight")
            keyword_weight = request_data.get("keyword_weight")
            
            if vector_weight is not None:
                self.hybrid_search.vector_weight = vector_weight
            if keyword_weight is not None:
                self.hybrid_search.keyword_weight = keyword_weight
            
            # 4. 确定搜索方法
            embedding_available = self.embedding_service.is_available()
            
            if not embedding_available and use_vector:
                # Embedding不可用，降级到关键词
                use_vector = False
                use_keyword = True
                search_method = "keyword_only"
            elif not use_vector and use_keyword:
                search_method = "keyword_only"
            elif use_vector and not use_keyword:
                search_method = "vector_only"
            else:
                search_method = "hybrid"
            
            # 5. 执行搜索
            results = self.hybrid_search.search(
                query=query,
                top_k=top_k,
                min_score=min_score,
                use_vector=use_vector,
                use_keyword=use_keyword,
                filters=filters
            )
            
            # 6. 构建响应
            result_dicts = [
                {
                    "memory_id": r.memory_id,
                    "content": r.content,
                    "score": r.score,
                    "vector_score": r.vector_score,
                    "keyword_score": r.keyword_score,
                    "vector_rank": r.vector_rank,
                    "keyword_rank": r.keyword_rank,
                    "memory_type": r.memory_type,
                    "created_at": r.created_at,
                    "metadata": r.metadata
                }
                for r in results
            ]
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            response = HybridSearchResponse(
                success=True,
                results=result_dicts,
                total=len(result_dicts),
                time_ms=round(elapsed_ms, 2),
                query=query,
                search_method=search_method
            )
            
            logger.info(
                f"混合搜索完成: '{query}' 方法={search_method} "
                f"找到 {len(results)} 条结果"
            )
            
            return asdict(response)
            
        except Exception as e:
            logger.error(f"混合搜索失败: {e}")
            return self._error_response(
                query=request_data.get("query", ""),
                error=f"搜索失败: {str(e)}",
                start_time=start_time
            )
    
    def search_with_fallback(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        带降级方案的搜索
        
        如果向量检索不可用，自动降级到关键词检索。
        
        Args:
            request_data: 请求数据（同search方法）
        
        Returns:
            响应数据
        """
        # 强制启用降级
        request_data["fallback"] = True
        return self.search(request_data)
    
    def get_search_weights(self) -> Dict[str, Any]:
        """
        获取当前搜索权重配置
        
        Returns:
            权重配置
        """
        return {
            "vector_weight": self.hybrid_search.vector_weight,
            "keyword_weight": self.hybrid_search.keyword_weight,
            "rrf_k": self.hybrid_search.rrf_k
        }
    
    def set_search_weights(
        self,
        vector_weight: Optional[float] = None,
        keyword_weight: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        设置搜索权重
        
        Args:
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
        
        Returns:
            更新后的权重配置
        """
        if vector_weight is not None:
            if 0 <= vector_weight <= 1:
                self.hybrid_search.vector_weight = vector_weight
            else:
                return {
                    "success": False,
                    "error": "vector_weight必须在0-1之间"
                }
        
        if keyword_weight is not None:
            if 0 <= keyword_weight <= 1:
                self.hybrid_search.keyword_weight = keyword_weight
            else:
                return {
                    "success": False,
                    "error": "keyword_weight必须在0-1之间"
                }
        
        return {
            "success": True,
            "weights": self.get_search_weights()
        }
    
    def _validate_search_request(self, request_data: Dict[str, Any]) -> Optional[str]:
        """验证搜索请求"""
        if not isinstance(request_data, dict):
            return "请求必须是JSON对象"
        
        if "query" not in request_data:
            return "缺少必需参数: query"
        
        query = request_data.get("query", "").strip()
        if not query:
            return "查询文本不能为空"
        
        top_k = request_data.get("top_k", 10)
        if not isinstance(top_k, int) or top_k < 1 or top_k > 100:
            return "top_k必须是1-100之间的整数"
        
        min_score = request_data.get("min_score", 0.05)
        if not isinstance(min_score, (int, float)):
            return "min_score必须是数字"
        if min_score < 0 or min_score > 1:
            return "min_score必须在0-1之间"
        
        # 验证权重
        vector_weight = request_data.get("vector_weight")
        if vector_weight is not None:
            if not isinstance(vector_weight, (int, float)):
                return "vector_weight必须是数字"
            if vector_weight < 0 or vector_weight > 1:
                return "vector_weight必须在0-1之间"
        
        keyword_weight = request_data.get("keyword_weight")
        if keyword_weight is not None:
            if not isinstance(keyword_weight, (int, float)):
                return "keyword_weight必须是数字"
            if keyword_weight < 0 or keyword_weight > 1:
                return "keyword_weight必须在0-1之间"
        
        return None
    
    def _error_response(
        self,
        query: str,
        error: str,
        start_time: float
    ) -> Dict[str, Any]:
        """构建错误响应"""
        elapsed_ms = (time.time() - start_time) * 1000
        
        return {
            "success": False,
            "results": [],
            "total": 0,
            "time_ms": round(elapsed_ms, 2),
            "query": query,
            "search_method": "none",
            "error": error
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取API统计信息"""
        return {
            "embedding_available": self.embedding_service.is_available(),
            "document_count": self.vector_search.count(),
            "weights": self.get_search_weights()
        }
