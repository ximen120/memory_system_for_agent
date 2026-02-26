# 记忆3.0 Gitee上传指南

## 快速上传

### 方式一：使用上传脚本（推荐）

```bash
# 进入项目目录
cd D:\wordir\memory_system_v3

# 运行上传脚本
python upload_to_gitee.py
```

脚本会自动：
1. 初始化Git仓库（如需要）
2. 检查.gitignore配置
3. 添加所有文件
4. 提交更改
5. 推送到Gitee

### 方式二：手动上传

```bash
# 1. 进入项目目录
cd D:\wordir\memory_system_v3

# 2. 初始化Git（如未初始化）
git init

# 3. 添加所有文件
git add .

# 4. 提交
git commit -m "初始提交记忆3.0项目"

# 5. 添加远程仓库（替换为你的Gitee地址）
git remote add origin https://gitee.com/你的用户名/memory-system-v3.git

# 6. 推送
git push -u origin master
```

## 隐私保护说明

### 已配置不上传的文件

`.gitignore` 已配置排除以下文件：

```
# 记忆数据 - 用户隐私，不上传
data/auto_memory/      # 自动保存的记忆
data/my_memories/      # 个人记忆
data/demo/             # 演示数据

# 敏感配置
.env                   # 环境变量
.env.local

# 缓存和临时文件
__pycache__/
*.pyc
.pytest_cache/
```

### 验证隐私保护

```bash
# 查看哪些文件会被上传
git ls-files

# 查看哪些文件被忽略（不应上传）
git check-ignore -v data/auto_memory/*
```

## 持续同步

### 每次修改后上传

```bash
# 快速上传（使用脚本）
python upload_to_gitee.py

# 或手动
git add .
git commit -m "描述你的修改"
git push origin master
```

### 设置快捷命令

在 `.bashrc` 或 `.zshrc` 中添加：

```bash
alias push-memory='cd /d D:\wordir\memory_system_v3 && python upload_to_gitee.py'
```

然后只需运行：
```bash
push-memory
```

## 常见问题

### Q: 如何确认记忆数据没有上传？

A: 在Gitee网页端查看仓库，确认 `data/auto_memory/` 目录不存在。

### Q: 不小心上传了记忆数据怎么办？

A: 
```bash
# 1. 从Git历史中删除
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch data/auto_memory/*' \
  --prune-empty --tag-name-filter cat -- --all

# 2. 强制推送
git push origin --force --all
```

### Q: 如何在其他电脑上下载项目？

A:
```bash
git clone https://gitee.com/你的用户名/memory-system-v3.git
```

注意：下载后需要重新创建 `data/` 目录和 `.env` 文件。

## Gitee仓库设置建议

1. **设置为私有仓库**（保护代码隐私）
2. **启用Issue功能**（方便记录问题和需求）
3. **添加README**（已包含项目说明）
4. **添加开源许可证**（如MIT）

## 需要帮助？

- Gitee文档: https://gitee.com/help
- Git教程: https://git-scm.com/doc
