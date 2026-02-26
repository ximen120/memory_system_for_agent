"""
API路由统一入口

整合所有API端点，提供统一的访问接口。
"""

import logging
from typing import Dict, Any, Optional

from .vector_api import VectorAPI
from .hybrid_api import HybridAPI
from .keyword_api import KeywordAPI
from .memory_api import MemoryAPI

logger = logging.getLogger(__name__)


class APIRouter:
    """
    API路由统一入口
    
    整合所有API端点，提供统一的访问接口。
    
    使用示例：
        >>> router = APIRouter()
        >>> 
        >>> # 向量搜索
        >>> response = router.route("/search/vector", {
        ...     "query": "咖啡",
        ...     "top_k": 10
        ... })
        >>> 
        >>> # 混合搜索
        >>> response = router.route("/search/hybrid", {
        ...     "query": "Python",
        ...     "top_k": 10
        ... })
    """
    
    def __init__(
        self,
        vector_api: Optional[VectorAPI] = None,
        hybrid_api: Optional[HybridAPI] = None,
        keyword_api: Optional[KeywordAPI] = None,
        memory_api: Optional[MemoryAPI] = None
    ):
        """
        初始化API路由
        
        Args:
            vector_api: 向量检索API（可选）
            hybrid_api: 混合检索API（可选）
            keyword_api: 关键词检索API（可选）
            memory_api: 记忆API（可选）
        """
        self.vector_api = vector_api or VectorAPI()
        self.hybrid_api = hybrid_api or HybridAPI()
        self.keyword_api = keyword_api or KeywordAPI()
        self.memory_api = memory_api or MemoryAPI()
        
        # 定义路由映射
        self._routes = {
            # 向量检索
            "/api/v1/search/vector": self._handle_vector_search,
            "/api/v1/embed": self._handle_embed,
            "/api/v1/embed/batch": self._handle_batch_embed,
            
            # 混合检索
            "/api/v1/search/hybrid": self._handle_hybrid_search,
            "/api/v1/search/weights": self._handle_weights,
            
            # 关键词检索
            "/api/v1/search/keyword": self._handle_keyword_search,
            
            # 记忆管理
            "/api/v1/memory/add": self._handle_memory_add,
            "/api/v1/memory/search": self._handle_memory_search,
            "/api/v1/memory/get": self._handle_memory_get,
            "/api/v1/memory/delete": self._handle_memory_delete,
            "/api/v1/memory/update": self._handle_memory_update,
            "/api/v1/memory/list": self._handle_memory_list,
            
            # 统计信息
            "/api/v1/stats": self._handle_stats,
        }
        
        logger.info("API路由初始化完成")
    
    def route(self, path: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        路由请求到对应的处理器
        
        Args:
            path: API路径
            request_data: 请求数据
        
        Returns:
            响应数据
        """
        # 标准化路径
        path = path.rstrip("/")
        
        # 查找处理器
        handler = self._routes.get(path)
        
        if handler:
            try:
                return handler(request_data)
            except Exception as e:
                logger.error(f"处理请求失败 {path}: {e}")
                return {
                    "success": False,
                    "error": f"处理失败: {str(e)}"
                }
        else:
            return {
                "success": False,
                "error": f"未知路径: {path}",
                "available_paths": list(self._routes.keys())
            }
    
    def get_available_routes(self) -> Dict[str, str]:
        """
        获取所有可用路由
        
        Returns:
            路由信息字典
        """
        return {
            path: handler.__doc__ or "No description"
            for path, handler in self._routes.items()
        }
    
    # ========== 向量检索处理器 ==========
    
    def _handle_vector_search(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理向量搜索请求"""
        return self.vector_api.search(request_data)
    
    def _handle_embed(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理向量生成请求"""
        return self.vector_api.embed(request_data)
    
    def _handle_batch_embed(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理批量向量生成请求"""
        return self.vector_api.batch_embed(request_data)
    
    # ========== 混合检索处理器 ==========
    
    def _handle_hybrid_search(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理混合搜索请求"""
        return self.hybrid_api.search(request_data)
    
    def _handle_weights(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理权重配置请求"""
        method = request_data.get("method", "GET").upper()
        
        if method == "GET":
            return {
                "success": True,
                "weights": self.hybrid_api.get_search_weights()
            }
        elif method == "POST":
            return self.hybrid_api.set_search_weights(
                vector_weight=request_data.get("vector_weight"),
                keyword_weight=request_data.get("keyword_weight")
            )
        else:
            return {
                "success": False,
                "error": f"不支持的HTTP方法: {method}"
            }
    
    # ========== 关键词检索处理器 ==========
    
    def _handle_keyword_search(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理关键词搜索请求"""
        return self.keyword_api.search(request_data)
    
    # ========== 记忆管理处理器 ==========
    
    def _handle_memory_add(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理添加记忆请求"""
        try:
            memory_id = self.memory_api.add_memory(
                content=request_data["content"],
                memory_type=request_data.get("memory_type", "fact"),
                importance=request_data.get("importance", 3.0),
                tags=request_data.get("tags"),
                **{k: v for k, v in request_data.items() 
                   if k not in ["content", "memory_type", "importance", "tags"]}
            )
            
            # 同时添加到关键词API
            self.keyword_api.add_document(
                memory_id=memory_id,
                content=request_data["content"],
                memory_type=request_data.get("memory_type", "fact"),
                importance=request_data.get("importance", 3.0),
                tags=request_data.get("tags")
            )
            
            return {
                "success": True,
                "memory_id": memory_id
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"添加失败: {str(e)}"
            }
    
    def _handle_memory_search(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理记忆搜索请求"""
        try:
            results = self.memory_api.search(
                query=request_data["query"],
                search_type=request_data.get("search_type", "hybrid"),
                top_k=request_data.get("top_k", 10),
                min_score=request_data.get("min_score", 0.05),
                filters=request_data.get("filters")
            )
            
            return {
                "success": True,
                "results": [
                    {
                        "memory_id": r.memory_id,
                        "content": r.content,
                        "score": r.score,
                        "memory_type": r.memory_type,
                        "created_at": r.created_at,
                        "tags": r.tags,
                        "search_method": r.search_method
                    }
                    for r in results
                ],
                "total": len(results)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"搜索失败: {str(e)}"
            }
    
    def _handle_memory_get(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取记忆请求"""
        try:
            memory_id = request_data.get("memory_id")
            if not memory_id:
                return {
                    "success": False,
                    "error": "缺少memory_id参数"
                }
            
            memory = self.memory_api.get_memory(memory_id)
            
            if memory:
                return {
                    "success": True,
                    "memory": {
                        "memory_id": memory.memory_id,
                        "content": memory.content,
                        "memory_type": memory.memory_type,
                        "importance": memory.importance,
                        "tags": memory.tags,
                        "created_at": memory.created_at,
                        "updated_at": memory.updated_at,
                        "metadata": memory.metadata
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "记忆不存在"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"获取失败: {str(e)}"
            }
    
    def _handle_memory_delete(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理删除记忆请求"""
        try:
            memory_id = request_data.get("memory_id")
            if not memory_id:
                return {
                    "success": False,
                    "error": "缺少memory_id参数"
                }
            
            success = self.memory_api.delete_memory(memory_id)
            
            # 同时从关键词API删除
            if success:
                self.keyword_api.delete_document(memory_id)
            
            return {
                "success": success,
                "message": "删除成功" if success else "记忆不存在"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"删除失败: {str(e)}"
            }
    
    def _handle_memory_update(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理更新记忆请求"""
        try:
            memory_id = request_data.get("memory_id")
            if not memory_id:
                return {
                    "success": False,
                    "error": "缺少memory_id参数"
                }
            
            # 提取更新字段
            updates = {k: v for k, v in request_data.items() 
                      if k != "memory_id"}
            
            success = self.memory_api.update_memory(memory_id, **updates)
            
            return {
                "success": success,
                "message": "更新成功" if success else "记忆不存在"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"更新失败: {str(e)}"
            }
    
    def _handle_memory_list(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理列出记忆请求"""
        try:
            memories = self.memory_api.list_memories(
                memory_type=request_data.get("memory_type"),
                limit=request_data.get("limit", 100),
                offset=request_data.get("offset", 0)
            )
            
            return {
                "success": True,
                "memories": [
                    {
                        "memory_id": m.memory_id,
                        "content": m.content,
                        "memory_type": m.memory_type,
                        "importance": m.importance,
                        "tags": m.tags,
                        "created_at": m.created_at
                    }
                    for m in memories
                ],
                "total": len(memories)
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"列出失败: {str(e)}"
            }
    
    # ========== 统计信息处理器 ==========
    
    def _handle_stats(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理统计信息请求"""
        return {
            "success": True,
            "stats": {
                "memory_api": self.memory_api.get_stats(),
                "vector_api": self.vector_api.get_stats(),
                "hybrid_api": self.hybrid_api.get_stats(),
                "keyword_api": self.keyword_api.get_stats()
            }
        }


# 全局路由实例
_router_instance: Optional[APIRouter] = None


def get_router() -> APIRouter:
    """获取全局路由实例（单例模式）"""
    global _router_instance
    if _router_instance is None:
        _router_instance = APIRouter()
    return _router_instance


def reset_router() -> None:
    """重置全局路由实例（用于测试）"""
    global _router_instance
    _router_instance = None
