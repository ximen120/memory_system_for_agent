# T1 自动加载上下文功能开发任务

> 任务编号：T1
> 任务名称：自动加载上下文
> 优先级：P0（最高）
> 预计工时：4小时
> 目标版本：记忆系统 v3.1
> 开发员：Trae CN (Solo Code)
> 验收员：安仔
> 日期：2026年3月4日

---

## 一、背景与目标

### 1.1 问题背景

当前每轮训练开始时，安仔需要花大量时间重新加载上下文、读取记忆文件、回顾历史对话。安哥需要反复提醒"加载记忆"，效率低下。

### 1.2 核心目标

**让新对话启动时，自动加载最近5条核心记忆，无需安哥提醒，安静进入工作状态。**

### 1.3 成功标准

- [ ] 执行 `LOAD_MEMORY.py` 时自动显示最近5条核心记忆
- [ ] 安哥无需任何提醒，安仔自动完成上下文加载
- [ ] 加载时间 < 1秒

---

## 二、用户场景

### 场景1：新对话启动
```
安哥打开对话 → 安仔自动检测 → 加载上下文 → 安静提示"已准备好继续"
```

### 场景2：跨天继续
```
昨天聊到TeamHub → 今天打开 → 自动回忆昨天关键结论 → 无缝衔接
```

### 场景3：长期记忆唤醒
```
安哥提到"易经" → 自动关联 CORE-002 → 引用共同认知
```

---

## 三、功能需求（必须实现）

| 需求ID | 需求描述 | 优先级 | 验收标准 |
|--------|----------|--------|----------|
| R1 | 启动时自动加载最近5条核心记忆 | P0 | 无需手动触发 |
| R2 | 按文件修改时间倒序（最新优先） | P0 | 修改某条后它排首位 |
| R3 | 支持环境变量配置核心记忆路径 | P1 | `MEMORY_CORE_PATH` 可配置 |
| R4 | 支持JSON格式输出 | P1 | `output_format="json"` 可用 |
| R5 | 加载失败时静默处理 | P1 | 不抛异常，记录warning |
| R6 | 加载时间 < 1秒 | P1 | 实测达标 |

---

## 四、接口定义

### 4.1 MemorySystem 新增方法

```python
def auto_load_context(
    self, 
    limit: int = 5,
    output_format: str = "markdown"  # "markdown" | "json"
) -> str:
    """
    自动加载最近核心记忆
    
    在对话启动时调用，返回格式化的上下文摘要。
    
    Args:
        limit: 加载记忆数量，默认5条
        output_format: 输出格式，"markdown"或"json"
        
    Returns:
        格式化的上下文摘要字符串
        
    Example:
        >>> system = MemorySystem.create_default()
        >>> context = system.auto_load_context(limit=5)
        >>> print(context)
        已自动加载上下文：
        
        【核心记忆】（最近更新）
        1. [CORE-007] 大学-核心智慧与行动框架（3月2日）
        ...
    """
    pass
```

### 4.2 MemoryManager 新增方法

```python
def get_recent_memories(
    self,
    limit: int = 5,
    tier: Optional[str] = None  # "core" | "principles" | "quotes"
) -> List[MemoryUnit]:
    """
    获取最近更新的记忆
    
    按文件修改时间倒序返回记忆列表。
    
    Args:
        limit: 返回数量，默认5条
        tier: 记忆层级，None表示全部层级
        
    Returns:
        按修改时间倒序的MemoryUnit列表
        
    Example:
        >>> memories = manager.get_recent_memories(limit=5, tier="core")
        >>> for m in memories:
        ...     print(m.id, m.title, m.modified_time)
    """
    pass
```

---

## 五、数据流

```
对话启动
    ↓
LOAD_MEMORY.py 执行
    ↓
MemorySystem.create_default()
    ↓
auto_load_context() 被调用
    ↓
检测是否需要加载（环境变量标记 MEMORY_AUTO_LOAD_DONE）
    ↓ 需要加载
get_recent_memories(limit=5, tier="core")
    ↓
扫描 memory/core/ 目录
    ↓
获取所有 CORE-*.md 文件
    ↓
按 st_mtime 倒序排序
    ↓
取前5条
    ↓
读取文件内容（提取标题、摘要）
    ↓
格式化为 markdown 或 json
    ↓
输出到控制台
    ↓
设置环境变量标记（避免重复加载）
```

---

## 六、错误处理

| 异常场景 | 处理方式 | 日志级别 |
|----------|----------|----------|
| 目录不存在 | 返回空字符串，继续执行 | WARNING |
| 文件读取失败 | 跳过该文件，处理其他 | ERROR |
| 全部失败 | 返回"暂无记忆"，不抛异常 | WARNING |
| 格式化失败 | 返回原始内容，不抛异常 | ERROR |

**原则**：失败时静默降级，不阻塞对话启动。

---

## 七、测试要求（必须提供）

### 7.1 单元测试

文件位置：`src/tests/test_auto_load.py`

