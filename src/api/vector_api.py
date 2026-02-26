"""
向量检索API

提供向量相似度搜索的RESTful API端点。
"""

import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from retrieval import EmbeddingService, VectorSearch

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchRequest:
    """向量搜索请求"""
    query: str
    top_k: int = 10
    min_similarity: float = 0.7
    filters: Optional[Dict[str, Any]] = None


@dataclass
class VectorSearchResponse:
    """向量搜索响应"""
    success: bool
    results: List[Dict[str, Any]]
    total: int
    time_ms: float
    query: str
    error: Optional[str] = None


class VectorAPI:
    """
    向量检索API
    
    提供向量相似度搜索功能。
    
    使用示例：
        >>> api = VectorAPI()
        >>> response = api.search({
        ...     "query": "咖啡",
        ...     "top_k": 5,
        ...     "min_similarity": 0.7
        ... })
    """
    
    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_search: Optional[VectorSearch] = None
    ):
        """
        初始化向量检索API
        
        Args:
            embedding_service: Embedding服务（可选）
            vector_search: 向量检索引擎（可选）
        """
        self.embedding_service = embedding_service or EmbeddingService()
        self.vector_search = vector_search or VectorSearch(self.embedding_service)
        
        logger.info("向量检索API初始化完成")
    
    def search(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        向量相似度搜索
        
        Args:
            request_data: 请求数据
                - query: 查询文本（必需）
                - top_k: 返回数量（默认10）
                - min_similarity: 最小相似度（默认0.7）
                - filters: 过滤条件（可选）
                    - memory_type: 记忆类型
                    - tags: 标签列表
                    - min_importance: 最小重要性
        
        Returns:
            响应数据
                - success: 是否成功
                - results: 搜索结果列表
                - total: 结果数量
                - time_ms: 耗时（毫秒）
                - query: 查询文本
                - error: 错误信息（如有）
        
        示例：
            >>> request = {
            ...     "query": "咖啡",
            ...     "top_k": 5,
            ...     "min_similarity": 0.7
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
            min_similarity = request_data.get("min_similarity", 0.7)
            filters = request_data.get("filters")
            
            # 3. 检查Embedding服务
            if not self.embedding_service.is_available():
                return self._error_response(
                    query=query,
                    error="Embedding服务不可用",
                    start_time=start_time
                )
            
            # 4. 执行搜索
            results = self.vector_search.search(
                query=query,
                top_k=top_k,
                min_similarity=min_similarity,
                filters=filters
            )
            
            # 5. 构建响应
            result_dicts = [
                {
                    "memory_id": r.memory_id,
                    "content": r.content,
                    "score": r.score,
                    "memory_type": r.memory_type,
                    "created_at": r.created_at,
                    "metadata": r.metadata
                }
                for r in results
            ]
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            response = VectorSearchResponse(
                success=True,
                results=result_dicts,
                total=len(result_dicts),
                time_ms=round(elapsed_ms, 2),
                query=query
            )
            
            logger.info(f"向量搜索完成: '{query}' 找到 {len(results)} 条结果")
            
            return asdict(response)
            
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return self._error_response(
                query=request_data.get("query", ""),
                error=f"搜索失败: {str(e)}",
                start_time=start_time
            )
    
    def embed(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成文本的embedding向量
        
        Args:
            request_data: 请求数据
                - text: 输入文本（必需）
        
        Returns:
            响应数据
                - success: 是否成功
                - embedding: 向量列表
                - dimension: 向量维度
                - time_ms: 耗时（毫秒）
                - error: 错误信息（如有）
        
        示例：
            >>> request = {"text": "测试文本"}
            >>> response = api.embed(request)
            >>> print(response["dimension"])
        """
        start_time = time.time()
        
        try:
            # 验证请求
            text = request_data.get("text", "").strip()
            if not text:
                return {
                    "success": False,
                    "error": "文本不能为空",
                    "time_ms": round((time.time() - start_time) * 1000, 2)
                }
            
            # 检查服务
            if not self.embedding_service.is_available():
                return {
                    "success": False,
                    "error": "Embedding服务不可用",
                    "time_ms": round((time.time() - start_time) * 1000, 2)
                }
            
            # 生成向量
            embedding = self.embedding_service.generate(text)
            
            if embedding is None:
                return {
                    "success": False,
                    "error": "向量生成失败",
                    "time_ms": round((time.time() - start_time) * 1000, 2)
                }
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "embedding": embedding,
                "dimension": len(embedding),
                "time_ms": round(elapsed_ms, 2)
            }
            
        except Exception as e:
            logger.error(f"向量生成失败: {e}")
            return {
                "success": False,
                "error": f"生成失败: {str(e)}",
                "time_ms": round((time.time() - start_time) * 1000, 2)
            }
    
    def batch_embed(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        批量生成embedding向量
        
        Args:
            request_data: 请求数据
                - texts: 文本列表（必需）
                - batch_size: 批处理大小（默认32）
        
        Returns:
            响应数据
                - success: 是否成功
                - embeddings: 向量列表
                - count: 成功数量
                - time_ms: 耗时（毫秒）
                - error: 错误信息（如有）
        """
        start_time = time.time()
        
        try:
            texts = request_data.get("texts", [])
            batch_size = request_data.get("batch_size", 32)
            
            if not texts:
                return {
                    "success": False,
                    "error": "文本列表不能为空",
                    "time_ms": round((time.time() - start_time) * 1000, 2)
                }
            
            if not self.embedding_service.is_available():
                return {
                    "success": False,
                    "error": "Embedding服务不可用",
                    "time_ms": round((time.time() - start_time) * 1000, 2)
                }
            
            # 批量生成
            embeddings = self.embedding_service.generate_batch(
                texts,
                batch_size=batch_size
            )
            
            success_count = sum(1 for e in embeddings if e is not None)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            return {
                "success": True,
                "embeddings": embeddings,
                "count": success_count,
                "total": len(texts),
                "time_ms": round(elapsed_ms, 2)
            }
            
        except Exception as e:
            logger.error(f"批量生成失败: {e}")
            return {
                "success": False,
                "error": f"批量生成失败: {str(e)}",
                "time_ms": round((time.time() - start_time) * 1000, 2)
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
        
        min_similarity = request_data.get("min_similarity", 0.7)
        if not isinstance(min_similarity, (int, float)):
            return "min_similarity必须是数字"
        if min_similarity < 0 or min_similarity > 1:
            return "min_similarity必须在0-1之间"
        
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
            "error": error
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取API统计信息"""
        return {
            "embedding_available": self.embedding_service.is_available(),
            "document_count": self.vector_search.count(),
            "embedding_model": self.embedding_service.config.model_name
        }
