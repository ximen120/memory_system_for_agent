# 记忆系统v3 源码维护指导

> 编制者：安仔（数字分身训练搭档）
> 日期：2026年3月2日
> 背景：基于实际部署升级过程中发现的问题
> 目标读者：Trae CN（负责源码维护和开发）
> 源码位置：D:\projects\memory_system_v3\
> 已部署skill位置：C:\Users\Simon\.stepfun\skills\memory-system-3\

---

## 一、升级过程概述

我们将记忆系统从旧版memory3_core.py升级到基于完整五层架构的新版。过程中发现了以下需要源码层面解决的问题。当前通过memory_bridge.py做了临时绕行方案，但源码本身需要修复，以便后续skill包重新打包后能直接使用。

---

## 一点五、安仔在已部署skill中做了哪些修改

以下是安仔在skill目录（C:\Users\Simon\.stepfun\skills\memory-system-3\）中做的所有修改。这些修改是为了绕过源码问题让系统先跑起来的临时方案。Trae CN需要理解每一项修改的原因，然后在源码中做出对应的正式修复，这样下次重新打包skill后就不需要再手动改了。

### 修改1：新增 scripts/memory_bridge.py（核心桥接层）

**做了什么**：新写了一个memory_bridge.py，替代原来的memory3_core.py，作为skill的统一入口。

**为什么**：原来的调用链是 scripts/api/memorize.py → UnifiedAPI → MemoryAPI，但MemoryAPI没有持久化（问题1），UnifiedAPI的data_dir传不下去（问题2），导致数据存不住。所以memory_bridge.py绕过了UnifiedAPI，直接调用底层的JsonStorage做持久化。

**源码应如何处理**：修复MemoryAPI的持久化（问题1）和UnifiedAPI的参数传递（问题2）后，memory_bridge.py应改为调用UnifiedAPI统一入口，而非直接操作JsonStorage。最终目标是memory_bridge.py只做路径配置和环境设置，业务逻辑全部走UnifiedAPI。

### 修改2：屏蔽skill/libs路径，改用conda环境的torch

**做了什么**：在memory_bridge.py开头，将skill/libs从sys.path中移除：
```python
sys.path = [p for p in sys.path if p != _libs_path]
```

**为什么**：skill/libs里打包的torch_python.dll在Windows上加载失败（问题3）。移除后Python会从conda环境的site-packages找到可用的torch。

**源码应如何处理**：两个选择——要么修复libs中的torch打包（确保与目标环境匹配），要么从libs中移除torch并在requirements.txt中声明依赖。推荐后者，因为torch体积大且平台敏感，不适合打包进skill。同时代码中应做graceful降级：torch不可用时语义检索自动降级为关键词检索，不报错。

### 修改3：设置HuggingFace离线模式

**做了什么**：在memory_bridge.py中设置环境变量：
```python
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
```

**为什么**：SentenceTransformer初始化时会联网访问huggingface.co检查模型更新，在中国网络环境下超时5分钟（问题4）。设置离线模式后直接用本地缓存，秒级加载。

**源码应如何处理**：在 `src/retrieval/embedding_service.py` 的 EmbeddingService.__init__() 中默认设置离线模式。增加 EmbeddingConfig.offline 参数（默认True），仅在用户显式设置offline=False时才联网。

### 修改4：recall()中实现语义+关键词混合检索

**做了什么**：memory_bridge.py的recall()函数中，对每条记忆同时计算关键词匹配分和语义相似度分，加权合并（语义0.7 + 关键词0.3）后排序返回。

**为什么**：源码中的HybridSearch（`src/retrieval/hybrid_search.py`）依赖ChromaDB做向量索引，但ChromaDB的初始化在当前环境下有问题（与MemoryAPI持久化问题叠加）。所以临时用遍历+逐条计算的方式实现了简易版混合检索。

**源码应如何处理**：修复MemoryAPI持久化后，HybridSearch应该能正常工作。正式方案应该是：记忆保存时同时写入JsonStorage（持久化）和ChromaDB（向量索引），检索时通过ChromaDB做向量近邻搜索（O(logN)），而非遍历所有文件逐一计算（O(N)）。当前427条记忆遍历一次需要3-5分钟，这个性能不可接受。

### 修改5：修改了scripts/api/下四个脚本的导入逻辑

