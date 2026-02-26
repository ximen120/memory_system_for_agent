# 记忆系统3.0 (Memory System v3.0)

一个为AI Agent设计的本地实时记忆管理系统，实现跨会话的个性化对话体验。

## 功能特性

- **实时记忆保存**：自动保存对话中的重要信息
- **智能检索**：基于语义相似度检索历史记忆
- **跨会话持久化**：重启后记忆不丢失
- **隐私保护**：数据本地存储，不上传云端
- **轻量级**：纯Python实现，无复杂依赖

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动记忆系统

```bash
python memory_boot.py
```

### 在Agent中使用

```python
from memory3_core import memorize, recall

# 保存记忆
memorize("用户喜欢Python编程", "preference", 4.0)

# 检索记忆
results = recall("编程")
```

## 项目结构

```
memory_system_v3/
├── scripts/           # 核心代码
│   ├── memory3_core.py
│   └── memory3_utils.py
├── data/              # 记忆数据（自动创建）
├── memory_boot.py     # 启动脚本
├── requirements.txt   # 依赖列表
└── README.md
```

## 隐私说明

- 所有记忆数据存储在本地 `data/` 目录
- 不会上传到任何远程服务器
- 支持.gitignore排除隐私数据

## 开源协议

MIT License - 详见 [LICENSE](LICENSE) 文件

## 作者

安仔 (Anzai) - ffdd-120@163.com
