# M2向量检索API完整实施计划

**版本**: v2.0  
**日期**: 2026-02-24  
**负责人**: 安仔  
**阶段**: Week 3-5 [M2] 向量检索

---

## 执行摘要

**目标**: 实现基于向量嵌入的语义检索功能  
**时间**: 10天  
**关键成果**: 向量检索API + 混合检索 + 降级方案  
**阻塞问题**: Embedding模型下载慢、ChromaDB Windows文件锁定  
**解决方案**: 预下载脚本 + 内存模式

---

## 项目背景

### 当前状态
- ✅ M1基础设施: 已完成
- ✅ M6傻瓜层: 已完成
- ⏳ M2向量检索: 待开始

### 阻塞问题
| 问题 | 影响 | 解决方案 |
|------|------|----------|
| Embedding模型下载慢 | 高 | 预下载脚本 + 延迟加载 + 缓存 |
| ChromaDB Windows文件锁定 | 中 | 内存模式 + 显式连接管理 |

---

## 实施计划

### Phase 1: 基础设施 (2天)

#### Day 1: Embedding服务

**任务**:
- [ ] 创建`src/retrieval/embedding_service.py`
- [ ] 实现延迟加载机制
- [ ] 实现模型缓存管理
- [ ] 实现降级方案
- [ ] 编写单元测试

**交付物**:
```python
class EmbeddingService:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        pass
    
    def generate(self, text: str) -> Optional[List[float]]:
        pass
    
    def generate_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        pass
    
    def is_available(self) -> bool:
        pass
```

**验收标准**:
- [ ] 延迟加载正常工作
- [ ] 本地缓存可用
- [ ] 降级方案测试通过
- [ ] 单元测试覆盖率>90%

#### Day 2: ChromaDB适配器

**任务**:
- [ ] 更新`src/storage/chroma_storage.py`
- [ ] 添加内存模式支持
- [ ] 添加显式连接管理
- [ ] 添加向量索引管理
- [ ] 编写单元测试

**交付物**:
```python
class ChromaStorage:
    def __init__(self, memory_mode=None):
        pass
    
    def add_vector(self, id, vector, metadata):
        pass
    
    def similarity_search(self, query_vector, top_k, min_similarity):
        pass
    
    def close(self):
        pass
```

**验收标准**:
- [ ] 内存模式正常工作
- [ ] Windows文件锁定问题解决
- [ ] 向量搜索功能正常
- [ ] 单元测试覆盖率>90%

---

### Phase 2: 检索API (3天)

#### Day 3: 向量检索

**任务**:
- [ ] 创建`src/retrieval/vector_search.py`
- [ ] 实现语义搜索接口
- [ ] 实现Top-K检索
- [ ] 实现相似度过滤
- [ ] 编写单元测试

**交付物**:
```python
class VectorSearch:
    def search(self, query, top_k, min_similarity, filters):
        pass
    
    def add_document(self, memory_id, content, metadata):
        pass
```

**验收标准**:
- [ ] 语义搜索准确率>80%
- [ ] Top-K检索正确
- [ ] 相似度过滤有效
- [ ] 单元测试覆盖率>85%

#### Day 4-5: 混合检索

**任务**:
- [ ] 创建`src/retrieval/hybrid_search.py`
- [ ] 实现RRF融合算法
- [ ] 实现权重调整
- [ ] 实现结果排序
- [ ] 编写单元测试

**交付物**:
```python
class HybridSearch:
    def search(self, query, top_k, use_vector, use_keyword):
        pass
    
    def _fuse_results(self, vector_results, keyword_results):
        pass
```

**验收标准**:
- [ ] 混合检索效果优于单一检索
- [ ] RRF算法正确实现
- [ ] 权重调整有效
- [ ] 单元测试覆盖率>85%

---

### Phase 3: API封装 (2天)

#### Day 6: 基础API

**任务**:
- [ ] 创建`src/api/memory_api.py`
- [ ] 实现统一接口
- [ ] 实现错误处理
- [ ] 编写API文档
- [ ] 编写单元测试

