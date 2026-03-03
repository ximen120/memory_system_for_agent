"""
MemoryAPI - 记忆系统统一接口

提供简洁的API接口，屏蔽底层实现细节。
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# 导入检索模块
from retrieval import EmbeddingService, VectorSearch, HybridSearch
# 导入存储模块
from storage.json_storage import JsonStorage

# 导入核心模型
from core.memory_unit import MemoryUnit


# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    memory_id: str
    content: str
    score: float
    memory_type: str
    created_at: str
    tags: List[str]
    metadata: Dict[str, Any]
    search_method: str  # "vector" | "keyword" | "hybrid"


@dataclass
class Memory:
    """记忆对象"""
    memory_id: str
    content: str
    memory_type: str
    importance: float
    tags: List[str]
    created_at: str
    updated_at: Optional[str]
    metadata: Dict[str, Any]


class MemoryAPI:
    """
    记忆系统统一API
    
    提供增删改查接口，屏蔽底层实现细节。
    
    使用示例：
        >>> api = MemoryAPI()
        >>> memory_id = api.add_memory("安哥喜欢喝咖啡")
        >>> results = api.search("咖啡")
        >>> for r in results:
        ...     print(r.content)
    """
    
    def __init__(
        self,
        data_dir: str = "./data",
        embedding_model: str = "all-MiniLM-L6-v2",
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ):
        """
        初始化MemoryAPI
        
        Args:
            data_dir: 数据目录
            embedding_model: Embedding模型名称
            vector_weight: 向量检索权重
            keyword_weight: 关键词检索权重
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化Embedding服务
        self.embedding_service = EmbeddingService(
            model_name=embedding_model,
            cache_dir=str(self.data_dir / "models")
        )
        
        # 初始化向量检索
        self.vector_search = VectorSearch(
            embedding_service=self.embedding_service
        )
        
        # 初始化混合检索
        self.hybrid_search = HybridSearch(
            vector_search=self.vector_search,
            vector_weight=vector_weight,
            keyword_weight=keyword_weight
        )
        
        # 初始化存储后端
        storage_dir = self.data_dir / "memories"
        self.json_storage = JsonStorage(str(storage_dir))
        
        # 内存缓存（优先从内存检索，降级到存储检索）
        self._memories: Dict[str, Memory] = {}
        
        # 启动时加载已有记忆
        self._load_existing_memories()
        
        logger.info(f"MemoryAPI初始化完成: data_dir={data_dir}")
    
    
    def _load_existing_memories(self) -> None:
        """从存储加载已有记忆到内存缓存"""
        try:
            existing_memories = self.json_storage.query(limit=99999)
            for memory_unit in existing_memories:
                # 转换为Memory对象
                memory = Memory(
                    memory_id=memory_unit.memory_id,
                    content=memory_unit.content,
                    memory_type=memory_unit.memory_type,
                    importance=memory_unit.importance,
                    tags=memory_unit.tags,
                    created_at=memory_unit.created_at,
                    updated_at=memory_unit.updated_at,
                    metadata={
                        "source": memory_unit.source,
                        "access_count": memory_unit.access_count,
                        "last_accessed_at": memory_unit.last_accessed_at
                    }
                )
                self._memories[memory_unit.memory_id] = memory
                
                # 添加到向量检索
                if self.embedding_service.is_available() and memory_unit.embedding:
                    self.vector_search.add_document(
                        memory_id=memory_unit.memory_id,
                        content=memory_unit.content,
                        embedding=memory_unit.embedding,
                        memory_type=memory_unit.memory_type,
                        metadata={
                            "importance": memory_unit.importance,
                            "tags": memory_unit.tags,
                            "source": memory_unit.source
                        }
                    )
            
            logger.info(f"从存储加载了 {len(existing_memories)} 条记忆")
        except Exception as e:
            logger.error(f"加载已有记忆失败: {e}")

    def add_memory(
        self,
        content: str,
        memory_type: str = "fact",
        importance: float = 3.0,
        tags: Optional[List[str]] = None,
        **metadata
    ) -> str:
        """
        添加记忆
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型 (fact/preference/plan/goal/context)
            importance: 重要性 (1-5)
            tags: 标签列表
            **metadata: 额外元数据
            
        Returns:
            memory_id: 记忆ID
            
        示例：
            >>> memory_id = api.add_memory(
            ...     "安哥喜欢喝咖啡",
            ...     memory_type="preference",
            ...     importance=4.0,
            ...     tags=["咖啡", "喜好"]
            ... )
        """
        # 生成记忆ID
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(content)}"
        
        # 创建记忆对象
        now = datetime.now().isoformat()
        memory = Memory(
            memory_id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            created_at=now,
            updated_at=None,
            metadata=metadata
        )
        
        # 保存到内存存储

        # 持久化到存储
        try:
            memory_unit = MemoryUnit(
                memory_id=memory_id,
                content=content,
                memory_type=memory_type,
                importance=importance,
                tags=tags or [],
                created_at=now,
                updated_at=None,
                source=metadata.get("source"),
                access_count=0,
                last_accessed_at=None
            )
            self.json_storage.save(memory_unit)
        except Exception as e:
            logger.error(f"持久化记忆失败: {e}")
        self._memories[memory_id] = memory
        
        # 添加到向量检索（如果Embedding服务可用）
        if self.embedding_service.is_available():
            embedding = self.embedding_service.generate(content)
            if embedding:
                self.vector_search.add_document(
                    memory_id=memory_id,
                    content=content,
                    embedding=embedding,
                    memory_type=memory_type,
                    metadata={
                        "importance": importance,
                        "tags": tags or [],
                        **metadata
                    }
                )
        
        logger.info(f"记忆已添加: {memory_id}")
        return memory_id
    
    def search(
        self,
        query: str,
        search_type: str = "hybrid",  # "vector" | "keyword" | "hybrid"
        top_k: int = 10,
        min_score: float = 0.05,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        搜索记忆
        
        Args:
            query: 查询文本
            search_type: 搜索类型
            top_k: 返回数量
            min_score: 最小分数
            filters: 过滤条件
                - memory_type: 记忆类型
                - tags: 标签列表
                - min_importance: 最小重要性
                
        Returns:
            搜索结果列表
            
        示例：
            >>> results = api.search("咖啡", top_k=5)
            >>> for r in results:
            ...     print(f"{r.content}: {r.score}")
        """
        results = []
        
        if search_type == "hybrid":
            # 混合检索
            hybrid_results = self.hybrid_search.search(
                query=query,
                top_k=top_k,
                min_score=min_score
            )
            
            for r in hybrid_results:
                results.append(SearchResult(
                    memory_id=r.memory_id,
                    content=r.content,
                    score=r.score,
                    memory_type=r.memory_type,
                    created_at=r.created_at,
                    tags=r.metadata.get("tags", []),
                    metadata=r.metadata,
                    search_method="hybrid"
                ))
        
        elif search_type == "vector":
            # 向量检索
            if not self.embedding_service.is_available():
                logger.warning("Embedding服务不可用，切换到关键词检索")
                return self.search(query, search_type="keyword", top_k=top_k)
            
            vector_results = self.vector_search.search(
                query=query,
                top_k=top_k,
                min_similarity=min_score,
                filters=filters
            )
            
            for r in vector_results:
                results.append(SearchResult(
                    memory_id=r.memory_id,
                    content=r.content,
                    score=r.score,
                    memory_type=r.memory_type,
                    created_at=r.created_at,
                    tags=r.metadata.get("tags", []),
                    metadata=r.metadata,
                    search_method="vector"
                ))
        
        elif search_type == "keyword":
            # 关键词检索（简化版）
            keywords = query.lower().split()
            
            for memory_id, memory in self._memories.items():
                # 应用过滤器
                if filters:
                    if "memory_type" in filters and memory.memory_type != filters["memory_type"]:
                        continue
                    if "min_importance" in filters and memory.importance < filters["min_importance"]:
                        continue
                
                # 关键词匹配
                content_lower = memory.content.lower()
                matches = sum(1 for kw in keywords if kw in content_lower)
                
                if matches > 0:
                    score = matches / len(keywords)
                    if score >= min_score:
                        results.append(SearchResult(
                            memory_id=memory_id,
                            content=memory.content,
                            score=score,
                            memory_type=memory.memory_type,
                            created_at=memory.created_at,
                            tags=memory.tags,
                            metadata=memory.metadata,
                            search_method="keyword"
                        ))
            
            # 排序
            results.sort(key=lambda x: x.score, reverse=True)
            results = results[:top_k]
        
        logger.info(f"搜索完成: '{query}' 返回 {len(results)} 条结果")
        return results
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """
        获取单条记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            记忆对象或None
        """
        return self._memories.get(memory_id)
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否删除成功
        """
        if memory_id not in self._memories:
            return False
        
        # 从内存存储删除
        del self._memories[memory_id]
        
        # 从向量检索删除
        self.vector_search.delete_document(memory_id)
        
        
        # 从持久化存储删除
        try:
            self.json_storage.delete(memory_id)
        except Exception as e:
            logger.error(f"删除持久化记忆失败: {e}")
        
        logger.info(f"记忆已删除: {memory_id}")
        return True
    
    def update_memory(
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
        if memory_id not in self._memories:
            return False
        
        memory = self._memories[memory_id]
        
        # 更新字段
        if content is not None:
            memory.content = content
        if importance is not None:
            memory.importance = importance
        if tags is not None:
            memory.tags = tags
        
        memory.metadata.update(metadata)
        memory.updated_at = datetime.now().isoformat()
        
        # 更新向量检索
        if content is not None:
            self.vector_search.update_document(
                memory_id=memory_id,
                content=content,
                importance=memory.importance,
                tags=memory.tags,
                **memory.metadata
            )
        
        
        # 持久化更新
        try:
            # 先加载原始数据
            original_unit = self.json_storage.load(memory_id)
            
            # 更新字段
            if content is not None:
                original_unit.update_content(content)
            if importance is not None:
                original_unit.importance = importance
            if tags is not None:
                original_unit.tags = tags
            original_unit.updated_at = memory.updated_at
            
            # 保存
            self.json_storage.save(original_unit)
        except Exception as e:
            logger.error(f"更新持久化记忆失败: {e}")
        
        logger.info(f"记忆已更新: {memory_id}")
        return True
    
    def list_memories(
        self,
        memory_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Memory]:
        """
        列出记忆
        
        Args:
            memory_type: 过滤记忆类型
            limit: 返回数量
            offset: 偏移量
            
        Returns:
            记忆列表
        """
        memories = list(self._memories.values())
        
        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]
        
        # 按时间排序
        memories.sort(key=lambda x: x.created_at, reverse=True)
        
        return memories[offset:offset + limit]
    
    def count_memories(self, memory_type: Optional[str] = None) -> int:
        """
        统计记忆数量
        
        Args:
            memory_type: 记忆类型过滤
            
        Returns:
            数量
        """
        if memory_type:
            return sum(1 for m in self._memories.values() if m.memory_type == memory_type)
        return len(self._memories)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取系统统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "total_memories": self.count_memories(),
            "vector_available": self.embedding_service.is_available(),
            "vector_count": self.vector_search.count(),
            "embedding_model": self.embedding_service.config.model_name,
            "data_dir": str(self.data_dir)
        }
    
    def clear_all(self) -> None:
        """清空所有记忆（谨慎使用）"""
        self._memories.clear()
        self.vector_search.clear()
        logger.warning("所有记忆已清空")
