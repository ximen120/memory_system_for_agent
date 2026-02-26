# Embedding模型预下载方案

**版本**: v1.0  
**日期**: 2026-02-24  
**目标**: 解决模型下载慢的问题

---

## 问题描述

**现象**: Embedding模型下载耗时5-10分钟，导致测试超时  
**影响**: 无法自动化测试，首次启动体验差  
**根本原因**: 
1. 模型文件大（~80MB）
2. 从HuggingFace下载，国内网络慢
3. 每次启动都检查/下载模型

---

## 解决方案

### 方案1: 预下载脚本（推荐）

**思路**: 在项目初始化时预下载模型，避免运行时下载

**实现**:
```bash
# 预下载
python scripts/download_model.py --model all-MiniLM-L6-v2

# 验证
python scripts/download_model.py --verify

# 查看缓存
python scripts/download_model.py --list
```

**优点**:
- 一次性下载，重复使用
- 支持断点续传
- 支持重试机制
- 清晰的进度显示

**缺点**:
- 首次 setup 需要额外时间

### 方案2: 延迟加载

**思路**: 首次使用时才加载模型，避免启动阻塞

**实现**:
```python
class EmbeddingService:
    def __init__(self):
        self._model = None
        self._is_loaded = False
    
    def _load_model(self):
        if self._is_loaded:
            return
        # 延迟加载
        self._model = SentenceTransformer(self.model_name)
        self._is_loaded = True
```

**优点**:
- 启动速度快
- 按需加载

**缺点**:
- 首次检索有延迟

### 方案3: 模型缓存

**思路**: 下载后缓存到本地，避免重复下载

**实现**:
```python
# 检查本地缓存
cache_path = Path("./models") / model_name
if cache_path.exists():
    model = SentenceTransformer(str(cache_path))
else:
    # 下载并缓存
    model = SentenceTransformer(model_name)
    model.save(str(cache_path))
```

**优点**:
- 自动缓存
- 无需手动管理

**缺点**:
- 首次仍需下载

### 方案4: 降级方案

**思路**: 模型不可用时，自动降级到关键词检索

**实现**:
```python
def search(self, query):
    if not self.embedding_service.is_available():
        logger.warning("Embedding不可用，使用关键词检索")
        return self.keyword_search.search(query)
    # 正常向量检索
```

**优点**:
- 系统可用性高
-  graceful degradation

**缺点**:
- 检索质量下降

---

## 推荐方案组合

**组合**: 预下载 + 延迟加载 + 模型缓存 + 降级方案

```
启动流程:
    1. 检查本地缓存
       ├── 存在 -> 直接使用
       └── 不存在 -> 延迟加载（首次使用时下载）

运行流程:
    1. 接收查询
    2. 检查Embedding服务
       ├── 可用 -> 向量检索
       └── 不可用 -> 降级到关键词检索
```

---

## 实施步骤

### Step 1: 创建预下载脚本

**文件**: `scripts/download_model.py`

**功能**:
- 下载指定模型
- 保存到本地缓存
- 支持断点续传
- 支持重试机制
- 验证模型完整性

### Step 2: 修改EmbeddingService

**文件**: `src/retrieval/embedding_service.py`

**修改**:
1. 添加延迟加载机制
2. 添加本地缓存检查
3. 添加降级处理

### Step 3: 更新安装流程

**文件**: `README.md`

**添加**:
```bash
# 安装依赖后，预下载模型
pip install -r requirements.txt
python scripts/download_model.py
```

### Step 4: CI/CD配置

**文件**: `.github/workflows/ci.yml`

**配置**:
```yaml
- name: Cache Embedding Model
  uses: actions/cache@v3
  with:
    path: ./models
    key: models-all-minilm-l6-v2
```

---

## 使用指南

### 开发环境

```bash
# 1. 克隆项目
git clone <repo>
cd memory_system_v3

# 2. 安装依赖
pip install -r requirements.txt

# 3. 预下载模型（推荐）
python scripts/download_model.py

# 4. 验证
python scripts/download_model.py --verify
```

### 生产环境

```bash
# Docker构建时预下载
RUN python scripts/download_model.py --model all-MiniLM-L6-v2
```

### 离线环境

```bash
# 在有网络的环境下载
python scripts/download_model.py --output ./models

# 复制模型到离线环境
cp -r ./models <offline_machine>

# 离线环境配置
export MODEL_PATH=/path/to/models
```

---

## 模型管理

### 查看已缓存模型

```bash
python scripts/download_model.py --list
```

输出:
```
已缓存的模型 (./models):
  all-MiniLM-L6-v2 (85.2 MB)
  bge-large-zh (420.5 MB)
```

### 删除模型缓存

```bash
rm -rf ./models/all-MiniLM-L6-v2
```

### 更新模型

```bash
# 删除旧版本
rm -rf ./models/all-MiniLM-L6-v2

# 下载新版本
python scripts/download_model.py --model all-MiniLM-L6-v2
```

---

## 性能指标

| 场景 | 时间 | 说明 |
|------|------|------|
| 首次下载 | 3-10分钟 | 取决于网络 |
| 本地加载 | 1-3秒 | 从缓存加载 |
| 延迟加载 | 3-10秒 | 首次使用时 |
| 降级检索 | <100ms | 关键词检索 |

---

## 风险与应对

| 风险 | 影响 | 应对方案 |
|------|------|----------|
| 下载失败 | 高 | 重试机制 + 降级方案 |
| 磁盘空间不足 | 中 | 清理旧模型 + 磁盘检查 |
| 模型损坏 | 低 | 校验和验证 + 重新下载 |
| 版本不兼容 | 低 | 版本锁定 + 兼容性测试 |

---

## 交付物

| 文件 | 路径 | 说明 |
|------|------|------|
| 预下载脚本 | `scripts/download_model.py` | 模型下载工具 |
| Embedding服务 | `src/retrieval/embedding_service.py` | 延迟加载实现 |
| 使用文档 | `docs/M2_EMBEDDING_PRELOAD.md` | 本方案文档 |

---

*方案设计完成时间: 2026-02-24*  
*为安哥打造的零操作记忆系统*
