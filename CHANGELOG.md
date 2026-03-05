# 更新日志

## [1.1.0] - 2026-03-04

### 新增（T1 + T2）

#### T1: 自动加载上下文
- **CoreMemoryManager**: 新增核心记忆管理器，管理高优先级记忆
  - `get_recent_memories()`: 获取最近的核心记忆
  - `format_markdown()`: 格式化为Markdown输出
  - `format_json()`: 格式化为JSON输出
- **MemorySystem.auto_load_context()**: 对话启动时自动加载最近5条核心记忆
- **MemorySystem.reset_auto_load_flag()`: 重置自动加载标记（用于测试）
- 新增测试文件: `tests/test_auto_load.py`

#### T2: 对话可靠保存
- **ConversationSaver**: 对话可靠保存核心类
  - 三重保障机制：实时触发、定时保存（10分钟）、结束信号检测
  - `on_message()`: 处理每条消息的核心入口
  - `force_save()`: 手动强制保存
  - `get_session_summary()`: 获取会话摘要
- **SaveResult**: 保存结果数据类
- **MemorySystem.on_message()`: 对话消息统一入口
- **MemorySystem.end_conversation()`: 结束对话并保存
- **END_SIGNAL_KEYWORDS**: 结束信号关键词列表（"保存"、"结束"、"下次见"等）
- 新增测试文件: `tests/test_conversation_saver.py`

### 改进
- 优化导入路径兼容性，支持多种导入方式
- 完善异常处理，确保保存失败不影响对话继续
- 新增设计文档目录: `docs/design/`

### 影响范围
- 新增文件：
  - `src/core/core_memory_manager.py`
  - `src/ux/conversation_saver.py`
  - `tests/test_auto_load.py`
  - `tests/test_conversation_saver.py`
  - `docs/design/`
- 修改文件：
  - `src/memory_system.py`（新增T1/T2方法）
  - `src/core/memory_manager.py`
  - `src/api/memory_api.py`
  - `src/api/unified_api.py`

### 验收
- T1: 自动加载上下文功能测试通过
- T2: 5个单元测试全部通过（基本功能、定时功能、结束信号、记忆提取、集成测试）

## [1.0.2] - 2026-03-04

### 修复（关键Bug）
- **Embedding未持久化**：`memory_api.py` 的 `add_memory` 方法中，embedding 生成在 JSON 保存之后，导致所有记忆的 embedding 字段写入 JSON 时为 None。重启后向量检索全部失效。
  - 修复：先生成 embedding，再连同 embedding 一起构造 MemoryUnit 并保存到 JSON。
- **旧记忆缺失Embedding自动修复**：`_load_existing_memories` 方法增加修复逻辑，对已有的 434 条 embedding 为 None 的旧记忆，启动时自动重新生成并回写 JSON 文件。
- **KeywordAPI 重启后索引丢失**：KeywordAPI 是纯内存索引，重启后所有关键词文档清空，导致 keyword 和 hybrid 搜索均返回空。
  - 修复：`unified_api.py` 新增 `_sync_keyword_index()` 方法，初始化时将 MemoryAPI 中已加载的记忆同步到 KeywordAPI。
- **SKILL.md 中搜索结果引用了不存在的字段**：启动检索命令模板中引用了 `r.importance`，但 `UnifiedSearchResult` 没有该字段，导致启动时报 AttributeError。
  - 修复：将模板中的 `importance` 替换为 `memory_type`。

### 影响范围
- 涉及文件：`src/api/memory_api.py`、`src/api/unified_api.py`、`SKILL.md`
- 两处部署目录已同步修改：`C:\Users\Simon\.stepfun\skills\memory-system-3\` 和 `D:\projects\memory_system_v3\`

### 复盘
- **根因**：前期开发验证不够充分，`add_memory` 中 embedding 生成与持久化的时序未经端到端测试；KeywordAPI 的纯内存特性在重启场景下未覆盖测试。
- **教训**：核心存储链路（写入→持久化→重启加载→检索）需要完整的端到端集成测试，不能只验证单次会话内的功能。

## [1.0.1] - 2026-02-25

### 新增
- Agent Skill封装，支持AI助手自动识别记忆指令
- `memory-system-3` Skill - 记忆系统主技能
- `memos-integration` Skill - 全局记忆集成技能
- Skill开发指南文档
- 一键安装脚本 `install_skills.bat`

### 改进
- 完善项目文档，添加Skills使用说明
- 优化README结构

## [1.0.0] - 2026-02-25

### 发布
- 记忆系统v3.0首次发布
- M6傻瓜层完整功能
- Gitee自动同步配置
- Windows凭证管理器集成

### 核心功能
- 全自动启动
- 自然语言交互
- 四层记忆架构
- 本地数据存储
