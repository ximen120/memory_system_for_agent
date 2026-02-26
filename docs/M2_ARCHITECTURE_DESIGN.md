# M2向量检索API架构设计

**版本**: v1.0  
**日期**: 2026-02-24  
**设计人**: 安仔

---

## 1. 整体架构

### 1.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户交互层                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ AutoTrigger │  │CommandParser│  │   TimelineViewer    │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
└─────────┼────────────────┼────────────────────┼─────────────┘
          │                │                    │
          └────────────────┴────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  MemoryAPI  │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
   ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
   │HybridSearch │  │KeywordSearch│  │ Timeline    │
   └──────┬──────┘  └─────────────┘  └─────────────┘
          │
   ┌──────┴──────┐
   │             │
┌──▼───┐    ┌────▼────┐
│Vector│    │ Keyword │
│Search│    │ Search  │
└──┬───┘    └─────────┘
   │
┌──▼──────────────┐
│ EmbeddingService │
└──┬──────────────┘
   │
┌──▼────────────────┐
│ sentence-transformers│
│  (all-MiniLM-L6-v2)  │
└─────────────────────┘
```

### 1.2 模块职责

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| MemoryAPI | 统一接口 | 用户请求 | 记忆数据 |
| HybridSearch | 混合检索 | 查询文本 | 排序结果 |
| VectorSearch | 向量检索 | 查询向量 | 相似结果 |
| EmbeddingService | 向量生成 | 文本 | 向量 |
| ChromaStorage | 向量存储 | 向量+元数据 | 存储状态 |

---

## 2. 详细设计

### 2.1 MemoryAPI (统一接口层)

```python
class MemoryAPI:
    """
    记忆系统统一API
    
    提供增删改查接口，屏蔽底层实现细节
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.embedding_service = EmbeddingService()
        self.vector_search = VectorSearch(self.embedding_service)
        self.keyword_search = KeywordSearch()
        self.hybrid_search = HybridSearch(
            self.vector_search, 
            self.keyword_search
        )
    
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
            memory_type: 记忆类型
            importance: 重要性
            tags: 标签列表
            **metadata: 额外元数据
            
        Returns:
            memory_id: 记忆ID
        """
        pass
    
    def search(
        self, 
        query: str,
        search_type: str = "hybrid",  # "vector" | "keyword" | "hybrid"
        top_k: int = 10,
        min_score: float = 0.7,
        filters: Optional[Dict] = None
    ) -> List[SearchResult]:
        """
        搜索记忆
        
        Args:
            query: 查询文本
            search_type: 搜索类型
            top_k: 返回数量
            min_score: 最小相似度
            filters: 过滤条件
            
        Returns:
            搜索结果列表
        """
        pass
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        pass
    
    def update_memory(
        self, 
        memory_id: str, 
        **updates
    ) -> bool:
        """更新记忆"""
        pass
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """获取单条记忆"""
        pass
