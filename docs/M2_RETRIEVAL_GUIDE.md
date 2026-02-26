# M2 向量检索模块使用指南

**版本**: v3.0  
**更新日期**: 2026-02-24  
**状态**: ✅ 已完成

---

## 概述

M2向量检索模块提供基于语义相似度的记忆检索能力，支持：

- **向量检索**: 基于Embedding的语义相似度搜索
- **关键词检索**: 基于TF-IDF的关键词匹配
- **混合检索**: RRF算法融合向量+关键词结果
- **相似度计算**: 多种相似度度量方法

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                      RetrievalAPI                           │
│                    (统一检索接口)                            │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
      ┌────────▼────────┐          ┌──────────▼──────────┐
      │  VectorSearch   │          │   KeywordSearch     │
      │   (向量检索)     │          │    (关键词检索)      │
      └────────┬────────┘          └──────────┬──────────┘
               │                              │
      ┌────────▼────────┐          ┌──────────▼──────────┐
      │ EmbeddingService│          │   TF-IDF Index      │
      │   (向量生成)     │          │   (倒排索引)         │
      └─────────────────┘          └─────────────────────┘
```

---

## 快速开始

### 1. 基础使用

```python
from retrieval import RetrievalAPI

# 创建API实例
api = RetrievalAPI.create_default("./data", "memories")

# 添加记忆
memory_id = api.add_memory(
    content="我喜欢在早晨喝咖啡",
    memory_type="preference",
    tags=["饮食", "早晨"],
    importance=4.0
)

# 向量搜索
response = api.vector_search("咖啡", top_k=5)
for result in response.results:
    print(f"{result.content} (score: {result.score:.3f})")
```

### 2. 混合搜索

```python
from retrieval import HybridSearch, VectorSearch, KeywordSearch

# 创建混合检索
vector_search = VectorSearch(embedding_service)
keyword_search = KeywordSearch()
hybrid = HybridSearch(vector_search, keyword_search)

# 搜索
results = hybrid.search("查询文本", top_k=10)
for result in results:
    print(f"{result.content} (融合分数: {result.score:.3f})")
    print(f"  向量分数: {result.vector_score}")
    print(f"  关键词分数: {result.keyword_score}")
```

### 3. 相似度计算

```python
from retrieval import SimilarityService, SimilarityMetric

service = SimilarityService()

# 计算两个向量的相似度
vec1 = [1.0, 0.0, 0.0]
vec2 = [0.0, 1.0, 0.0]

result = service.compute(vec1, vec2, SimilarityMetric.COSINE)
print(f"余弦相似度: {result.score:.3f}")
print(f"归一化分数: {result.normalized_score:.3f}")

# 批量计算
query = [1.0, 0.0, 0.0]
candidates = [[0.0, 1.0, 0.0], [1.0, 0.0, 0.0]]
results = service.compute_batch(query, candidates, top_k=2)
```

---

## API参考

### RetrievalAPI

统一检索接口，整合多种检索方式。

#### 方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `create_default()` | storage_path, collection_name, model_name | RetrievalAPI | 创建默认实例 |
| `vector_search()` | query, top_k, min_similarity, filters | SearchResponse | 向量搜索 |
| `hybrid_search()` | query, top_k, min_score | SearchResponse | 混合搜索 |
| `add_memory()` | content, memory_type, tags, importance | str/None | 添加记忆 |
| `remove_memory()` | memory_id | bool | 移除记忆 |
| `get_stats()` | - | dict | 获取统计信息 |

### VectorSearch

基于ChromaDB的向量检索引擎。

#### 方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `search()` | query, top_k, min_similarity, filters | List[VectorSearchResult] | 向量搜索 |
| `add_document()` | memory_id, content, embedding, ... | bool | 添加文档 |
| `remove_document()` | memory_id | bool | 移除文档 |
| `get_stats()` | - | dict | 获取统计信息 |

### KeywordSearch

基于TF-IDF的关键词检索引擎。

#### 方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `search()` | query, top_k, min_score | List[KeywordSearchResult] | 关键词搜索 |
| `add_document()` | memory_id, content, ... | bool | 添加文档 |
| `remove_document()` | memory_id | bool | 移除文档 |
| `get_stats()` | - | dict | 获取统计信息 |

### HybridSearch

混合检索引擎，使用RRF算法融合结果。

#### 方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `search()` | query, top_k, min_score | List[HybridSearchResult] | 混合搜索 |
| `add_document()` | memory_id, content, ... | bool | 添加文档 |
| `remove_document()` | memory_id | bool | 移除文档 |
| `get_stats()` | - | dict | 获取统计信息 |

### SimilarityService

相似度计算服务。

#### 方法

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `compute()` | vec1, vec2, metric | SimilarityResult | 计算相似度 |
| `compute_batch()` | query_vec, candidate_vecs, top_k | List[tuple] | 批量计算 |
| `compute_matrix()` | vectors, metric | List[List[float]] | 相似度矩阵 |

#### 相似度度量

| 度量 | 说明 | 范围 |
|------|------|------|
| `COSINE` | 余弦相似度 | [-1, 1] |
| `EUCLIDEAN` | 欧几里得距离 | [0, ∞) |
| `MANHATTAN` | 曼哈顿距离 | [0, ∞) |
| `DOT_PRODUCT` | 点积 | (-∞, ∞) |

---

## RRF融合算法

混合检索使用RRF (Reciprocal Rank Fusion) 算法融合向量检索和关键词检索的结果。

### 公式

```
RRF分数 = Σ(weight_i / (k + rank_i))
```

其中：
- `weight_i`: 第i个检索方法的权重（默认向量0.7，关键词0.3）
- `k`: 常数（默认60）
- `rank_i`: 文档在第i个检索结果中的排名（从0开始）

### 示例

```
文档A:
  - 向量检索排名: 0
  - 关键词检索排名: 2
  