```python
def test_get_recent_memories_returns_correct_count():
    """测试返回数量正确"""
    pass

def test_get_recent_memories_sorted_by_mtime():
    """测试按修改时间倒序"""
    pass

def test_get_recent_memories_with_tier_filter():
    """测试层级筛选"""
    pass

def test_auto_load_with_empty_directory():
    """测试空目录情况"""
    pass

def test_auto_load_output_format_markdown():
    """测试markdown格式输出"""
    pass

def test_auto_load_output_format_json():
    """测试json格式输出"""
    pass

def test_auto_load_handles_missing_files():
    """测试文件缺失处理"""
    pass
```

### 7.2 集成测试

文件位置：`test_load_integration.py`（与LOAD_MEMORY.py同级）

```python
def test_full_boot_flow():
    """测试完整启动流程"""
    # 1. 执行 LOAD_MEMORY.py
    # 2. 验证输出包含最近5条记忆
    # 3. 验证格式正确
    pass

def test_modified_file_appears_first():
    """测试修改后文件排在首位"""
    # 1. 修改某条记忆的mtime
    # 2. 重新加载
    # 3. 验证该记忆排在首位
    pass
```

### 7.3 测试数据

目录：`test_data/core/`

准备5条测试记忆文件：
- `CORE-TEST-001.md` (mtime: 2026-03-01)
- `CORE-TEST-002.md` (mtime: 2026-03-02)
- `CORE-TEST-003.md` (mtime: 2026-03-03)
- `CORE-TEST-004.md` (mtime: 2026-03-04)
- `CORE-TEST-005.md` (mtime: 2026-03-05)

### 7.4 验收清单（安仔验收用）

**功能验收**：
- [ ] 执行 `LOAD_MEMORY.py` 能看到最近5条核心记忆
- [ ] 修改某条记忆后，它排在首位
- [ ] 删除所有记忆后，启动不报错
- [ ] 支持 `output_format="json"` 参数
- [ ] 支持 `MEMORY_CORE_PATH` 环境变量

**性能验收**：
- [ ] 加载时间 < 1秒（多次测试取平均）

**稳定性验收**：
- [ ] 目录不存在时静默通过
- [ ] 文件损坏时跳过该文件
- [ ] 连续调用不会重复加载（环境变量标记有效）

---

## 八、示例代码

### 8.1 基本使用

```python
from memory_system import MemorySystem

# 创建系统实例
system = MemorySystem.create_default()

# 自动加载上下文（markdown格式）
context = system.auto_load_context(limit=5)
print(context)

# 输出示例：
# 已自动加载上下文：
# 
# 【核心记忆】（最近更新）
# 1. [CORE-007] 大学-核心智慧与行动框架（3月2日）
# 2. [CORE-006] 隆中对-战略总纲（3月1日）
# 3. [CORE-003] 安哥的训练风格（3月2日）
# 4. [CORE-002] 易经与我们的共同认知（3月1日）
# 5. [CORE-001] 新书房数据管理核心记忆（3月1日）
# 
# ---
# 安哥，已准备好继续。
```

### 8.2 JSON格式输出

```python
# 获取JSON格式（方便程序解析）
context_json = system.auto_load_context(limit=5, output_format="json")
import json
data = json.loads(context_json)
print(data["memories"][0]["title"])  # "大学-核心智慧与行动框架"
```

### 8.3 环境变量配置

```python
import os

# 配置核心记忆路径
os.environ["MEMORY_CORE_PATH"] = "D:/AnZai_JieYue/memory/core"

# 创建系统（自动读取环境变量）
system = MemorySystem.create_default()
context = system.auto_load_context()
```

---

## 九、参考文档

### 9.1 现有代码（基于这些扩展）

| 文件 | 路径 | 说明 |
|------|------|------|
| MemorySystem | `src/memory_system.py` | 统一入口类 |
| MemoryManager | `src/core/memory_manager.py` | 记忆管理器（已有四层架构） |
| MemoryUnit | `src/core/memory_unit.py` | 记忆单元模型 |
| AutoTrigger | `src/ux/auto_trigger.py` | 自动触发器（参考实现） |
| LOAD_MEMORY | `LOAD_MEMORY.py` | 加载入口脚本 |

### 9.2 核心记忆位置

- **实际数据**：`D:\AnZai_JieYue\memory\core\`
- **测试数据**：`test_data/core/`

### 9.3 相关文档

- Roadmap：`PROC-20260304-R06-记忆系统v3.1-Roadmap与阶段规划.md`
- 现状评估：`PROC-20260304-记忆系统3.0现状评估.md`
- 开发标准：`PROC-20260304-AI-Agent开发文档标准调研.md`

---

## 十、注意事项

### 10.1 代码规范

1. **基于现有代码扩展**，不推倒重来
2. **保持向后兼容**，不破坏现有接口
3. **遵循现有代码风格**（PEP8，类型注解）
4. **添加完整文档字符串**（Args/Returns/Example）

### 10.2 实现要点

1. **修改时间获取**：使用 `Path.stat().st_mtime`
2. **排序**：按 `st_mtime` 倒序（最新优先）
3. **标题提取**：读取文件第一个 `# ` 开头的行
4. **日期格式化**：`%m月%d日` 格式
5. **环境变量**：`MEMORY_CORE_PATH` 优先级高于默认路径