```

### 2.2 EmbeddingService (向量生成服务)

```python
class EmbeddingService:
    """
    Embedding生成服务
    
    特性：
    - 延迟加载模型（避免启动阻塞）
    - 模型缓存管理
    - 降级方案（模型不可用时返回None）
    - 批量生成支持
    """
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        cache_dir: Optional[str] = None,
        device: str = "cpu"
    ):
        self.model_name = model_name
        self.cache_dir = cache_dir or "./models"
        self.device = device
        self._model = None
        self._is_loaded = False
    
    def _load_model(self) -> bool:
        """
        延迟加载模型
        
        Returns:
            是否加载成功
        """
        if self._is_loaded:
            return True
        
        try:
            from sentence_transformers import SentenceTransformer
            
            model_path = Path(self.cache_dir) / self.model_name
            
            if model_path.exists():
                # 使用本地缓存
                self._model = SentenceTransformer(str(model_path))
            else:
                # 下载模型
                self._model = SentenceTransformer(self.model_name)
                # 保存到本地缓存
                self._model.save(str(model_path))
            
            self._is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return False
    
    def generate(
        self, 
        text: str,
        return_none_on_error: bool = True
    ) -> Optional[List[float]]:
        """
        生成文本的embedding向量
        
        Args:
            text: 输入文本
            return_none_on_error: 出错时返回None而非抛出异常
            
        Returns:
            向量列表或None
        """
        if not self._load_model():
            if return_none_on_error:
                return None
            raise RuntimeError("模型未加载")
        
        try:
            embedding = self._model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"生成embedding失败: {e}")
            if return_none_on_error:
                return None
            raise
    
    def generate_batch(
        self, 
        texts: List[str]
    ) -> List[Optional[List[float]]]:
        """批量生成embedding"""
        if not self._load_model():
            return [None] * len(texts)
        
        try:
            embeddings = self._model.encode(texts)
            return [e.tolist() for e in embeddings]
        except Exception as e:
            logger.error(f"批量生成失败: {e}")
            return [None] * len(texts)
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self._load_model()
```

### 2.3 VectorSearch (向量检索)

```python
class VectorSearch:
    """
    向量检索引擎
    
    基于ChromaDB实现语义相似度搜索
    """
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        storage: Optional[ChromaStorage] = None,
        collection_name: str = "memories"
    ):
        self.embedding_service = embedding_service
        self.storage = storage or ChromaStorage(
            collection_name=collection_name,
            # Windows默认使用内存模式
            memory_mode=IS_WINDOWS
        )
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.7,
        filters: Optional[Dict] = None
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
        # 1. 生成查询向量
        query_vector = self.embedding_service.generate(query)
        if query_vector is None:
            logger.warning("Embedding服务不可用，返回空结果")
            return []
        
        # 2. 执行向量搜索
        results = self.storage.similarity_search(
            query_vector=query_vector,
            top_k=top_k,
            min_similarity=min_similarity,
            filters=filters
        )
        
        return results
    
    def add_document(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """添加文档到向量库"""
        vector = self.embedding_service.generate(content)
        if vector is None:
            return False
        
        return self.storage.add_vector(
            id=memory_id,
            vector=vector,
            metadata=metadata or {}
        )
```

### 2.4 HybridSearch (混合检索)

```python
class HybridSearch:
    """
    混合检索引擎
    
    结合向量检索和关键词检索的优势
    """
    
    def __init__(
        self,
        vector_search: VectorSearch,
        keyword_search: KeywordSearch,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ):
        self.vector_search = vector_search
        self.keyword_search = keyword_search
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.6,
        use_vector: bool = True,
        use_keyword: bool = True
    ) -> List[HybridSearchResult]:
        """
        混合搜索
        
        策略：
        1. 如果Embedding服务可用，优先使用向量检索
        2. 同时执行关键词检索作为补充
        3. 融合两种结果，重新排序
        """
        vector_results = []
        keyword_results = []
        
        # 向量检索
        if use_vector and self.vector_search.embedding_service.is_available():
            vector_results = self.vector_search.search(
                query, top_k=top_k * 2, min_similarity=0.5
            )
        
        # 关键词检索
        if use_keyword:
            keyword_results = self.keyword_search.search(
                query, limit=top_k * 2
            )
        
        # 融合结果
        fused_results = self._fuse_results(
            vector_results, 
            keyword_results,
            top_k=top_k
        )
        
        # 过滤低分结果
        return [r for r in fused_results if r.score >= min_score]
    
    def _fuse_results(
        self,
        vector_results: List[VectorSearchResult],
        keyword_results: List[KeywordSearchResult],
        top_k: int
    ) -> List[HybridSearchResult]:
        """
        融合两种检索结果
        
        使用RRF (Reciprocal Rank Fusion)算法
        """
        # 构建ID到结果的映射
        all_results = {}
        
        # 处理向量结果
        for rank, result in enumerate(vector_results):
            if result.memory_id not in all_results:
                all_results[result.memory_id] = {
                    "vector_rank": rank,
                    "keyword_rank": None,
                    "result": result
                }
        
        # 处理关键词结果
        for rank, result in enumerate(keyword_results):
            if result.memory_id in all_results:
                all_results[result.memory_id]["keyword_rank"] = rank
            else:
                all_results[result.memory_id] = {
                    "vector_rank": None,
                    "keyword_rank": rank,
                    "result": result
                }
        
        # RRF评分
        k = 60  # RRF常数
        fused = []
        
        for memory_id, data in all_results.items():
            vector_rank = data["vector_rank"]
            keyword_rank = data["keyword_rank"]
            
            # 计算RRF分数
            score = 0
            if vector_rank is not None:
                score += self.vector_weight / (k + vector_rank)
            if keyword_rank is not None:
                score += self.keyword_weight / (k + keyword_rank)
            
            fused.append(HybridSearchResult(
                memory_id=memory_id,
                content=data["result"].content,
                score=score,
                vector_rank=vector_rank,
                keyword_rank=keyword_rank
            ))
        
        # 按分数排序
        fused.sort(key=lambda x: x.score, reverse=True)
        
        return fused[:top_k]
```

---

## 3. 数据流设计

### 3.1 添加记忆流程

```
用户输入: "安哥喜欢喝咖啡"
    ↓
MemoryAPI.add_memory()
    ↓
[并行执行]
    ├── 1. 保存到JSON存储 (基础数据)
    ├── 2. 生成Embedding → 保存到ChromaDB (向量数据)
    └── 3. 更新关键词索引
    ↓
