# MemOS ↔ 记忆3.0 集成方案

## 目标

让MemOS Skill在对话开始时**自动启动记忆3.0系统**，实现统一记忆管理。

## 当前状态

| 系统 | 位置 | 启动方式 | 状态 |
|------|------|----------|------|
| MemOS | `~/.xiaoyue_memory/` | ✅ 自动（Skill触发） | 运行中 |
| 记忆3.0 | `D:\wordir\memory_system_v3\` | ❌ 手动 | 待集成 |

## 集成方案B：MemOS调用记忆3.0

### 实现步骤

#### 步骤1：修改MemOS Skill（已完成 ✅）

创建集成桥梁：`memos_bridge.py`

功能：
- `auto_load_memory()` - 自动加载两个系统的记忆
- `sync_from_memory3()` - 同步数据到MemOS
- `get_combined_memories()` - 统一检索接口

#### 步骤2：修改Skill配置

修改 `C:\Users\Simon\.stepfun\skills\persistent-memory\SKILL.md`：

```yaml
triggers:
  - 对话开始时自动加载记忆（auto_load_memory_with_bridge）
```

#### 步骤3：创建统一的auto_load函数

在 `persistent-memory/scripts/auto_memory.py` 中添加：

```python
def auto_load_memory_with_bridge():
    """
    自动加载MemOS + 记忆3.0
    """
    import sys
    sys.path.insert(0, 'D:\\wordir\\memory_system_v3')
    from memos_bridge import auto_load_memory
    
    return auto_load_memory()
```

### 集成后的工作流程

```
新话题开始
  ↓
MemOS Skill自动触发
  ↓
调用 memos_bridge.auto_load_memory()
  ↓
同时加载：
  ├── MemOS档案（~/.xiaoyue_memory/）
  └── 记忆3.0（D:\wordir\memory_system_v3\）
  ↓
返回合并的记忆数据
  ↓
安仔使用统一记忆回答问题
```

## 文件清单

| 文件 | 功能 | 状态 |
|------|------|------|
| `memos_bridge.py` | 集成桥梁 | ✅ 已完成 |
| `SKILL.md` 修改 | 添加触发器 | ⏳ 待修改 |
| `auto_memory.py` 修改 | 统一加载函数 | ⏳ 待修改 |

## 下一步行动

需要修改的文件在：`C:\Users\Simon\.stepfun\skills\persistent-memory/`

1. 备份原Skill
2. 修改 `scripts/auto_memory.py`，添加bridge调用
3. 测试集成效果

## 备选方案A：包装成独立Skill

如果方案B修改困难，可以：

创建新Skill：`memory-system-3`
- `always_active: true`
- 自动启动记忆3.0
- 与MemOS Skill并行运行

## 安哥的选择？

- **方案B**（推荐）：修改现有Skill，需要编辑系统文件
- **方案A**：创建新Skill，更独立但可能有冲突
- **维持现状**：MemOS自动，记忆3.0手动