**交付物**:
```python
class MemoryAPI:
    def add_memory(self, content, **metadata):
        pass
    
    def search(self, query, search_type, top_k, filters):
        pass
    
    def delete_memory(self, memory_id):
        pass
    
    def update_memory(self, memory_id, **updates):
        pass
```

**验收标准**:
- [ ] 所有接口正常工作
- [ ] 错误处理完善
- [ ] API文档清晰
- [ ] 单元测试覆盖率>85%

#### Day 7: M6集成

**任务**:
- [ ] 更新`src/ux/auto_trigger.py`集成向量检索
- [ ] 更新`src/ux/keyword_search.py`添加向量选项
- [ ] 更新`src/ux/command_parser.py`支持语义查询
- [ ] 编写集成测试

**交付物**:
- 更新后的M6模块
- 集成测试脚本

**验收标准**:
- [ ] M6模块集成成功
- [ ] 向量检索可通过自然语言调用
- [ ] 集成测试通过

---

### Phase 4: 测试与优化 (2天)

#### Day 8: 全面测试

**任务**:
- [ ] 端到端测试
- [ ] 性能测试
- [ ] 降级方案测试
- [ ] 边界情况测试

**测试用例**:
| 测试类型 | 用例数 | 目标通过率 |
|----------|--------|------------|
| 单元测试 | 50+ | 90% |
| 集成测试 | 20+ | 85% |
| 性能测试 | 10+ | 100% |

**验收标准**:
- [ ] 所有测试通过
- [ ] 检索响应时间<500ms
- [ ] 降级方案可用

#### Day 9: 性能优化

**任务**:
- [ ] 批量处理优化
- [ ] 缓存策略优化
- [ ] 内存占用优化
- [ ] 响应时间优化

**性能目标**:
| 指标 | 目标 | 当前 |
|------|------|------|
| 检索响应 | <500ms | 待测 |
| 批量插入 | >100条/s | 待测 |
| 内存占用 | <500MB | 待测 |

---

### Phase 5: 文档与交付 (1天)

#### Day 10: 文档整理

**任务**:
- [ ] 更新README
- [ ] 编写M2使用指南
- [ ] 编写API参考文档
- [ ] 更新项目状态
- [ ] 生成M2完成报告

**交付物**:
| 文档 | 路径 |
|------|------|
| M2使用指南 | `docs/M2_USER_GUIDE.md` |
| API参考 | `docs/M2_API_REFERENCE.md` |
| 完成报告 | `M2_COMPLETION_REPORT.md` |

---

## 技术架构

### 整体架构

```
用户交互层 (M6)
    ↓
MemoryAPI (统一接口)
    ↓
HybridSearch (混合检索)
    ├── VectorSearch (语义检索)
    │       └── EmbeddingService
    │               └── sentence-transformers
    └── KeywordSearch (关键词检索)
    ↓
ChromaStorage (向量存储)
```

### 数据流

```
添加记忆:
    用户输入 → MemoryAPI.add_memory()
    → [并行] JSON存储 + 向量生成 + 向量存储
    → 返回 memory_id

搜索记忆:
    用户查询 → MemoryAPI.search()
    → HybridSearch.search()
    → [并行] VectorSearch + KeywordSearch
    → 结果融合 (RRF)
    → 返回排序结果
```

---

## 风险管理

### 技术风险

| 风险 | 概率 | 影响 | 应对方案 | 负责人 |
|------|------|------|----------|--------|
| 模型下载失败 | 中 | 高 | 预下载+重试+降级 | 安仔 |
| Windows文件锁定 | 低 | 中 | 内存模式+显式关闭 | 安仔 |
| 向量检索效果差 | 低 | 中 | 调参+混合检索 | 安仔 |
| 性能不达标 | 中 | 中 | 缓存+批量+异步 | 安仔 |

### 进度风险

| 风险 | 概率 | 影响 | 应对方案 |
|------|------|------|----------|
| 开发延期 | 中 | 中 | 预留缓冲时间 |
| 测试不通过 | 低 | 高 | 增加测试时间 |
| 集成问题 | 低 | 中 | 提前集成测试 |

