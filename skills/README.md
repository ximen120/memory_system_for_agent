# Agent Skills 目录

本目录包含记忆3.0系统的Agent Skill封装，用于AI助手自动识别和执行记忆相关任务。

## Skill列表

### 1. memory-system-3

**文件**: `memory-system-3/SKILL.md`

**功能**: 记忆系统3.0主技能

**触发方式**:
- 用户输入"记忆3.0"
- 自动检测记忆相关指令

**核心能力**:
- 启动记忆系统
- 加载历史记忆
- 返回系统状态

**配置**:
```yaml
name: memory-system-3
always_active: true
```

### 2. memos-integration

**文件**: `memos-integration/SKILL.md`

**功能**: 全局记忆管理技能

**触发方式**:
- 所有对话自动启用
- 自动保存和检索

**核心能力**:
- 自动保存重要信息
- 自动检索相关记忆
- 跨会话记忆融合

**配置**:
```yaml
name: memos-integration
always_active: true
```

## Skill安装方法

### 方法1：复制到系统目录

```bash
# 复制到AI助手的skills目录
xcopy /E /I skills\* C:\Users\%USERNAME%\.stepfun\skills\
```

### 方法2：创建符号链接

```bash
# 创建符号链接，保持同步
mklink /D C:\Users\Simon\.stepfun\skills\memory-system-3 D:\wordir\memory_system_v3\skills\memory-system-3
mklink /D C:\Users\Simon\.stepfun\skills\memos-integration D:\wordir\memory_system_v3\skills\memos-integration
```

### 方法3：手动安装

1. 打开 `C:\Users\{用户名}\.stepfun\skills\`
2. 创建 `memory-system-3` 目录
3. 复制 `SKILL.md` 到该目录
4. 重启AI助手

## Skill开发指南

详见: `../docs/SKILL_DEVELOPMENT_GUIDE.md`

### 开发新Skill的步骤

1. **创建目录**: `skills/{skill-name}/`
2. **编写SKILL.md**: 包含YAML frontmatter和指令
3. **测试**: 放置到系统目录并测试
4. **文档**: 更新本README

### Skill文件格式

```markdown
---
name: skill-name
description: 技能描述
always_active: true/false
---

# 技能标题

## 系统指令

...

## 工作流程

...

## 示例

...
```

## 注意事项

- Skill文件名必须是 `SKILL.md`
- YAML frontmatter 必须放在文件开头
- `always_active: true` 表示自动启用
- 使用绝对路径，避免相对路径
- 考虑错误处理和边界情况

## 更新日志

### 2026-02-25
- 创建 `memory-system-3` skill
- 创建 `memos-integration` skill
- 添加开发指南

## 相关文档

- [开发指南](../docs/SKILL_DEVELOPMENT_GUIDE.md)
- [项目README](../README.md)
- [集成方案](../INTEGRATION_PLAN.md)
