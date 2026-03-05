"""
统一API接口

整合所有API功能，提供统一的调用方式。
这是记忆系统的主要入口点。
"""

import logging
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime

from .memory_api import MemoryAPI
from .vector_api import VectorAPI
from .hybrid_api import HybridAPI
from .keyword_api import KeywordAPI
from .routes import APIRouter
from core.config_loader import Config

logger = logging.getLogger(__name__)


@dataclass
class UnifiedSearchResult:
    """统一搜索结果"""
    memory_id: str
    content: str
    score: float
    memory_type: str
    search_method: str  # "vector" | "keyword" | "hybrid"
    created_at: str
    tags: List[str]
    metadata: Dict[str, Any]


class UnifiedAPI:
    """
    统一API接口
    
    整合所有API功能，提供简洁统一的调用方式。
    
    这是记忆系统的主要入口，推荐所有用户通过此类使用API。
    
    使用示例：
        >>> api = UnifiedAPI()
        >>> 
        >>> # 添加记忆
        >>> memory_id = api.remember("安哥喜欢喝咖啡")
        >>> 
        >>> # 搜索记忆
        >>> results = api.search("咖啡")
        >>> 
        >>> # 自然语言查询
        >>> results = api.query("查找关于咖啡的记忆")
    """
    
    VERSION = "2.0.0"
    
    def __init__(
        self,
        data_dir: str = "./data",
        embedding_model: Optional[str] = None,
        auto_init: bool = True
    ):
        """
        初始化统一API
        
        Args:
            data_dir: 数据目录
            embedding_model: Embedding模型名称，默认从.env读取
            auto_init: 是否自动初始化
        """
        self.data_dir = data_dir
        # 如果没有指定模型，从.env读取
        if embedding_model is None:
            cfg = Config()
            embedding_model = cfg.embedding_model
        self.embedding_model = embedding_model
        
        # 初始化各API
        self.memory_api = MemoryAPI(data_dir=data_dir, embedding_model=embedding_model)
        self.vector_api = VectorAPI(embedding_service=self.memory_api.embedding_service, vector_search=self.memory_api.vector_search)
        self.hybrid_api = HybridAPI(embedding_service=self.memory_api.embedding_service, vector_search=self.memory_api.vector_search)
        self.keyword_api = KeywordAPI()
        self.router = APIRouter()
        
        if auto_init:
            self._initialize()
        
        # 启动时将已有记忆同步到 KeywordAPI（修复：keyword 纯内存索引重启后丢失）
        self._sync_keyword_index()
        
        logger.info(f"UnifiedAPI v{self.VERSION} 初始化完成")
    
    def _sync_keyword_index(self):
        """将 MemoryAPI 中已加载的记忆同步到 KeywordAPI 的内存索引"""
        try:
            for memory_id, memory in self.memory_api._memories.items():
                self.keyword_api.add_document(
                    memory_id=memory_id,
                    content=memory.content,
                    memory_type=memory.memory_type,
                    importance=memory.importance,
                    tags=memory.tags,
                    metadata=memory.metadata
                )
            logger.info(f"已同步 {len(self.memory_api._memories)} 条记忆到关键词索引")
        except Exception as e:
            logger.error(f"同步关键词索引失败: {e}")
    
    def _initialize(self):
        """初始化系统"""
        # 检查Embedding服务
        if self.vector_api.embedding_service.is_available():
            logger.info("Embedding服务可用")
        else:
            logger.warning("Embedding服务不可用，将使用关键词检索")
    
    # ========== 核心功能 ==========
    
    def remember(
        self,
        content: str,
        memory_type: str = "fact",
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None,
        **metadata
    ) -> str:
        """
        记住一条信息
        
        这是添加记忆的最简单方式。
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型 (fact/preference/plan/goal/context)
            importance: 重要性 (1-5)，None则自动判断
            tags: 标签列表
            **metadata: 额外元数据
            
        Returns:
            memory_id: 记忆ID
            
        示例：
            >>> api = UnifiedAPI()
            >>> mid = api.remember("安哥喜欢喝咖啡", importance=4.0)
            >>> print(mid)
        """
        # 自动判断重要性
        if importance is None:
            importance = self._auto_judge_importance(content)
        
        # 自动提取标签
        if tags is None:
            tags = self._auto_extract_tags(content)
        
        # 添加记忆
        memory_id = self.memory_api.add_memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags,
            **metadata
        )
        
        # 同时添加到关键词索引
        self.keyword_api.add_document(
            memory_id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags,
            metadata=metadata
        )
        
        logger.info(f"已记住: {content[:30]}... (ID: {memory_id[:20]}...)")
        return memory_id
    
    def search(
        self,
        query: str,
        search_type: str = "auto",  # "auto" | "vector" | "keyword" | "hybrid"
        top_k: int = 10,
        min_score: float = 0.05,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[UnifiedSearchResult]:
        """
        搜索记忆
        
        智能搜索，根据查询自动选择最佳搜索方式。
        
        Args:
            query: 查询文本
            search_type: 搜索类型
                - "auto": 自动选择（默认）
                - "vector": 向量检索
                - "keyword": 关键词检索
                - "hybrid": 混合检索
            top_k: 返回数量
            min_score: 最小分数
            filters: 过滤条件
                - memory_type: 记忆类型
                - tags: 标签列表
                - min_importance: 最小重要性
                
        Returns:
            搜索结果列表
            
        示例：
            >>> api = UnifiedAPI()
            >>> results = api.search("咖啡")
            >>> for r in results:
            ...     print(f"{r.content}: {r.score}")
        """
        # 自动选择搜索类型
        if search_type == "auto":
            search_type = self._choose_search_type(query)
        
        # 执行搜索
        if search_type == "vector":
            results = self._vector_search(query, top_k, min_score, filters)
        elif search_type == "keyword":
            results = self._keyword_search(query, top_k, min_score, filters)
        else:  # hybrid
            results = self._hybrid_search(query, top_k, min_score, filters)
        
        logger.info(f"搜索 '{query}' 找到 {len(results)} 条结果")
        return results
    
    def query(self, natural_language: str, **kwargs) -> List[UnifiedSearchResult]:
        """
        自然语言查询
        
        理解自然语言，执行相应的搜索或操作。
        
        Args:
            natural_language: 自然语言查询
            **kwargs: 其他参数
            
        Returns:
            搜索结果列表
            
        示例：
            >>> api = UnifiedAPI()
            >>> results = api.query("查找关于咖啡的记忆")
            >>> results = api.query("安哥喜欢什么？")
        """
        # 解析自然语言
        query_type, query_content = self._parse_natural_language(natural_language)
        
        if query_type == "search":
            return self.search(query_content, **kwargs)
        elif query_type == "remember":
            memory_id = self.remember(query_content)
            return [UnifiedSearchResult(
                memory_id=memory_id,
                content=query_content,
                score=1.0,
                memory_type="fact",
                search_method="remember",
                created_at=datetime.now().isoformat(),
                tags=[],
                metadata={}
            )]
        else:
            return self.search(natural_language, **kwargs)
    
    def forget(self, memory_id: str) -> bool:
        """
        忘记一条记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否删除成功
            
        示例：
            >>> api.forget("mem_xxx")
        """
        success = self.memory_api.delete_memory(memory_id)
        if success:
            self.keyword_api.delete_document(memory_id)
            logger.info(f"已忘记: {memory_id}")
        return success
    
    def recall(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        回忆一条记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            记忆内容或None
            
        示例：
            >>> memory = api.recall("mem_xxx")
            >>> print(memory["content"])
        """
        memory = self.memory_api.get_memory(memory_id)
        if memory:
            return {
                "memory_id": memory.memory_id,
                "content": memory.content,
                "memory_type": memory.memory_type,
                "importance": memory.importance,
                "tags": memory.tags,
                "created_at": memory.created_at,
                "updated_at": memory.updated_at,
                "metadata": memory.metadata
            }
        return None
    
    def list_all(
        self,
        memory_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        列出所有记忆
        
        Args:
            memory_type: 过滤记忆类型
            limit: 返回数量
            
        Returns:
            记忆列表
        """
        memories = self.memory_api.list_memories(
            memory_type=memory_type,
            limit=limit
        )
        
        return [
            {
                "memory_id": m.memory_id,
                "content": m.content,
                "memory_type": m.memory_type,
                "importance": m.importance,
                "tags": m.tags,
                "created_at": m.created_at
            }
            for m in memories
        ]
    
    def update(
        self,
        memory_id: str,
        content: Optional[str] = None,
        importance: Optional[float] = None,
        tags: Optional[List[str]] = None,
        **metadata
    ) -> bool:
        """
        更新记忆
        
        Args:
            memory_id: 记忆ID
            content: 新内容
            importance: 新重要性
            tags: 新标签
            **metadata: 新元数据
            
        Returns:
            是否更新成功
        """
        return self.memory_api.update_memory(
            memory_id=memory_id,
            content=content,
            importance=importance,
            tags=tags,
            **metadata
        )
    
    # ========== 高级功能 ==========
    
    def embed(self, text: str) -> Optional[List[float]]:
        """
        生成文本的向量表示
        
        Args:
            text: 输入文本
            
        Returns:
            向量或None
        """
        response = self.vector_api.embed({"text": text})
        if response["success"]:
            return response["embedding"]
        return None
    
    def similar_to(
        self,
        memory_id: str,
        top_k: int = 5
    ) -> List[UnifiedSearchResult]:
        """
        查找与指定记忆相似的记忆
        
        Args:
            memory_id: 参考记忆ID
            top_k: 返回数量
            
        Returns:
            相似记忆列表
        """
        memory = self.recall(memory_id)
        if not memory:
            return []
        
        return self.search(
            query=memory["content"],
            search_type="vector",
            top_k=top_k + 1  # +1因为会包含自己
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取系统统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "version": self.VERSION,
            "total_memories": self.memory_api.count_memories(),
            "embedding_available": self.vector_api.embedding_service.is_available(),
            "embedding_model": self.embedding_model,
            "data_dir": self.data_dir
        }
    
    def clear_all(self) -> None:
        """清空所有记忆（谨慎使用）"""
        self.memory_api.clear_all()
        self.keyword_api.clear_documents()
        logger.warning("所有记忆已清空")
    
    # ========== 内部方法 ==========
    
    def _auto_judge_importance(self, content: str) -> float:
        """自动判断重要性"""
        # 简单启发式规则
        importance = 3.0
        
        # 关键词加权
        high_priority = ["重要", "关键", "必须", "计划", "目标"]
        for kw in high_priority:
            if kw in content:
                importance = max(importance, 4.0)
                break
        
        # 偏好类
        preference = ["喜欢", "讨厌", "爱好"]
        for kw in preference:
            if kw in content:
                importance = max(importance, 3.5)
                break
        
        return importance
    
    def _auto_extract_tags(self, content: str) -> List[str]:
        """自动提取标签"""
        # 简单实现：提取2-4字的关键词
        import re
        words = re.findall(r'\b[\u4e00-\u9fa5]{2,4}\b', content)
        
        # 去重并限制数量
        tags = list(dict.fromkeys(words))[:5]
        return tags
    
    def _choose_search_type(self, query: str) -> str:
        """自动选择搜索类型"""
        # 如果Embedding不可用，使用关键词
        if not self.vector_api.embedding_service.is_available():
            return "keyword"
        
        # 短查询使用关键词，长查询使用混合
        if len(query) < 5:
            return "keyword"
        elif len(query) > 20:
            return "hybrid"
        else:
            return "hybrid"
    
    def _parse_natural_language(self, text: str) -> tuple:
        """解析自然语言"""
        text = text.strip()
        
        # 搜索意图
        search_keywords = ["查找", "搜索", "查询", "找", "看看"]
        for kw in search_keywords:
            if text.startswith(kw):
                content = text[len(kw):].strip("关于的").strip()
                return "search", content
        
        # 记住意图
        remember_keywords = ["记住", "记录", "保存"]
        for kw in remember_keywords:
            if text.startswith(kw):
                content = text[len(kw):].strip()
                return "remember", content
        
        # 默认搜索
        return "search", text
    
    def _vector_search(
        self,
        query: str,
        top_k: int,
        min_score: float,
        filters: Optional[Dict[str, Any]]
    ) -> List[UnifiedSearchResult]:
        """执行向量搜索"""
        response = self.vector_api.search({
            "query": query,
            "top_k": top_k,
            "min_similarity": min_score,
            "filters": filters
        })
        
        if not response["success"]:
            return []
        
        return [
            UnifiedSearchResult(
                memory_id=r["memory_id"],
                content=r["content"],
                score=r["score"],
                memory_type=r["memory_type"],
                search_method="vector",
                created_at=r["created_at"],
                tags=r["metadata"].get("tags", []),
                metadata=r["metadata"]
            )
            for r in response["results"]
        ]
    
    def _keyword_search(
        self,
        query: str,
        top_k: int,
        min_score: float,
        filters: Optional[Dict[str, Any]]
    ) -> List[UnifiedSearchResult]:
        """执行关键词搜索"""
        response = self.keyword_api.search({
            "query": query,
            "top_k": top_k,
            "match_mode": "OR",
            "filters": filters
        })
        
        if not response["success"]:
            return []
        
        return [
            UnifiedSearchResult(
                memory_id=r["memory_id"],
                content=r["content"],
                score=r["score"],
                memory_type=r["memory_type"],
                search_method="keyword",
                created_at=r["created_at"],
                tags=r["metadata"].get("tags", []),
                metadata=r["metadata"]
            )
            for r in response["results"]
        ]
    
    def _hybrid_search(
        self,
        query: str,
        top_k: int,
        min_score: float,
        filters: Optional[Dict[str, Any]]
    ) -> List[UnifiedSearchResult]:
        """执行混合搜索"""
        response = self.hybrid_api.search({
            "query": query,
            "top_k": top_k,
            "min_score": min_score,
            "filters": filters
        })
        
        if not response["success"]:
            return []
        
        return [
            UnifiedSearchResult(
                memory_id=r["memory_id"],
                content=r["content"],
                score=r["score"],
                memory_type=r["memory_type"],
                search_method=response.get("search_method", "hybrid"),
                created_at=r["created_at"],
                tags=r["metadata"].get("tags", []),
                metadata=r["metadata"]
            )
            for r in response["results"]
        ]