**做了什么**：在memorize.py、recall.py、query.py、stats.py中，将：
```python
from api import UnifiedAPI
api = UnifiedAPI()
```
改为：
```python
from api import UnifiedAPI
from core.config_loader import Config
config = Config()
api = UnifiedAPI(data_dir=config.data_dir)
```

**为什么**：原来的代码不传data_dir，数据会存在默认位置（开源代码目录内）。修改后通过Config读取配置的数据路径。

**源码应如何处理**：这个修改的方向是对的，但实现不够优雅。建议在UnifiedAPI.__init__()内部自动读取Config，而非在每个调用脚本里都手动读取。调用方只需要 `api = UnifiedAPI()` 即可，data_dir的解析逻辑封装在UnifiedAPI内部。

### 修改6：新增 .env 配置文件

**做了什么**：在skill根目录创建了.env文件，内容：
```
DATA_DIR=D:\AnZai_JieYue\memory\data
VECTOR_DB_PATH=D:\AnZai_JieYue\memory\data\vector_db
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
LOG_LEVEL=INFO
```

**为什么**：将私有数据路径从代码中抽离到配置文件，实现数据与代码分离。

**源码应如何处理**：在config_loader.py中增加.env文件加载支持（可用python-dotenv或手动解析）。在default_config.yaml中提供.env.example模板，说明可配置项。开源代码中不包含.env文件（加入.gitignore），只包含.env.example。

---

## 二、必须修复的问题（P0）

### 问题1：MemoryAPI层无持久化

**文件**：`src/api/memory_api.py`

**现象**：MemoryAPI内部用Python字典（内存）存储记忆数据，进程结束后数据全部丢失。UnifiedAPI调用MemoryAPI.remember()保存的记忆，重启后不存在。

**根因**：MemoryAPI.__init__()中 self.memories = {} 是纯内存字典，没有接入任何Storage后端。

**修改方案**：
1. MemoryAPI初始化时接收一个storage参数（JsonStorage或ChromaStorage实例）
2. remember()方法在写入内存字典的同时，调用storage.save()持久化
3. 启动时从storage.list_all()加载已有记忆到内存字典
4. search()方法优先从内存字典检索（快），降级到storage检索（全）

**参考代码位置**：
- JsonStorage已实现完整的save/load/list_all：`src/storage/json_storage.py`
- MemoryUnit数据模型：`src/core/memory_unit.py`

**自检标准**：
```
1. 启动MemoryAPI，调用remember("测试")保存一条记忆
2. 关闭进程
3. 重新启动MemoryAPI
4. 调用search("测试")，能找到之前保存的记忆
5. 检查storage_dir下有对应的JSON文件
```

---

### 问题2：UnifiedAPI的data_dir参数传递断裂

**文件**：`src/api/unified_api.py`

**现象**：UnifiedAPI.__init__()接收data_dir参数，但没有正确传递给内部的MemoryAPI、ChromaStorage等组件。导致即使传了data_dir，数据仍然存在默认位置或内存中。

**修改方案**：
1. UnifiedAPI.__init__(data_dir=None)接收data_dir后，传递给所有子组件
2. 如果data_dir为None，从配置文件或环境变量DATA_DIR读取
3. 确保MemoryAPI、ChromaStorage、JsonStorage都使用同一个data_dir

**自检标准**：
```
1. api = UnifiedAPI(data_dir="D:/test_data")
2. api.remember("测试")
3. 检查D:/test_data/下有数据文件
4. 检查默认路径./data/下没有新数据
```

---

### 问题3：skill打包的torch依赖不兼容

**目录**：`libs/` 下的torch相关文件

**现象**：skill包中libs/目录打包了torch、torchvision等库，但其中的torch_python.dll在目标Windows环境（Python 3.11, AMD64）上加载失败。导致所有依赖torch的功能（embedding生成、语义检索）不可用。

**根因**：打包时的torch版本/编译环境与目标环境不匹配。

**修改方案（二选一）**：

方案A（推荐）：不在libs/中打包torch
- 从libs/中移除torch、torchvision、torchaudio
- 在requirements.txt中声明torch依赖
- 在SKILL.md中说明需要conda环境提供torch
- 在代码中做graceful降级：torch不可用时，语义检索降级为关键词检索

方案B：修复打包
- 确保打包的torch版本与目标环境完全匹配（Python 3.11, Windows AMD64, CPU）
- 测试torch_python.dll能正常加载