RRF分数 = 0.7/(60+0) + 0.3/(60+2) = 0.0117 + 0.0048 = 0.0165
```

---

## 配置选项

### Embedding配置

```python
from retrieval import EmbeddingService, EmbeddingConfig

config = EmbeddingConfig(
    model_name="all-MiniLM-L6-v2",  # 模型名称
    cache_dir="./models",            # 缓存目录
    device="cpu",                    # 运行设备
    max_seq_length=512               # 最大序列长度
)

service = EmbeddingService(config=config)
```

### 混合检索配置

```python
hybrid = HybridSearch(
    vector_search=vector_search,
    keyword_search=keyword_search,
    vector_weight=0.7,      # 向量检索权重
    keyword_weight=0.3,     # 关键词检索权重
    rrf_k=60               # RRF常数
)
```

---

## 性能优化

### 1. 模型缓存

Embedding模型会自动缓存到本地，避免重复下载：

```python
# 模型缓存路径
./models/all-MiniLM-L6-v2/
```

### 2. 延迟加载

EmbeddingService使用延迟加载策略，模型在首次调用`generate()`时才加载：

```python
service = EmbeddingService()  # 不加载模型
embedding = service.generate("文本")  # 此时加载模型
```

### 3. 批量处理

使用批量接口提高性能：

```python
# 批量计算相似度
results = service.compute_batch(query_vec, candidate_vecs, top_k=10)
```

---

## 测试

### 运行测试

```bash
# 相似度计算测试
python -m pytest tests/test_similarity.py -v

# 关键词检索测试
python -m pytest tests/test_keyword_search.py -v

# 混合检索测试
python -m pytest tests/test_hybrid_search.py -v

# 集成测试
python -m pytest tests/integration/test_m2_retrieval_integration.py -v
```

### 测试结果

| 模块 | 测试数 | 状态 |
|------|--------|------|
| 相似度计算 | 18 | ✅ 通过 |
| 关键词检索 | 16 | ✅ 通过 |
| 混合检索 | 4 | ✅ 通过 |
| 集成测试 | 10 | ✅ 通过 |
| **总计** | **48** | **✅ 全部通过** |

---

## 故障排除

### 问题1: Embedding模型加载慢

**原因**: 首次使用需要下载模型（约100MB）

**解决**: 
- 使用镜像加速: `HF_ENDPOINT=https://hf-mirror.com`
- 或预下载模型到 `./models/` 目录

### 问题2: 向量搜索返回空结果

**原因**: 
- 索引为空
- 相似度阈值过高
- 查询文本为空

**解决**:
```python
# 检查统计信息
stats = api.get_stats()
print(stats)

# 降低相似度阈值
results = api.vector_search("查询", min_similarity=0.5)
```

### 问题3: 混合检索结果不符合预期

**原因**: 权重设置不合理

**解决**: 调整向量/关键词权重
```python
hybrid = HybridSearch(
    vector_search, 
    keyword_search,
    vector_weight=0.8,   # 提高向量权重
    keyword_weight=0.2
)
```

---

## 更新日志

### 2026-02-24
- ✅ 完成向量检索API封装
- ✅ 完成相似度计算服务
- ✅ 完成混合检索实现
- ✅ 完成48个测试用例
- ✅ 完成使用文档

---

## 下一步

- M3: 自动优化（AutoOptimizer）
- M4: 四层完善（核心层+检索层+存储层+傻瓜层）
- M5: 系统集成测试