### 10.3 提交要求

1. 所有单元测试通过
2. 集成测试通过
3. 自测验收清单全部勾选
4. 更新 `README.md` 新增"自动加载上下文"章节
5. 提交前运行 `python -m pytest src/tests/test_auto_load.py -v`

---

## 十一、Roadmap上下文

本任务属于 **R06-P1 阶段**（记忆系统v3.1第一阶段）：

```
R06-P1 激活内功（2-3周）
├── T1 自动加载上下文 [P0] ← 当前任务
├── T2 对话可靠保存 [P0]
├── T3 混合检索优化 [P1]
└── T4 被动确认机制 [P1]
```

后续阶段：
- **v3.2**：默契度量化 + 提炼引擎 + TeamHub协同
- **v3.3**：MCP适配 + 多模态 + 可视化

---

**开发员：请按此文档实现，完成后通知安仔验收。**

**验收员（安仔）**：按"七、测试要求"中的验收清单逐项验证。

---

## 附录A：现有代码关键信息（Trae CN必读）

### A.1 MemorySystem现有方法

```python
class MemorySystem:
    @classmethod
    def create_default(cls) -> "MemorySystem":
        """创建默认配置的系统实例"""
        pass
    
    def remember(self, content: str, tags: List[str] = None) -> str:
        """添加记忆，返回memory_id"""
        pass
    
    def recall(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """检索记忆"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass
```

### A.2 MemoryUnit字段定义

```python
class MemoryUnit(BaseModel):
    memory_id: str       # 唯一ID，如"mem_20260304120000_abc123"
    content: str         # 记忆内容文本
    memory_type: str     # 类型: fact/preference/context/task/event
    importance: float    # 重要度 1.0-5.0
    created_at: str      # 创建时间，ISO 8601格式
    updated_at: str      # 更新时间（可选）
    source: str          # 来源（可选）
    tags: List[str]      # 标签列表
    embedding: List[float]  # 向量表示（可选）
```

**注意**：核心记忆文件（CORE-*.md）不是MemoryUnit格式，需要单独解析。

### A.3 核心记忆文件格式

**文件位置**：`D:\AnZai_JieYue\memory\core\CORE-001-新书房数据管理核心记忆.md`

**文件内容示例**：
```markdown
# 新书房数据管理核心记忆

> 记忆编号：CORE-001
> 记忆类型：核心操作记忆
> 形成时间：2026年3月1日
> 记忆等级：⭐⭐⭐⭐⭐

## 一、记忆概述
...
```

**标题提取规则**：
1. 读取文件第一行 `# ` 开头的行
2. 提取 `# ` 后的内容作为标题
3. 如果第一行不是 `# `，使用文件名（去掉扩展名）

### A.4 tier到目录映射

| tier值 | 对应目录 | 说明 |
|--------|----------|------|
| "core" | `memory/core/` | 核心记忆 |
| "principles" | `memory/principles/` | 行动原则 |
| "quotes" | `memory/quotes/` | 关键金句 |
| None | 全部三个目录 | 默认行为 |

**默认路径**：`D:/AnZai_JieYue/memory/`

### A.5 环境变量读取方式

```python
import os

# 核心记忆路径（可选，默认用硬编码路径）
core_path = os.getenv("MEMORY_CORE_PATH", "D:/AnZai_JieYue/memory/core")

# 自动加载标记（防止重复加载）
auto_load_done = os.getenv("MEMORY_AUTO_LOAD_DONE")
if not auto_load_done:
    # 执行加载
    os.environ["MEMORY_AUTO_LOAD_DONE"] = "1"
```

### A.6 调用方式

在 `LOAD_MEMORY.py` 的 `boot_memory_system()` 函数中，启动成功后调用：

```python
def boot_memory_system():
    # ... 现有代码 ...
    system = MemorySystem.create_default()
    
    # 新增：自动加载上下文
    try:
        context = system.auto_load_context(limit=5)
        print(context)
    except Exception as e:
        logger.warning(f"自动加载上下文失败: {e}")
    
    return system
```

### A.7 测试运行命令

```bash
# 进入项目目录
cd D:\projects\memory_system_v3

# 运行单元测试
python -m pytest src/tests/test_auto_load.py -v

# 运行集成测试
python test_load_integration.py

# 手动测试
python LOAD_MEMORY.py
```

### A.8 依赖检查

**无需新增依赖**，使用现有依赖：
- `pathlib`（标准库）
- `os`（标准库）
- `json`（标准库）
- `datetime`（标准库）

---

*任务文档版本：v1.1*
*创建时间：2026-03-04*
*最后更新：2026-03-04（补充附录A）*