**自检标准**：
```
方案A：
1. 从libs/中删除torch相关文件
2. 在conda环境中运行：python -c "import torch; print(torch.__version__)"
3. 运行skill的memorize.py和recall.py，确认功能正常
4. 在没有torch的环境中运行，确认降级到关键词检索而非报错

方案B：
1. 重新打包torch
2. 设置PYTHONPATH只包含libs/（不含conda）
3. python -c "import torch; print(torch.__version__)" 成功
```

---

### 问题4：HuggingFace联网超时

**文件**：`src/retrieval/embedding_service.py`

**现象**：EmbeddingService._load_model()中，SentenceTransformer()初始化时会尝试联网访问huggingface.co检查模型更新。在中国网络环境下，该请求超时（约60秒×5次重试=5分钟），严重影响启动速度。

**修改方案**：
1. 在EmbeddingService.__init__()中，默认设置离线模式环境变量：
   ```python
   os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
   os.environ.setdefault("HF_HUB_OFFLINE", "1")
   ```
2. 优先从本地缓存加载模型，仅在用户显式要求时联网
3. 在EmbeddingConfig中增加offline参数，默认True

**自检标准**：
```
1. 断开网络（或设置防火墙阻断huggingface.co）
2. 确保本地有模型缓存（models/all-MiniLM-L6-v2/）
3. 运行EmbeddingService，模型应在5秒内加载完成
4. 生成embedding向量成功
```

---

## 三、应该修复的问题（P1）

### 问题5：scripts/api与src/api命名冲突

**文件**：`scripts/api/` 和 `src/api/`

**现象**：两个目录都叫api。当sys.path同时包含scripts/和src/时，`from api import UnifiedAPI`可能导入到错误的模块。

**修改方案**：
- 将scripts/api/重命名为scripts/commands/或scripts/cli/
- 或者在scripts/api/__init__.py中显式指定导入路径

**自检标准**：
```
1. sys.path同时包含scripts/和src/
2. from api import UnifiedAPI 能正确导入src/api/unified_api.py中的类
3. scripts下的命令脚本仍能正常运行
```

---

### 问题6：配置文件不支持外部数据路径

**文件**：`assets/config/default_config.yaml` 和 `src/core/config_loader.py`

**现象**：default_config.yaml中数据路径是相对路径`./data/memory_db`，不支持通过环境变量或外部配置文件覆盖。用户如果想把数据存在其他位置（如我们的新书房），必须修改源码。

**修改方案**：
1. config_loader.py中增加环境变量读取逻辑：
   ```python
   data_dir = os.environ.get("MEMORY_DATA_DIR", config.get("storage", {}).get("path", "./data"))
   ```
2. 支持.env文件加载（可选，用python-dotenv）
3. 在default_config.yaml中添加注释说明如何通过环境变量覆盖

**自检标准**：
```
1. 不设环境变量时，数据存在./data/（默认行为不变）
2. 设置MEMORY_DATA_DIR=/custom/path后，数据存在/custom/path/
3. .env文件中的配置能被正确读取
```

---

### 问题7：数据迁移兼容性

**文件**：`src/core/memory_unit.py` 和 `src/storage/json_storage.py`

**现象**：从旧系统迁移438条记忆时，14条因格式不兼容被跳过。旧数据中部分字段缺失（如memory_id、created_at），MemoryUnit初始化时报错。

**修改方案**：
1. MemoryUnit增加宽容模式：缺失字段自动填充默认值
   - memory_id缺失 → 自动生成
   - created_at缺失 → 使用文件修改时间
   - memory_type缺失 → 默认"fact"
   - importance缺失 → 默认3.0
2. JsonStorage.load()增加异常处理，格式错误时记录日志而非抛出异常
3. 提供migrate_from_v2()工具函数，专门处理旧格式数据导入

**自检标准**：
```
1. 构造一条只有content字段的最简记忆：{"content": "测试"}
2. MemoryUnit能正常初始化，自动填充其他字段
3. JsonStorage.save()和load()正常工作
4. 用旧格式数据文件测试migrate_from_v2()
```

---

## 四、建议优化的方向（P2）

### 优化1：向量索引缓存

**现状**：当前每次语义检索都需要遍历所有记忆文件，逐一生成embedding并计算相似度。427条记忆一次检索需要约3-5分钟。

