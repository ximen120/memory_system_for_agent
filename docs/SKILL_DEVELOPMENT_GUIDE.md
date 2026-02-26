# 记忆3.0 Agent Skill 开发指南

## 什么是Agent Skill

Agent Skill 是AI助手的扩展技能，通过特定的格式定义，让AI助手能够：
- 自动识别用户意图
- 执行预定义的工作流程
- 提供标准化的服务

## Skill文件格式

Skill文件使用Markdown格式，包含YAML frontmatter和Markdown内容：

```markdown
---
name: skill-name
description: 技能描述
always_active: true/false
---

# 技能标题

## 系统指令

...
```

## 记忆3.0 Skill封装

### 文件位置

```
C:\Users\{用户名}\.stepfun\skills\memory-system-3\SKILL.md
```

### 封装步骤

#### 1. 创建skill目录

```bash
mkdir -p C:\Users\Simon\.stepfun\skills\memory-system-3
```

#### 2. 编写SKILL.md文件

包含以下部分：
- **YAML Frontmatter**: name, description, always_active
- **系统指令**: 强制自动运行说明
- **核心功能**: 自动保存、自动检索、指令系统
- **工作流程**: 详细的执行步骤
- **配置信息**: 路径、环境等
- **禁止事项**: 明确不能做的事
- **示例**: 使用示例

#### 3. 关键配置

```yaml
name: memory-system-3
description: 记忆系统3.0 - 本地实时记忆管理
always_active: true
```

#### 4. 核心指令定义

| 指令 | 触发条件 | 执行操作 |
|------|----------|----------|
| 记忆3.0 | 用户输入包含"记忆3.0" | 启动记忆系统 |
| 记住 | 用户说"记住..." | 显式保存信息 |
| 回忆 | 用户说"回忆..." | 检索记忆 |
| 加载记忆 | 用户说"加载记忆" | 完整加载并报告 |

### 完整Skill文件示例

见 `C:\Users\Simon\.stepfun\skills\memory-system-3\SKILL.md`

## Skill工作原理

### 自动触发机制

```
用户输入
  ↓
AI助手检查所有active skills
  ↓
匹配触发条件
  ↓
执行skill定义的工作流程
  ↓
返回结果
```

### 记忆3.0的触发逻辑

1. **检测**: 用户输入是否包含"记忆3.0"
2. **启动**: 执行 `python memory_boot.py --check`
3. **加载**: 读取 `data/auto_memory/` 下的记忆文件
4. **响应**: 返回加载的记忆数量

## 开发注意事项

### 1. 路径使用绝对路径

```python
# 正确
D:\wordir\memory_system_v3\memory_boot.py

# 错误
.\memory_boot.py
```

### 2. 环境激活

```bash
# 使用完整路径调用conda环境
C:\Users\Simon\.conda\envs\memory_v3\python.exe script.py
```

### 3. 错误处理

```python
try:
    result = execute_command(...)
    if result.success:
        return "成功信息"
    else:
        return "错误: " + result.error
except Exception as e:
    return "异常: " + str(e)
```

### 4. 隐私保护

- 不要返回记忆文件的完整路径
- 不要显示敏感配置信息
- 记忆数据不上传到云端

## Skill测试

### 测试步骤

1. **放置skill文件**到正确位置
2. **重启AI助手**或刷新skills
3. **测试触发词**: "记忆3.0"
4. **验证响应**: 是否正确加载记忆

### 测试用例

| 输入 | 预期响应 |
|------|----------|
| 记忆3.0 | 🧠 记忆3.0运行中，已加载X条记忆 |
| 记住我喜欢咖啡 | （静默保存，无提示） |
| 我喜欢什么？ | 你喜欢咖啡 |

## 故障排除

### Skill未触发

1. 检查skill文件位置是否正确
2. 检查YAML frontmatter格式
3. 检查always_active是否为true
4. 重启AI助手

### 记忆加载失败

1. 检查 `memory_boot.py` 是否存在
2. 检查conda环境是否正常
3. 检查 `data/auto_memory/` 目录权限
4. 查看错误日志

## 进阶开发

### 添加新指令

在SKILL.md中添加新的指令定义：

```markdown
### 新指令

**触发**: 用户输入包含"关键词"

**执行**:
1. 步骤1
2. 步骤2

**返回**: 结果格式
```

### 集成其他工具

可以结合使用：
- `desktop_terminal_execute`: 执行命令
- `Read`: 读取记忆文件
- `Write`: 写入新记忆
- `Glob`: 搜索记忆文件

## 参考资源

- 当前skill: `C:\Users\Simon\.stepfun\skills\memory-system-3\SKILL.md`
- 项目文档: `D:\wordir\memory_system_v3\README.md`
- 集成方案: `D:\wordir\memory_system_v3\INTEGRATION_PLAN.md`
