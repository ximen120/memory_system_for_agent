"""
向量检索引擎

基于ChromaDB实现语义相似度搜索。
"""

import logging
from typing import List, Optional, Dict, Any, Union
from dataclasses import dataclass

try:
    from .embedding_service import EmbeddingService
    from .similarity import cosine_similarity
except ImportError:
    from embedding_service import EmbeddingService
    from similarity import cosine_similarity

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """向量搜索结果"""
    memory_id: str
    content: str
    score: float  # 相似度分数 (0-1)
    memory_type: str
    created_at: str
    metadata: Dict[str, Any]


class VectorSearch:
    """
    向量检索引擎
    
    基于ChromaDB实现语义相似度搜索。
    
    使用示例：
        >>> from retrieval import VectorSearch, EmbeddingService
        >>> from storage import ChromaStorage
        >>> 
        >>> embedding_service = EmbeddingService()
        >>> storage = ChromaStorage("./data", "memories")
        >>> vector_search = VectorSearch(embedding_service, storage)
        >>> 
        >>> results = vector_search.search("查询文本", top_k=10)
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        storage=None,
        collection_name: str = "memories"
    ):
        """
        初始化向量检索引擎
        
        Args:
            embedding_service: Embedding服务
            storage: 向量存储（ChromaStorage实例，可选）
            collection_name: 集合名称
        """
        self.embedding_service = embedding_service
        self.storage = storage
        self.collection_name = collection_name
        
        # 如果没有提供storage，使用内存存储（向后兼容）
        self._use_memory_storage = storage is None
        self._vectors: Dict[str, List[float]] = {}
        self._documents: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"向量检索引擎初始化: collection={collection_name}, use_memory={self._use_memory_storage}")
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """
        向量相似度搜索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            min_similarity: 最小相似度(0-1)
            filters: 元数据过滤条件
            
        Returns:
            搜索结果列表
        """
        if not query or not query.strip():
            logger.warning("查询文本为空")
            return []
        
        try:
            # 生成查询向量
            query_embedding = self.embedding_service.generate(query)
            if query_embedding is None:
                logger.error("生成查询向量失败")
                return []
            
            # 使用存储层进行向量搜索
            if self._use_memory_storage:
                return self._search_memory(
                    query_embedding, 
                    top_k=top_k, 
                    min_similarity=min_similarity,
                    filters=filters
                )
            else:
                return self._search_storage(
                    query_embedding,
                    top_k=top_k,
                    min_similarity=min_similarity,
                    filters=filters
                )
                
        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            return []
    
    def _search_storage(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        min_similarity: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """使用ChromaStorage进行搜索"""
        try:
            # 调用存储层的向量搜索
            memories = self.storage.search(
                query_embedding=query_embedding,
                top_k=top_k * 2,  # 多取一些，过滤后再截断
                filters=filters
            )
            
            results = []
            for memory in memories:
                # 计算相似度（ChromaDB返回的是距离，需要转换）
                # 这里假设ChromaStorage已经返回了相似度
                score = getattr(memory, 'similarity', 0.8)  # 默认值
                
                if score >= min_similarity:
                    results.append(VectorSearchResult(
                        memory_id=memory.memory_id,
                        content=memory.content,
                        score=score,
                        memory_type=memory.memory_type,
                        created_at=str(memory.created_at),
                        metadata={
                            'tags': memory.tags,
                            'importance': memory.importance,
                            'source': memory.source
                        }
                    ))
            
            # 按相似度排序并截断
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"存储层搜索失败: {e}")
            return []
    
    def _search_memory(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        min_similarity: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[VectorSearchResult]:
        """使用内存存储进行搜索（向后兼容）"""
        if not self._vectors:
            return []
        
        # 计算相似度
        from .similarity import cosine_similarity
        
        scored_results = []
        for memory_id, vector in self._vectors.items():
            score = cosine_similarity(query_embedding, vector)
            
            if score >= min_similarity:
                doc = self._documents.get(memory_id, {})
                
                # 应用过滤器
                if filters:
                    skip = False
                    for key, value in filters.items():
                        if key == 'memory_type' and doc.get('memory_type') != value:
                            skip = True
                            break
                        if key == 'tags' and not any(tag in doc.get('tags', []) for tag in value):
                            skip = True
                            break
                    if skip:
                        continue
                
                scored_results.append((score, memory_id, doc))
        
        # 排序并截断
        scored_results.sort(key=lambda x: x[0], reverse=True)
        scored_results = scored_results[:top_k]
        
        # 转换为结果对象
        results = []
        for score, memory_id, doc in scored_results:
            results.append(VectorSearchResult(
                memory_id=memory_id,
                content=doc.get('content', ''),
                score=score,
                memory_type=doc.get('memory_type', 'unknown'),
                created_at=doc.get('created_at', ''),
                metadata={
                    'tags': doc.get('tags', []),
                    'importance': doc.get('importance', 0),
                    'source': doc.get('source', '')
                }
            ))
        
        return results
    
    def add_document(
        self,
        memory_id: str,
        content: str,
        embedding: List[float],
        memory_type: str = "fact",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加文档到索引
        
        Args:
            memory_id: 记忆ID
            content: 文本内容
            embedding: 向量
            memory_type: 记忆类型
            metadata: 元数据
            
        Returns:
            是否成功
        """
        try:
            if self._use_memory_storage:
                # 内存模式
                self._vectors[memory_id] = embedding
                self._documents[memory_id] = {
                    'content': content,
                    'memory_type': memory_type,
                    'created_at': str(__import__('datetime').datetime.now()),
                    **(metadata or {})
                }
            else:
                # 使用存储层
                from core import MemoryUnit
                memory = MemoryUnit(
                    content=content,
                    memory_type=memory_type,
                    embedding=embedding,
                    **(metadata or {})
                )
                self.storage.save(memory)
            
            return True
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
    def remove_document(self, memory_id: str) -> bool:
        """
        从索引中移除文档（delete_document的别名）
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否成功
        """
        return self.delete_document(memory_id)
    
    def update_document(self, memory_id: str, content: str, **metadata) -> bool:
        """
        更新文档
        
        Args:
            memory_id: 记忆ID
            content: 新内容
            **metadata: 新元数据
            
        Returns:
            是否更新成功
        """
        try:
            # 重新生成embedding
            embedding = self.embedding_service.embed(content)
            
            if self._use_memory_storage:
                # 内存模式
                if memory_id in self._documents:
                    self._documents[memory_id]['content'] = content
                    self._documents[memory_id].update(metadata)
                    self._vectors[memory_id] = embedding
                    logger.info(f"文档已更新: {memory_id}")
                    return True
                else:
                    logger.warning(f"文档不存在，无法更新: {memory_id}")
                    return False
            else:
                # 使用存储层 - 先删除再添加
                if hasattr(self.storage, 'delete') and hasattr(self.storage, 'add'):
                    self.storage.delete(memory_id)
                    self.storage.add(
                        memory_id=memory_id,
                        content=content,
                        embedding=embedding,
                        **metadata
                    )
                    logger.info(f"文档已更新: {memory_id}")
                    return True
                else:
                    logger.warning(f"存储不支持更新操作: {memory_id}")
                    return False
        except Exception as e:
            logger.error(f"更新文档失败 {memory_id}: {e}")
            return False
    
    def delete_document(self, memory_id: str) -> bool:
        """
        删除文档
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否删除成功
        """
        try:
            if self._use_memory_storage:
                # 内存模式
                self._vectors.pop(memory_id, None)
                self._documents.pop(memory_id, None)
            else:
                # 使用存储层
                self.storage.delete(memory_id)
            
            logger.info(f"文档已删除: {memory_id}")
            return True
        except Exception as e:
            logger.error(f"删除文档失败 {memory_id}: {e}")
            return False
    
    def count(self) -> int:
        """
        获取索引中的文档总数
        
        Returns:
            文档总数
        """
        if self._use_memory_storage:
            return len(self._documents)
        else:
            try:
                return self.storage.count()
            except Exception:
                return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取索引统计信息
        
        Returns:
            统计信息字典
        """
        if self._use_memory_storage:
            return {
                'total_documents': len(self._vectors),
                'collection_name': self.collection_name,
                'storage_type': 'memory'
            }
        else:
            try:
                return {
                    'total_documents': self.storage.count(),
                    'collection_name': self.collection_name,
                    'storage_type': 'chroma'
                }
            except Exception as e:
                logger.error(f"获取统计信息失败: {e}")
                return {
                    'total_documents': 0,
                    'collection_name': self.collection_name,
                    'storage_type': 'chroma',
                    'error': str(e)
                }


# 便捷函数
def create_vector_search(
    storage_path: str = "./data/vector_db",
    collection_name: str = "memories",
    model_name: str = "all-MiniLM-L6-v2"
) -> VectorSearch:
    """
    创建向量检索引擎（便捷函数）
    
    Args:
        storage_path: 存储路径
        collection_name: 集合名称
        model_name: Embedding模型名称
        
    Returns:
        VectorSearch实例
    """
    from storage import ChromaStorage
    
    embedding_service = EmbeddingService(model_name=model_name)
    storage = ChromaStorage(storage_path, collection_name)
    
    return VectorSearch(embedding_service, storage, collection_name)


if __name__ == "__main__":
    # 测试代码
    print("向量检索引擎测试")
    
    # 创建内存模式的检索引擎
    embedding_service = EmbeddingService()
    vector_search = VectorSearch(embedding_service)
    
    print(f"引擎状态: {vector_search.get_stats()}")
    print("\n测试完成!")