**建议**：
1. 记忆保存时同时生成embedding向量，存入ChromaDB或单独的向量缓存文件
2. 检索时直接从向量索引查询，O(logN)而非O(N)
3. ChromaStorage已有代码（`src/storage/chroma_storage.py`），需要接入并验证

**预期效果**：检索时间从分钟级降到秒级

---

### 优化2：中文语义模型

**现状**：all-MiniLM-L6-v2是英文为主的模型，对中文语义理解偏弱。测试中"远光灯照路"和"开灯看方向"的相似度只有0.459，区分度不够。

**建议**：
- 评估BGE-M3或text2vec-large-chinese等中文语义模型
- 在EmbeddingConfig中支持模型切换
- 提供模型下载脚本（scripts/download_model.py已有框架）

---

### 优化3：skill包打包流程标准化

**现状**：当前skill包是手动打包，libs/中的依赖可能与目标环境不匹配。

**建议**：
1. 编写打包脚本，自动检测目标环境的Python版本和平台
2. 区分"必须打包的依赖"和"由环境提供的依赖"
3. 在SKILL.md中明确声明环境要求

---

## 五、当前临时方案说明

在源码修复之前，我们通过以下临时方案保证系统可用：

**文件**：`C:\Users\Simon\.stepfun\skills\memory-system-3\scripts\memory_bridge.py`

**临时方案内容**：
1. 屏蔽skill/libs路径，使用conda环境的torch（绕过问题3）
2. 设置HF离线模式环境变量（绕过问题4）
3. 直接使用JsonStorage做持久化（绕过问题1和2）
4. recall()中实现简单的语义+关键词混合检索（绕过向量索引缺失）

**当源码修复后**：memory_bridge.py应改为调用UnifiedAPI统一入口，而非直接操作JsonStorage。

---

## 六、修复优先级和执行顺序

| 优先级 | 问题 | 预估工作量 | 依赖 |
|--------|------|-----------|------|
| P0-1 | MemoryAPI无持久化 | 2小时 | 无 |
| P0-2 | UnifiedAPI参数传递 | 1小时 | P0-1 |
| P0-3 | torch依赖处理 | 1小时 | 无 |
| P0-4 | HF离线模式 | 30分钟 | 无 |
| P1-5 | api命名冲突 | 30分钟 | 无 |
| P1-6 | 配置外部化 | 1小时 | 无 |
| P1-7 | 数据迁移兼容 | 1小时 | P0-1 |
| P2-1 | 向量索引缓存 | 3小时 | P0-1,P0-3 |
| P2-2 | 中文语义模型 | 2小时 | P0-3 |
| P2-3 | 打包流程标准化 | 2小时 | P0-3 |

建议执行顺序：P0-3 → P0-4 → P0-1 → P0-2 → P1-5 → P1-6 → P1-7 → P2

---

## 七、全量自检清单

所有P0和P1修复完成后，执行以下端到端验证：

```
测试环境：conda环境 memory_v3 (Python 3.11, Windows AMD64)
数据目录：使用临时测试目录，不影响生产数据

1. 系统启动测试
   □ UnifiedAPI(data_dir="D:/test") 启动成功
   □ 启动时间 < 10秒（含模型加载）
   □ 无网络请求（离线模式）

2. 记忆保存测试
   □ api.remember("测试内容") 返回memory_id
   □ 数据文件出现在D:/test/目录下
   □ 文件内容包含完整的MemoryUnit字段

3. 关键词检索测试
   □ api.search("测试", search_type="keyword") 返回结果
   □ 结果包含刚保存的记忆

4. 语义检索测试
   □ api.search("试一下", search_type="semantic") 返回结果
   □ 语义相关的记忆排名高于不相关的

5. 持久化测试
   □ 关闭进程，重新启动
   □ api.search("测试") 仍能找到之前的记忆

6. 数据隔离测试
   □ 开源代码目录 D:\projects\memory_system_v3\data\ 无新增数据
   □ 所有数据只在指定的data_dir中

7. 降级测试
   □ 移除torch后，系统仍能启动
   □ 语义检索自动降级为关键词检索
   □ 无报错，有日志提示

8. 旧数据兼容测试
   □ 用旧格式数据（只有content字段）导入成功
   □ 缺失字段自动填充默认值
```

---

*文档位置：D:\AnZai_JieYue\02-Plans\TASK-20260302-记忆系统源码维护指导.md*
*同步副本：D:\projects\memory_system_v3\MAINTENANCE_GUIDE.md*
