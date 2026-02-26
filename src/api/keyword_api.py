"""
关键词检索API

提供关键词搜索的RESTful API端点。
"""

import time
import logging
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class KeywordSearchRequest:
    """关键词搜索请求"""
    query: str
    top_k: int = 10
    match_mode: str = "OR"  # "AND" | "OR"
    case_sensitive: bool = False
    filters: Optional[Dict[str, Any]] = None


@dataclass
class KeywordSearchResponse:
    """关键词搜索响应"""
    success: bool
    results: List[Dict[str, Any]]
    total: int
    time_ms: float
    query: str
    match_mode: str
    error: Optional[str] = None


class KeywordAPI:
    """
    关键词检索API
    
    提供关键词搜索功能，支持AND/OR匹配模式。
    
    使用示例：
        >>> api = KeywordAPI()
        >>> response = api.search({
        ...     "query": "咖啡 喜欢",
        ...     "match_mode": "AND",
        ...     "top_k": 10
        ... })
    """
    
    def __init__(self, documents: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        初始化关键词检索API
        
        Args:
            documents: 文档数据（可选）
        """
        # 内存中的文档存储
        self._documents: Dict[str, Dict[str, Any]] = documents or {}
        
        logger.info("关键词检索API初始化完成")
    
    def search(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        关键词搜索
        
        Args:
            request_data: 请求数据
                - query: 查询关键词（必需）
                - top_k: 返回数量（默认10）
                - match_mode: 匹配模式（默认OR）
                    - AND: 所有关键词都必须匹配
                    - OR: 任一关键词匹配即可
                - case_sensitive: 是否区分大小写（默认False）
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
                - match_mode: 匹配模式
                - error: 错误信息（如有）
        
        示例：
            >>> request = {
            ...     "query": "咖啡 喜欢",
            ...     "match_mode": "AND",
            ...     "top_k": 5
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
                    match_mode=request_data.get("match_mode", "OR"),
                    error=validation_error,
                    start_time=start_time
                )
            
            # 2. 解析请求
            query = request_data["query"]
            top_k = request_data.get("top_k", 10)
            match_mode = request_data.get("match_mode", "OR").upper()
            case_sensitive = request_data.get("case_sensitive", False)
            filters = request_data.get("filters")
            
            # 3. 提取关键词
            keywords = self._extract_keywords(query)
            if not keywords:
                return self._error_response(
                    query=query,
                    match_mode=match_mode,
                    error="无法提取有效关键词",
                    start_time=start_time
                )
            
            # 4. 执行搜索
            results = self._search_keywords(
                keywords=keywords,
                match_mode=match_mode,
                case_sensitive=case_sensitive,
                filters=filters
            )
            
            # 5. 排序并限制数量
            results.sort(key=lambda x: x["score"], reverse=True)
            results = results[:top_k]
            
            # 6. 构建响应
            elapsed_ms = (time.time() - start_time) * 1000
            
            response = KeywordSearchResponse(
                success=True,
                results=results,
                total=len(results),
                time_ms=round(elapsed_ms, 2),
                query=query,
                match_mode=match_mode
            )
            
            logger.info(
                f"关键词搜索完成: '{query}' 模式={match_mode} "
                f"找到 {len(results)} 条结果"
            )
            
            return asdict(response)
            
        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            return self._error_response(
                query=request_data.get("query", ""),
                match_mode=request_data.get("match_mode", "OR"),
                error=f"搜索失败: {str(e)}",
                start_time=start_time
            )
    
    def _extract_keywords(self, query: str) -> List[str]:
        """
        从查询中提取关键词
        
        Args:
            query: 查询文本
        
        Returns:
            关键词列表
        """
        # 分词（简化版，按空格和标点分割）
        keywords = re.findall(r'\b\w+\b', query)
        
        # 过滤停用词和短词
        stop_words = {'的', '了', '是', '在', '和', '或', '与', 'the', 'a', 'an', 'is', 'are'}
        keywords = [kw for kw in keywords if len(kw) > 1 and kw.lower() not in stop_words]
        
        return keywords
    
    def _search_keywords(
        self,
        keywords: List[str],
        match_mode: str,
        case_sensitive: bool,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        执行关键词搜索
        
        Args:
            keywords: 关键词列表
            match_mode: 匹配模式
            case_sensitive: 是否区分大小写
            filters: 过滤条件
        
        Returns:
            搜索结果列表
        """
        results = []
        
        for memory_id, doc in self._documents.items():
            # 应用过滤器
            if filters and not self._apply_filters(doc, filters):
                continue
            
            # 获取内容
            content = doc.get("content", "")
            
            # 大小写处理
            if not case_sensitive:
                content = content.lower()
                keywords = [kw.lower() for kw in keywords]
            
            # 计算匹配
            matches = 0
            matched_keywords = []
            
            for kw in keywords:
                if kw in content:
                    matches += 1
                    matched_keywords.append(kw)
            
            # 根据匹配模式判断是否保留
            if match_mode == "AND" and matches == len(keywords):
                should_include = True
            elif match_mode == "OR" and matches > 0:
                should_include = True
            else:
                should_include = False
            
            if should_include:
                # 计算分数（匹配关键词比例）
                score = matches / len(keywords)
                
                results.append({
                    "memory_id": memory_id,
                    "content": doc.get("content", ""),
                    "score": round(score, 4),
                    "matched_keywords": matched_keywords,
                    "memory_type": doc.get("memory_type", "unknown"),
                    "created_at": doc.get("created_at", ""),
                    "metadata": doc.get("metadata", {})
                })
        
        return results
    
    def _apply_filters(
        self,
        doc: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> bool:
        """应用过滤器"""
        for key, value in filters.items():
            if key == "memory_type":
                if doc.get("memory_type") != value:
                    return False
            elif key == "tags":
                doc_tags = doc.get("tags", [])
                if isinstance(value, list):
                    if not any(tag in doc_tags for tag in value):
                        return False
                else:
                    if value not in doc_tags:
                        return False
            elif key == "min_importance":
                if doc.get("importance", 0) < value:
                    return False
        
        return True
    
    def add_document(
        self,
        memory_id: str,
        content: str,
        memory_type: str = "fact",
        importance: float = 3.0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加文档
        
        Args:
            memory_id: 记忆ID
            content: 文档内容
            memory_type: 记忆类型
            importance: 重要性
            tags: 标签列表
            metadata: 元数据
        
        Returns:
            是否添加成功
        """
        from datetime import datetime
        
        self._documents[memory_id] = {
            "content": content,
            "memory_type": memory_type,
            "importance": importance,
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        return True
    
    def delete_document(self, memory_id: str) -> bool:
        """
        删除文档
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            是否删除成功
        """
        if memory_id in self._documents:
            del self._documents[memory_id]
            return True
        return False
    
    def clear_documents(self) -> None:
        """清空所有文档"""
        self._documents.clear()
    
    def get_document_count(self) -> int:
        """获取文档数量"""
        return len(self._documents)
    
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
        
        match_mode = request_data.get("match_mode", "OR").upper()
        if match_mode not in ["AND", "OR"]:
            return "match_mode必须是AND或OR"
        
        return None
    
    def _error_response(
        self,
        query: str,
        match_mode: str,
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
            "match_mode": match_mode,
            "error": error
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取API统计信息"""
        return {
            "document_count": self.get_document_count()
        }
