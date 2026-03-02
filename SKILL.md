---
name: memory-system-v3
description: 为AI Agent提供本地实时记忆管理能力，实现跨会话的个性化对话体验
version: 3.0.0
author: 安仔 (Anzai)
email: ffdd-120@163.com
homepage: https://gitee.com/ximen120/memory_system_for_agent
license: MIT
tags: [memory, agent, recall, personalize]
---

# 记忆系统3.0 - Agent集成指南

## 快速开始

### 1. 检测安装状态

检查是否已安装记忆系统：
```python
import sys
sys.path.insert(0, r'D:\projects\memory_system_v3')
try:
    from scripts.memory3_core import memorize, recall
    print("✅ 记忆系统已安装")
except ImportError as e:
    print(f"❌ 未安装: {e}")
```

### 2. 安装（如未安装）

**方式A: Git克隆**
```bash
git clone https://gitee.com/ximen120/memory_system_for_agent.git D:\projects\memory_system_v3
```

**方式B: 本仓库目录**
如果当前已是本仓库目录，直接使用：
```python
import sys
sys.path.insert(0, r'<当前目录>')
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

依赖列表：
- numpy
- scikit-learn
- chardet
- networkx

### 4. 启动记忆系统

```python
# 启动记忆服务
python memory_boot.py

# 预期输出：
# ✅ 记忆系统启动成功
# 📚 共 X 条记忆 | 最近 Y 条已加载
```

### 5. 在Agent中集成

```python
import sys
# 根据实际安装路径调整
sys.path.insert(0, r'D:\projects\memory_system_v3')

from scripts.memory3_core import memorize, recall

# 保存记忆
memorize("用户喜欢Python编程", "preference", 4.0)

# 检索记忆
results = recall("编程")
# 返回：[{'content': '用户喜欢Python编程', 'type': 'preference', ...}]
```

## 核心API

### memorize(content, type, priority)

保存一条记忆。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| content | str | 是 | 记忆内容 |
| type | str | 是 | 记忆类型，如fact/preference/task |
| priority | float | 是 | 优先级 1.0-5.0，数值越大越重要 |

**示例:**
```python
memorize("用户名叫安仔", "fact", 5.0)
memorize("用户喜欢Python", "preference", 4.5)
memorize("用户生日是2月28日", "fact", 5.0)
```

### recall(query, top_k=5, type_filter=None)

检索相关记忆。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | str | 是 | 检索关键词 |
| top_k | int | 否 | 返回条数，默认5 |
| type_filter | str | 否 | 按类型过滤 |

**示例:**
```python
# 检索所有相关记忆
results = recall("Python")

# 只检索事实类型
results = recall("生日", type_filter="fact")

# 返回更多条数
results = recall("用户", top_k=10)
```

**返回值:**
```python
[
  {
    "content": "用户喜欢Python编程",
    "type": "preference", 
    "priority": 4.5,
    "created_at": "2026-02-26T10:30:00"
  }
]
```

## 最佳实践

### 1. 自动记忆时机

在以下场景自动调用memorize：
- 用户自我介绍时 → 记录姓名、身份
- 用户表达偏好时 → 记录喜好、厌恶
- 用户设置参数时 → 记录配置
- 对话产生结论时 → 记录核心结论

### 2. 智能检索时机

在以下场景调用recall：
- 对话开始时 → 回忆用户信息，个性化开场
- 用户提问前 → 检索相关背景
- 做推荐时 → 检索用户偏好
- 决策前 → 检索历史经验

### 3. 记忆管理策略

```python
# 高优先级事实（用户基本信息）
memorize("用户名称", "fact", 5.0)

# 中优先级偏好（兴趣爱好）
memorize("用户偏好", "preference", 4.0)

# 普通优先级任务
memorize("当前任务", "task", 3.0)
```

## 常见错误处理

| 错误 | 原因 | 解决方案 |
|------|------|---------|
| ModuleNotFoundError | 路径错误或未安装依赖 | 检查sys.path，安装requirements |
| ImportError | 依赖缺失 | pip install -r requirements.txt |
| 记忆检索为空 | 确实没有相关记忆 | 正常情况，可提示用户这是首次交流 |
| 启动失败 | 数据目录权限问题 | 检查data/目录可写权限 |

## 完整示例

```python
import sys
sys.path.insert(0, r'D:\projects\memory_system_v3')
from scripts.memory3_core import memorize, recall

class AgentWithMemory:
    def __init__(self):
        self.user_id = None
    
    def greet(self, user_input):
        """智能问候，利用记忆"""
        # 检索用户信息
        memories = recall("用户")
        
        if memories:
            # 记住用户，个性化问候
            user_name = self._extract_name(memories)
            return f"欢迎回来，{user_name}！很高兴再次为你服务。"
        else:
            # 新用户
            return "你好！我是安仔，很高兴认识你。请问怎么称呼？"
    
    def _extract_name(self, memories):
        """从记忆中提取用户名"""
        for m in memories:
            if "叫" in m.get('content', ''):
                return m['content'].split("叫")[-1].strip()
        return "朋友"
    
    def learn(self, content, memory_type="fact"):
        """学习新知识"""
        memorize(content, memory_type, 4.0)
        return f"已记住：{content}"
    
    def remember(self, query):
        """回忆相关信息"""
        return recall(query)

# 使用示例
agent = AgentWithMemory()

# 学习
agent.learn("用户喜欢Python编程", "preference")
agent.learn("用户名叫安仔", "fact")

# 回忆
memories = agent.remember("编程")
print(memories)
```

## 隐私说明

- 所有数据存储在本地 `data/` 目录
- 不上传任何数据到远程服务器
- 用户完全拥有数据所有权

## 更新日志

### v3.0.0
- 首次发布
- 支持语义检索
- 支持优先级管理
- 支持多类型记忆

## 获取帮助

- 问题反馈：https://gitee.com/ximen120/memory_system_for_agent/issues
- 作者邮箱：ffdd-120@163.com

---

**记住：有记忆的Agent，才是真正智能的Agent。**
