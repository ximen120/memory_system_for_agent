# M2向量检索API实施方案

**版本**: v1.0  
**日期**: 2026-02-24  
**负责人**: 安仔  
**阶段**: Week 3-5 [M2] 向量检索

---

## 目标

实现基于向量嵌入的记忆检索功能，支持语义搜索。

---

## 实施步骤

### Phase 1: 基础设施 (2天)

#### 1.1 Embedding服务封装
- [ ] 封装EmbeddingGenerator为服务类
- [ ] 实现模型延迟加载机制
- [ ] 添加模型缓存管理
- [ ] 实现降级方案（模型不可用时使用关键词检索）

**文件**: `src/retrieval/embedding_service.py`

```python
class EmbeddingService:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = None
        self.model_name = model_name
        self._load_model_lazy()
    
    def _load_model_lazy(self):
        # 延迟加载，避免启动时阻塞
        pass
    
    def generate(self, text: str) -> List[float]:
        # 生成embedding
        pass
    
    def is_available(self) -> bool:
        # 检查模型是否可用
        pass
```

#### 1.2 向量存储适配器
- [ ] 实现ChromaDB存储适配器
- [ ] 添加向量索引管理
- [ ] 实现批量插入和查询
- [ ] 添加相似度阈值配置

**文件**: `src/storage/chroma_adapter.py`

---

### Phase 2: 检索API (3天)

#### 2.1 向量检索接口
- [ ] 实现语义搜索接口
- [ ] 支持Top-K检索
- [ ] 添加相似度过滤
- [ ] 实现结果排序

**文件**: `src/retrieval/vector_search.py`

```python
class VectorSearch:
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_similarity: float = 0.7
    ) -> List[SearchResult]:
        pass
```

#### 2.2 混合检索
- [ ] 结合向量检索和关键词检索
- [ ] 实现结果融合算法
- [ ] 支持权重调整

**文件**: `src/retrieval/hybrid_search.py`

---

### Phase 3: API封装 (2天)

#### 3.1 基础API
- [ ] 封装记忆添加API
- [ ] 封装记忆查询API
- [ ] 封装记忆删除API
- [ ] 添加API文档

**文件**: `src/api/memory_api.py`

```python
class MemoryAPI:
    def add_memory(self, content: str, **metadata) -> str:
        pass
    
    def search_memories(self, query: str, **filters) -> List[Memory]:
        pass
    
    def delete_memory(self, memory_id: str) -> bool:
        pass
```

#### 3.2 与M6集成
- [ ] 在AutoTrigger中集成向量检索
- [ ] 在KeywordSearch中添加向量检索选项
- [ ] 更新CommandParser支持语义查询

---

## 技术方案

### 架构图

```
用户输入
    ↓
CommandParser (自然语言解析)
    ↓
HybridSearch (混合检索)
    ├── VectorSearch (语义检索)
    │       └── EmbeddingService
    │               └── sentence-transformers
    └── KeywordSearch (关键词检索)
    ↓
结果融合
    ↓
返回结果
```

### 关键技术决策

| 决策 | 方案 | 理由 |
|------|------|------|
| Embedding模型 | all-MiniLM-L6-v2 | 轻量、快速、效果好 |
| 向量数据库 | ChromaDB | 本地运行、无需服务器 |
| 相似度算法 | 余弦相似度 | 标准做法 |
| 降级方案 | 关键词检索 | 模型不可用时可用 |

---

## 测试计划

### 单元测试
- [ ] EmbeddingService测试
- [ ] VectorSearch测试
- [ ] HybridSearch测试
- [ ] MemoryAPI测试

### 集成测试
- [ ] 端到端检索流程
- [ ] 混合检索效果
- [ ] 降级方案验证

### 性能测试
- [ ] 检索响应时间 < 500ms
- [ ] 批量插入性能
- [ ] 内存占用监控

---

## 风险与应对

| 风险 | 影响 | 应对方案 |
|------|------|----------|
| 模型下载慢 | 高 | 预下载/延迟加载/本地缓存 |
| Windows文件锁定 | 中 | 内存模式/改进清理逻辑 |
| 向量检索效果差 | 中 | 调参/混合检索/反馈优化 |
| 内存占用高 | 中 | 模型量化/分批加载 |

---

## 交付物

| 交付物 | 路径 | 说明 |
|--------|------|------|
| Embedding服务 | `src/retrieval/embedding_service.py` | 模型封装 |
| 向量检索 | `src/retrieval/vector_search.py` | 语义搜索 |
| 混合检索 | `src/retrieval/hybrid_search.py` | 融合检索 |
| API封装 | `src/api/memory_api.py` | 统一接口 |
| 测试脚本 | `tests/test_vector_*.py` | 单元测试 |
| 集成测试 | `tests/integration/test_m2_*.py` | 集成测试 |

---

## 时间线

| 阶段 | 任务 | 预计工时 | 开始 | 结束 |
|------|------|----------|------|------|
| Phase 1 | 基础设施 | 2天 | Day 1 | Day 2 |
| Phase 2 | 检索API | 3天 | Day 3 | Day 5 |
| Phase 3 | API封装 | 2天 | Day 6 | Day 7 |
| 测试 | 全面测试 | 2天 | Day 8 | Day 9 |
| 文档 | 文档整理 | 1天 | Day 10 | Day 10 |

**总计**: 10天 (Week 3-5)

---

## 验收标准

- [ ] Embedding服务可用，延迟加载正常
- [ ] 向量检索准确率 > 80%
- [ ] 混合检索效果优于单一检索
- [ ] 检索响应时间 < 500ms
- [ ] 降级方案可用
- [ ] 所有测试通过

---

## 下一步行动

1. **立即开始**: Phase 1 - Embedding服务封装
2. **准备环境**: 预下载Embedding模型
3. **并行任务**: 调研ChromaDB内存模式

---

*为安哥打造的零操作记忆系统*  
*M2向量检索API实施方案*