返回 memory_id
```

### 3.2 搜索记忆流程

```
用户查询: "查找安哥的喜好"
    ↓
MemoryAPI.search(query="安哥的喜好", search_type="hybrid")
    ↓
HybridSearch.search()
    ↓
[并行执行]
    ├── VectorSearch.search()
    │       └── EmbeddingService.generate(query)
    │       └── ChromaStorage.similarity_search()
    └── KeywordSearch.search()
    ↓
结果融合 (RRF算法)
    ↓
返回排序结果
```

---

## 4. 接口定义

### 4.1 数据模型

```python
@dataclass
class SearchResult:
    """搜索结果"""
    memory_id: str
    content: str
    score: float
    memory_type: str
    created_at: str
    metadata: Dict[str, Any]

@dataclass
class VectorSearchResult(SearchResult):
    """向量搜索结果"""
    similarity: float  # 余弦相似度

@dataclass
class HybridSearchResult(SearchResult):
    """混合搜索结果"""
    vector_rank: Optional[int]
    keyword_rank: Optional[int]
    fusion_score: float
```

### 4.2 配置项

```python
@dataclass
class M2Config:
    """M2模块配置"""
    
    # Embedding配置
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    embedding_cache_dir: str = "./models"
    
    # ChromaDB配置
    chroma_persist_dir: str = "./data/vector_db"
    chroma_memory_mode: bool = IS_WINDOWS  # Windows默认内存模式
    
    # 检索配置
    default_search_type: str = "hybrid"
    default_top_k: int = 10
    min_similarity: float = 0.7
    
    # 混合检索权重
    vector_weight: float = 0.7
    keyword_weight: float = 0.3
```

---

## 5. 错误处理

### 5.1 降级策略

| 场景 | 处理方式 | 降级方案 |
|------|----------|----------|
| Embedding模型不可用 | 记录警告 | 仅使用关键词检索 |
| ChromaDB连接失败 | 记录错误 | 使用JSON存储+内存索引 |
| 向量生成失败 | 跳过该文档 | 继续处理其他文档 |
| 搜索结果为空 | 返回空列表 | 提示用户扩大搜索范围 |

### 5.2 异常类型

```python
class EmbeddingError(Exception):
    """Embedding生成错误"""
    pass

class VectorSearchError(Exception):
    """向量检索错误"""
    pass

class StorageConnectionError(Exception):
    """存储连接错误"""
    pass
```

---

## 6. 性能优化

### 6.1 缓存策略

- **模型缓存**: Embedding模型单例模式，避免重复加载
- **向量缓存**: 热门查询向量缓存（LRU策略）
- **结果缓存**: 相同查询结果缓存（TTL=5分钟）

### 6.2 批量处理

- **批量生成**: 支持批量文本embedding生成
- **批量插入**: 支持批量向量写入ChromaDB
- **批量查询**: 支持多查询并行执行

### 6.3 异步支持

```python
async def search_async(
    self, 
    query: str,
    **kwargs
) -> List[SearchResult]:
    """异步搜索"""
    # 异步执行向量检索和关键词检索
    vector_task = asyncio.create_task(
        self.vector_search.search_async(query, **kwargs)
    )
    keyword_task = asyncio.create_task(
        self.keyword_search.search_async(query, **kwargs)
    )
    
    vector_results, keyword_results = await asyncio.gather(
        vector_task, keyword_task
    )
    
    return self._fuse_results(vector_results, keyword_results)
```

---

## 7. 测试策略

### 7.1 单元测试

| 模块 | 测试内容 | 覆盖率目标 |
|------|----------|------------|
| EmbeddingService | 模型加载、向量生成、降级 | 90% |
| VectorSearch | 相似度搜索、过滤、排序 | 90% |
| HybridSearch | 结果融合、权重调整 | 85% |
| MemoryAPI | 完整流程、错误处理 | 85% |

### 7.2 集成测试

- 端到端检索流程
- 降级方案验证
- 性能基准测试

---

## 8. 部署考虑

### 8.1 模型管理

```bash
# 预下载脚本
python scripts/download_model.py \
    --model all-MiniLM-L6-v2 \
    --output ./models
```

### 8.2 环境变量

```bash
# .env文件
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu
CHROMA_MEMORY_MODE=true  # Windows推荐
DEFAULT_SEARCH_TYPE=hybrid
```

---

## 9. 后续扩展

### 9.1 可能的优化

- [ ] 支持GPU加速（CUDA）
- [ ] 多模型融合（Ensemble）
- [ ] 增量索引更新
- [ ] 分布式向量存储

### 9.2 新功能

- [ ] 图像embedding支持
- [ ] 多语言模型支持
- [ ] 实时学习（在线更新）

---

*架构设计完成时间: 2026-02-24*  
*为安哥打造的零操作记忆系统*