---

## 质量保证

### 测试策略

| 测试类型 | 覆盖率目标 | 工具 |
|----------|------------|------|
| 单元测试 | >90% | pytest |
| 集成测试 | >85% | pytest |
| 性能测试 | 100% | pytest-benchmark |

### Code Review

- [ ] 每个模块完成后进行review
- [ ] 关键代码双人review
- [ ] 性能敏感代码专项review

---

## 资源需求

### 人力资源
- 开发: 安仔 (10天全职)

### 硬件资源
- 开发机: Windows PC
- 测试环境: 本地
- 存储: ~500MB (模型+数据)

### 软件资源
- Python 3.11+
- sentence-transformers
- ChromaDB
- pytest

---

## 交付清单

### 代码交付

| 模块 | 文件 | 状态 |
|------|------|------|
| Embedding服务 | `src/retrieval/embedding_service.py` | ⏳ |
| 向量检索 | `src/retrieval/vector_search.py` | ⏳ |
| 混合检索 | `src/retrieval/hybrid_search.py` | ⏳ |
| API封装 | `src/api/memory_api.py` | ⏳ |
| ChromaDB适配器 | `src/storage/chroma_storage.py` | ⏳ |

### 文档交付

| 文档 | 路径 | 状态 |
|------|------|------|
| 架构设计 | `docs/M2_ARCHITECTURE_DESIGN.md` | ✅ |
| Embedding预下载 | `docs/M2_EMBEDDING_PRELOAD.md` | ✅ |
| ChromaDB内存模式 | `docs/M2_CHROMADB_MEMORY_MODE.md` | ✅ |
| 实施计划 | `docs/M2_IMPLEMENTATION_PLAN_FULL.md` | ✅ |
| 使用指南 | `docs/M2_USER_GUIDE.md` | ⏳ |
| API参考 | `docs/M2_API_REFERENCE.md` | ⏳ |

### 工具交付

| 工具 | 路径 | 状态 |
|------|------|------|
| 模型预下载脚本 | `scripts/download_model.py` | ✅ |

---

## 验收标准

### 功能验收

- [ ] Embedding服务可用，延迟加载正常
- [ ] 向量检索准确率>80%
- [ ] 混合检索效果优于单一检索
- [ ] 降级方案可用
- [ ] M6集成成功

### 性能验收

- [ ] 检索响应时间<500ms
- [ ] 批量插入>100条/s
- [ ] 内存占用<500MB

### 质量验收

- [ ] 单元测试覆盖率>90%
- [ ] 集成测试通过率>85%
- [ ] 所有文档完整

---

## 下一步行动

### 立即执行 (Day 1)

1. **环境准备**
   ```bash
   # 预下载模型
   python scripts/download_model.py
   
   # 验证模型
   python scripts/download_model.py --verify
   ```

2. **开始开发**
   - 创建`src/retrieval/embedding_service.py`
   - 实现延迟加载机制

### 本周目标 (Day 1-5)

- [ ] 完成Phase 1: 基础设施
- [ ] 完成Phase 2: 检索API
- [ ] 开始Phase 3: API封装

### 下周目标 (Day 6-10)

- [ ] 完成Phase 3: API封装
- [ ] 完成Phase 4: 测试与优化
- [ ] 完成Phase 5: 文档与交付

---

## 沟通计划

### 日报
- 每日进度更新
- 阻塞问题汇报
- 下一步计划

### 周报
- 本周完成情况
- 下周计划
- 风险提示

---

## 附录

### A. 参考文档

- [M2架构设计](M2_ARCHITECTURE_DESIGN.md)
- [Embedding预下载方案](M2_EMBEDDING_PRELOAD.md)
- [ChromaDB内存模式方案](M2_CHROMADB_MEMORY_MODE.md)

### B. 相关链接

- [sentence-transformers文档](https://www.sbert.net/)
- [ChromaDB文档](https://docs.trychroma.com/)
- [RRF算法论文](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)

---

*实施计划完成时间: 2026-02-24*  
*为安哥打造的零操作记忆系统*
