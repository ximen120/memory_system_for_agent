# 记忆3.0 发行版 v1.0.1

**发布日期**: 2026-02-25

**版本号**: 1.0.1

**下载地址**: https://gitee.com/ximen120/memory_system_for_agent/releases

---

## 发行说明

### 新增功能

#### 1. Agent Skill封装
记忆3.0现已封装为标准Agent Skills，AI助手可自动识别和执行记忆任务。

**包含Skills**:
- `memory-system-3` - 记忆系统主技能
- `memos-integration` - 全局记忆集成技能

#### 2. 一键安装
提供 `install_skills.bat` 脚本，双击即可安装Skills到系统目录。

#### 3. 开发文档
新增完整的Skill开发指南，方便开发者扩展功能。

---

## 文件清单

```
memory_system_v3/
├── src/                      # 核心源代码
│   ├── core/                # 核心模型
│   ├── storage/             # 存储层
│   ├── retrieval/           # 检索层
│   └── ux/                  # 傻瓜层
├── skills/                   # Agent Skills
│   ├── memory-system-3/
│   │   └── SKILL.md
│   ├── memos-integration/
│   │   └── SKILL.md
│   └── README.md
├── docs/                     # 文档
│   ├── M6_USER_GUIDE.md
│   ├── API_REFERENCE.md
│   ├── PROJECT_STATUS.md
│   └── SKILL_DEVELOPMENT_GUIDE.md
├── tests/                    # 测试
├── data/                     # 数据目录（空）
├── README.md                 # 项目说明
├── CHANGELOG.md              # 更新日志
├── LICENSE                   # MIT许可证
├── requirements.txt          # 依赖
├── install_skills.bat        # Skill安装脚本
├── auto_sync.py             # 自动同步脚本
├── sync_now.bat             # 手动同步脚本
└── setup_secure_git.bat     # Git安全配置
```

---

## 快速开始

### 1. 下载项目

```bash
git clone https://gitee.com/ximen120/memory_system_for_agent.git
cd memory_system_for_agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 安装Agent Skills（可选）

双击运行 `install_skills.bat`，或手动复制 `skills/` 到 `C:\Users\{用户名}\.stepfun\skills\`

### 4. 开始使用

```python
from src.ux.memory_layers import create_memory_layers

# 创建记忆管理器
manager = create_memory_layers(data_dir="./data")

# 添加记忆
manager.add(
    content="我喜欢喝咖啡",
    memory_type="preference",
    importance=4.0,
    tags=["咖啡", "喜好"]
)

# 搜索记忆
results = manager.search_by_keywords(["咖啡"])
```

---

## 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.11+
- **依赖**: 见 `requirements.txt`

---

## 贡献者

- **安哥** - 项目发起人、需求定义
- **安仔** - 核心开发、Skill封装

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 联系方式

- **项目主页**: https://gitee.com/ximen120/memory_system_for_agent
- **Issue反馈**: https://gitee.com/ximen120/memory_system_for_agent/issues

---

## 更新日志

详见 [CHANGELOG.md](CHANGELOG.md)

## 未来计划

- [ ] M2向量检索层
- [ ] 多用户支持
- [ ] Web管理界面
- [ ] 跨平台支持 (Linux/macOS)

---

**感谢使用记忆3.0！**
