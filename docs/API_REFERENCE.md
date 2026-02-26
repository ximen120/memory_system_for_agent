# API参考文档

**版本**: 2.0.0  
**更新日期**: 2026-02-24  
**适用**: 安仔记忆系统 v3.0

---

## 目录

1. [快速开始](#快速开始)
2. [UnifiedAPI](#unifiedapi)
3. [VectorAPI](#vectorapi)
4. [HybridAPI](#hybridapi)
5. [KeywordAPI](#keywordapi)
6. [MemoryAPI](#memoryapi)
7. [错误处理](#错误处理)
8. [示例代码](#示例代码)

---

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 基本使用

```python
from api import UnifiedAPI

# 创建API实例
api = UnifiedAPI()

# 添加记忆
memory_id = api.remember("安哥喜欢喝咖啡")

# 搜索记忆
results = api.search("咖啡")

# 自然语言查询
results = api.query("安哥喜欢什么？")
```

---

## UnifiedAPI

统一API接口，推荐所有用户使用。

### 初始化

```python
from api import UnifiedAPI

api = UnifiedAPI(
    data_dir="./data",                    # 数据目录
    embedding_model="all-MiniLM-L6-v2",   # Embedding模型
    auto_init=True                        # 自动初始化
)
```

### remember - 记住信息

```python
memory_id = api.remember(
    content="安哥喜欢喝咖啡",           # 记忆内容（必需）
    memory_type="preference",           # 记忆类型（默认fact）
    importance=4.0,                     # 重要性（默认自动判断）
    tags=["咖啡", "喜好"]                # 标签（默认自动提取）
)
```

**记忆类型**:
- `fact` - 事实
- `preference` - 偏好
- `plan` - 计划
- `goal` - 目标
- `context` - 上下文

### search - 搜索记忆

```python
results = api.search(
    query="咖啡",                       # 查询文本（必需）
    search_type="auto",                 # 搜索类型（默认auto）
    top_k=10,                           # 返回数量（默认10）
    min_score=0.05,                     # 最小分数（默认0.05）
    filters={                           # 过滤条件（可选）
        "memory_type": "preference",
        "tags": ["咖啡"],
        "min_importance": 3.0
    }
)
```

**搜索类型**:
- `auto` - 自动选择
- `vector` - 向量检索
- `keyword` - 关键词检索
- `hybrid` - 混合检索

**返回结果**:
```python
[
    {
        "memory_id": "mem_xxx",
        "content": "安哥喜欢喝咖啡",
        "score": 0.95,
        "memory_type": "preference",
        "search_method": "hybrid",
        "created_at": "2026-02-24T10:00:00",
        "tags": ["咖啡", "喜好"],
        "metadata": {}
    }
]
```

### query - 自然语言查询

```python
results = api.query("查找关于咖啡的记忆")
results = api.query("安哥喜欢什么？")
results = api.query("记住安哥下周要开会")
```

### recall - 回忆特定记忆

```python
memory = api.recall("mem_xxx")
# 返回: {"memory_id": "...", "content": "...", ...}
```

### forget - 忘记记忆

```python
success = api.forget("mem_xxx")
```

### update - 更新记忆

```python
success = api.update(
    "mem_xxx",
    content="新内容",
    importance=4.5,
    tags=["新标签"]
)
```

### list_all - 列出所有记忆

```python
memories = api.list_all(
    memory_type="preference",  # 过滤类型（可选）
    limit=100                  # 返回数量（默认100）
)
```

### similar_to - 查找相似记忆

```python
similar = api.similar_to("mem_xxx", top_k=5)
```

### get_stats - 获取统计信息

```python
stats = api.get_stats()
# 返回: {"version": "2.0.0", "total_memories": 100, ...}
```

---

## VectorAPI

向量检索API，提供语义搜索功能。

### 初始化

```python
from api import VectorAPI

api = VectorAPI()
```

### search - 向量搜索

```python
response = api.search({
    "query": "咖啡",
    "top_k": 10,
    "min_similarity": 0.7,
    "filters": {"memory_type": "preference"}
})

# 返回格式
{
    "success": True,
    "results": [...],
    "total": 10,
    "time_ms": 45.2,
    "query": "咖啡"
}
```

### embed - 生成向量

```python
response = api.embed({"text": "测试文本"})

# 返回格式
{
    "success": True,
    "embedding": [0.1, 0.2, ...],  # 384维向量
    "dimension": 384,
    "time_ms": 12.3
}
```

### batch_embed - 批量生成向量

```python
response = api.batch_embed({
    "texts": ["文本1", "文本2", "文本3"],
    "batch_size": 32
})

# 返回格式
{
    "success": True,
    "embeddings": [[...], [...], [...]],
    "count": 3,
    "total": 3,
    "time_ms": 25.6
}
```

---

## HybridAPI

混合检索API，结合向量和关键词检索。

### 初始化

```python
from api import HybridAPI

api = HybridAPI()
```

### search - 混合搜索

```python
response = api.search({
    "query": "Python编程",
    "top_k": 10,
    "min_score": 0.05,
    "vector_weight": 0.7,      # 向量权重
    "keyword_weight": 0.3,     # 关键词权重
    "use_vector": True,        # 使用向量检索
    "use_keyword": True        # 使用关键词检索
})

# 返回格式
{
    "success": True,
    "results": [...],
    "total": 10,
    "time_ms": 78.5,
    "query": "Python编程",
    "search_method": "hybrid"  # 实际使用的搜索方法
}
```

### get_search_weights - 获取权重

```python
weights = api.get_search_weights()
# 返回: {"vector_weight": 0.7, "keyword_weight": 0.3, "rrf_k": 60}
```

### set_search_weights - 设置权重

```python
response = api.set_search_weights(
    vector_weight=0.8,
    keyword_weight=0.2
)

# 返回格式
{
    "success": True,
    "weights": {"vector_weight": 0.8, "keyword_weight": 0.2, "rrf_k": 60}
}
```

---

## KeywordAPI

关键词检索API，基于文本匹配。

### 初始化

```python
from api import KeywordAPI

api = KeywordAPI()
```

### search - 关键词搜索

```python
response = api.search({
    "query": "咖啡 喜欢",
    "top_k": 10,
    "match_mode": "AND",       # "AND" | "OR"
    "case_sensitive": False,   # 区分大小写
    "filters": {"memory_type": "preference"}
})

# 返回格式
{
    "success": True,
    "results": [
        {
            "memory_id": "mem_xxx",
            "content": "安哥喜欢喝咖啡",
            "score": 1.0,
            "matched_keywords": ["喜欢", "咖啡"],
            "memory_type": "preference",
            "created_at": "2026-02-24T10:00:00",
            "metadata": {}
        }
    ],
    "total": 1,
    "time_ms": 5.2,
    "query": "咖啡 喜欢",
    "match_mode": "AND"
}
```

### add_document - 添加文档

```python
success = api.add_document(
    memory_id="mem_xxx",
    content="文档内容",
    memory_type="fact",
    importance=3.0,
    tags=["标签1", "标签2"],
    metadata={"key": "value"}
)
```

---

## MemoryAPI

记忆管理API，基础CRUD操作。

### 初始化

```python
from api import MemoryAPI

api = MemoryAPI(data_dir="./data")
```

### add_memory - 添加记忆

```python
memory_id = api.add_memory(
    content="记忆内容",
    memory_type="fact",
    importance=3.0,
    tags=["标签"]
)
```

### search - 搜索记忆

```python
results = api.search(
    query="查询",
    search_type="hybrid",
    top_k=10,
    filters={"memory_type": "fact"}
)
```

### get_memory - 获取记忆

```python
memory = api.get_memory("mem_xxx")
```

### update_memory - 更新记忆

```python
success = api.update_memory(
    "mem_xxx",
    content="新内容",
    importance=4.0
)
```

### delete_memory - 删除记忆

```python
success = api.delete_memory("mem_xxx")
```

### list_memories - 列出记忆

```python
memories = api.list_memories(
    memory_type="fact",
    limit=100,
    offset=0
)
```

---

## 错误处理

### 错误响应格式

```json
{
    "success": False,
    "results": [],
    "total": 0,
    "time_ms": 5.2,
    "query": "查询",
    "error": "错误描述"
}
```

### 常见错误码

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| 缺少必需参数 | 请求缺少必需字段 | 检查请求参数 |
| 查询文本不能为空 | query参数为空 | 提供查询文本 |
| Embedding服务不可用 | 模型未加载 | 检查模型安装 |
| 记忆不存在 | memory_id无效 | 检查ID是否正确 |

---

## 示例代码

### 示例1: 基本CRUD

```python
from api import UnifiedAPI

api = UnifiedAPI()

# 创建
mid = api.remember("安哥喜欢喝咖啡", importance=4.0)

# 读取
memory = api.recall(mid)
print(memory["content"])

# 更新
api.update(mid, content="安哥非常喜欢喝咖啡")

# 删除
api.forget(mid)
```

### 示例2: 搜索功能

```python
from api import UnifiedAPI

api = UnifiedAPI()

# 添加测试数据
api.remember("Python编程语言", "fact")
api.remember("Java编程语言", "fact")
api.remember("安哥喜欢喝咖啡", "preference")

# 向量搜索
results = api.search("编程", search_type="vector")

# 关键词搜索
results = api.search("咖啡 喜欢", search_type="keyword")

# 混合搜索
results = api.search("编程语言", search_type="hybrid")

# 自然语言查询
results = api.query("安哥喜欢什么？")
```

### 示例3: 批量操作

```python
from api import UnifiedAPI

api = UnifiedAPI()

# 批量添加
contents = [
    "记忆1",
    "记忆2",
    "记忆3"
]

memory_ids = []
for content in contents:
    mid = api.remember(content)
    memory_ids.append(mid)

# 批量搜索
for mid in memory_ids:
    memory = api.recall(mid)
    print(memory["content"])
```

### 示例4: 使用底层API

```python
from api import VectorAPI, HybridAPI, KeywordAPI

# 向量API
vector_api = VectorAPI()
response = vector_api.embed({"text": "测试"})

# 混合API
hybrid_api = HybridAPI()
response = hybrid_api.search({"query": "测试", "top_k": 5})

# 关键词API
keyword_api = KeywordAPI()
response = keyword_api.search({"query": "测试", "match_mode": "AND"})
```

---

## 性能指标

| 操作 | 平均耗时 | 说明 |
|------|----------|------|
| 添加记忆 | <10ms | 不含向量生成 |
| 向量搜索 | <100ms | 取决于数据量 |
| 关键词搜索 | <10ms | 内存检索 |
| 混合搜索 | <150ms | 向量+关键词 |
| 向量生成 | <50ms | 单文本 |

---

## 更新日志

### v2.0.0 (2026-02-24)
- 新增UnifiedAPI统一接口
- 新增自然语言查询支持
- 新增自动重要性判断
- 新增自动标签提取
- 完善API文档

---

*文档生成时间: 2026-02-24*  
*为安哥打造的零操作记忆系统*
