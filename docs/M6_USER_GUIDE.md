# M6傻瓜层使用指南

**版本**: v3.0  
**更新日期**: 2026-02-24  
**适用对象**: 安哥

---

## 目录

1. [功能概述](#功能概述)
2. [快速开始](#快速开始)
3. [六大模块详解](#六大模块详解)
4. [使用示例](#使用示例)
5. [常见问题](#常见问题)

---

## 功能概述

M6傻瓜层是安仔记忆系统的用户交互层，设计理念是**"安哥只用说话，剩下的安仔搞定"**。

### 核心能力

- **全自动**: 自动判断什么该记，自动保存
- **自然语言**: 用日常说话方式管理记忆
- **零配置**: 开箱即用，无需设置
- **自修复**: 出问题自动处理

---

## 快速开始

### 1. 安装

```bash
# 克隆项目
git clone <repository>
cd memory_system_v3

# 安装依赖
pip install -r requirements.txt
```

### 2. 基本使用

```python
from src.ux.memory_layers import create_memory_layers

# 创建记忆管理器
manager = create_memory_layers(data_dir="./data")

# 添加记忆（自动分层）
memory_id = manager.add(
    content="安哥喜欢喝美式咖啡",
    memory_type="preference",
    importance=4.0
)

# 搜索记忆
results = manager.search_by_keywords(["咖啡"])
for r in results:
    print(r.content)
```

### 3. 自然语言交互

```python
from src.ux.command_parser import CommandParser
from src.ux.auto_trigger import AutoTrigger

# 解析自然语言命令
parser = CommandParser()

# "记住..."
cmd = parser.parse("记住安哥下周要开会")
print(cmd.command_type)  # -> CommandType.REMEMBER

# "查找..."
cmd = parser.parse("查找关于项目的记忆")
print(cmd.command_type)  # -> CommandType.SEARCH

# "忘掉..."
cmd = parser.parse("忘掉昨天的临时记录")
print(cmd.command_type)  # -> CommandType.FORGET
```

---

## 六大模块详解

### 1. AutoTrigger - 自动触发器

**功能**: 智能判断何时保存记忆

**工作原理**:
- 分析内容重要性
- 识别关键词（"记住"、"喜欢"、"计划"等）
- 计算置信度，自动决定是否保存

**使用示例**:

```python
from src.ux.auto_trigger import AutoTrigger

trigger = AutoTrigger()

# 测试不同内容
test_cases = [
    "安哥喜欢喝咖啡",           # -> 触发保存 (包含"喜欢")
    "记住下周的会议",           # -> 触发保存 (包含"记住")
    "今天天气不错",             # -> 可能不触发
    "好的",                     # -> 不触发 (太短)
]

for content in test_cases:
    decision = trigger.should_save(content)
    print(f"'{content}' -> 保存: {decision.should_save}, 置信度: {decision.confidence}")
```

**配置选项**:

```python
trigger = AutoTrigger(
    min_content_length=10,      # 最小内容长度
    max_content_length=500,     # 最大内容长度
    min_confidence=0.6          # 最小置信度阈值
)
```

---

### 2. TagManager - 标签管理器

**功能**: 自动提取和管理标签

**特性**:
- 自动从内容提取关键词
- 预定义标签分类
- 支持手动添加标签

**使用示例**:

```python
from src.ux.tag_manager import TagManager

tag_mgr = TagManager()

# 自动提取标签
content = "安哥计划下周学习Python编程"
tags = tag_mgr.auto_extract_tags(content)
print(tags)  # -> ['计划', '学习', 'Python', '编程']

# 添加预定义标签
all_tags = tag_mgr.suggest_tags(content)
print(all_tags)  # 包含自动提取 + 预定义匹配的标签
```

**预定义标签分类**:

| 分类 | 标签 | 关键词 |
|------|------|--------|
| 领域 | 工作 | 工作、项目、会议、报告 |
| 领域 | 生活 | 生活、家庭、朋友、日常 |
| 领域 | 学习 | 学习、课程、读书、知识 |
| 优先级 | 重要 | 重要、关键、紧急 |
| 状态 | 待办 | 待办、计划、安排 |
| 偏好 | 喜好 | 喜欢、爱好、偏好 |

---

### 3. KeywordSearch - 关键词检索

**功能**: 基于关键词的记忆检索

**特性**:
- 多关键词组合搜索
- 支持AND/OR模式
- 模糊匹配
- 结果排序

**使用示例**:

```python
from src.ux.keyword_search import KeywordSearch

# 创建检索器
search = KeywordSearch()

# 添加记忆
search.add_memories([
    {"content": "安哥喜欢Python", "tags": ["编程"]},
    {"content": "安哥喝咖啡", "tags": ["生活"]},
])

# 搜索
results = search.search(
    keywords=["安哥", "Python"],
    match_mode="AND"  # 或 "OR"
)

for result in results:
    print(f"{result.memory['content']} (相关度: {result.score:.2f})")
```

---

### 4. CommandParser - 命令解析器

**功能**: 将自然语言解析为结构化命令

**支持的命令**:

| 命令类型 | 关键词 | 示例 |
|----------|--------|------|
| REMEMBER | 记住、记得、记录、保存 | "记住安哥喜欢咖啡" |
| FORGET | 忘掉、忘记、删除、移除 | "忘掉昨天的记录" |
| SEARCH | 查找、搜索、查询 | "查找关于项目的记忆" |
| SHOW | 显示、列出、查看 | "显示所有记忆" |
| UPDATE | 更新、修改 | "更新昨天的记录" |
| TAG | 标签 | "给这个添加标签" |

**使用示例**:

```python
from src.ux.command_parser import CommandParser, CommandType

parser = CommandParser()

# 解析命令
test_commands = [
    "记住安哥喜欢喝咖啡",
    "查找Python相关的记忆",
    "忘掉昨天的临时记录",
    "显示最近一周的记忆",
]

for cmd_text in test_commands:
    parsed = parser.parse(cmd_text)
    print(f"'{cmd_text}'")
    print(f"  类型: {parsed.command_type.value}")
    print(f"  内容: {parsed.content}")
    print(f"  置信度: {parsed.confidence:.2f}")
    print()
```

---

### 5. TimelineViewer - 时间线浏览器

**功能**: 按时间顺序查看记忆

**特性**:
- 按天分组显示
- 支持时间范围筛选
- 多种时间范围选项

**使用示例**:

```python
from src.ux.timeline_viewer import TimelineViewer, TimeRange

viewer = TimelineViewer()

# 添加记忆
viewer.add_memories([
    {"content": "今天学习了Python", "created_at": "2026-02-24T10:00:00"},
    {"content": "完成了项目文档", "created_at": "2026-02-24T14:00:00"},
])

# 查看时间线
timeline = viewer.get_timeline(TimeRange.TODAY)

for group in timeline.groups:
    print(f"\n=== {group.date} ({group.count}条) ===")
    for item in group.items:
        print(f"  [{item.memory_type}] {item.content}")
```

**支持的时间范围**:

- `TODAY` - 今天
- `YESTERDAY` - 昨天
- `THIS_WEEK` - 本周
- `LAST_WEEK` - 上周
- `THIS_MONTH` - 本月
- `ALL` - 全部

---

### 6. MemoryLayers - 四层记忆架构

**功能**: 自动分层管理记忆

**四层架构**:

| 层级 | 名称 | 时间范围 | 重要性 | 容量 |
|------|------|----------|--------|------|
| Working | 工作记忆 | 1天内 | >=1.0 | 100条 |
| Short-Term | 短期记忆 | 7天内 | >=1.0 | 1000条 |
| Long-Term | 长期记忆 | 30天内 | >=3.0 | 5000条 |
| Permanent | 永久记忆 | 无限制 | >=4.5 | 无限制 |

**自动流转逻辑**:

- **晋升**: 高频访问 + 高重要性 → 自动晋升到更高层
- **降级**: 长时间未访问 → 自动降级到更低层

**使用示例**:

```python
from src.ux.memory_layers import create_memory_layers, MemoryLayerType

# 创建四层记忆管理器
manager = create_memory_layers(data_dir="./data")

# 添加记忆（自动根据重要性分层）
# 重要性5.0 -> Permanent层
manager.add("安哥是Simon", "fact", importance=5.0)

# 重要性4.0 -> Long-Term层
manager.add("安哥喜欢咖啡", "preference", importance=4.0)

# 重要性2.0 -> Short-Term层
manager.add("今天天气不错", "context", importance=2.0)

# 查看统计
stats = manager.get_stats()
print(f"总记忆数: {stats['total_memories']}")
for layer_name, layer_stat in stats['layers'].items():
    print(f"  {layer_name}: {layer_stat['count']}条")

# 跨层搜索
results = manager.search_by_keywords(["安哥"])
print(f"\n找到 {len(results)} 条包含'安哥'的记忆")

# 获取时间线
timeline = manager.get_timeline(days=7)
print(f"\n最近7天有 {len(timeline)} 条记忆")

# 执行自动流转
migration_stats = manager.run_migration()
print(f"\n自动流转: 晋升 {migration_stats['promotions']} 条, 降级 {migration_stats['demotions']} 条")
```

---

## 使用示例

### 完整工作流示例

```python
from src.ux.memory_layers import create_memory_layers
from src.ux.auto_trigger import AutoTrigger
from src.ux.command_parser import CommandParser
from src.ux.tag_manager import TagManager

# 初始化
manager = create_memory_layers(data_dir="./data")
trigger = AutoTrigger()
parser = CommandParser()
tag_mgr = TagManager()

# 场景1: 自动保存重要信息
user_input = "安哥计划下周学习Rust编程语言"

# 1. 判断是否保存
decision = trigger.should_save(user_input)
if decision.should_save:
    print(f"检测到重要内容 (置信度: {decision.confidence:.2f})")
    
    # 2. 自动提取标签
    tags = tag_mgr.auto_extract_tags(user_input)
    print(f"自动标签: {tags}")
    
    # 3. 保存到记忆层
    memory_id = manager.add(
        content=user_input,
        memory_type="goal",
        importance=4.5,
        tags=tags
    )
    print(f"已保存 (ID: {memory_id[:20]}...)")

# 场景2: 自然语言查询
query = "查找关于Rust的记忆"
parsed = parser.parse(query)

if parsed.command_type.value == "search":
    results = manager.search_by_keywords(["Rust"])
    print(f"\n找到 {len(results)} 条相关记忆:")
    for r in results:
        print(f"  - {r.content}")

# 场景3: 查看时间线
timeline = manager.get_timeline(days=7)
print(f"\n最近7天记忆:")
for item in timeline[:5]:
    print(f"  [{item['layer']}] {item['content'][:40]}...")
```

---

## 常见问题

### Q1: 如何调整自动保存的敏感度？

```python
# 降低阈值，更容易触发保存
trigger = AutoTrigger(min_confidence=0.5)

# 提高阈值，更严格
trigger = AutoTrigger(min_confidence=0.8)
```

### Q2: 如何手动指定记忆层级？

```python
from src.ux.memory_layers import MemoryLayerType

# 强制保存到特定层
memory_id = manager.add(
    content="重要信息",
    memory_type="fact",
    importance=5.0,
    layer=MemoryLayerType.PERMANENT  # 强制到永久层
)
```

### Q3: 如何批量导入记忆？

```python
memories = [
    {"content": "记忆1", "type": "fact", "importance": 3.0},
    {"content": "记忆2", "type": "preference", "importance": 4.0},
]

for mem in memories:
    manager.add(
        content=mem["content"],
        memory_type=mem["type"],
        importance=mem["importance"]
    )
```

### Q4: 如何备份记忆数据？

```python
import shutil
from pathlib import Path

# 备份数据目录
data_dir = Path("./data")
backup_dir = Path("./data_backup")
shutil.copytree(data_dir, backup_dir)
print("备份完成")
```

---

## 相关文档

- [项目状态](PROJECT_STATUS.md) - 当前进度和计划
- [API参考](API_REFERENCE.md) - 完整API文档
- [测试报告](../M6_INTEGRATION_TEST_REPORT.md) - M6集成测试报告

---

*为安哥打造的零操作记忆系统*  
*有问题随时问安仔 😊*
