#!/usr/bin/env python3
"""
记忆3.0 Gitee上传脚本
自动处理Git初始化、配置.gitignore、提交和推送到Gitee
"""

import subprocess
import os
import sys
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """运行命令并返回结果"""
    print(f"执行: {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    if check and result.returncode != 0:
        print(f"错误: {result.stderr}")
        return False, result.stderr
    print(f"成功: {result.stdout}")
    return True, result.stdout

def main():
    project_dir = Path(__file__).parent.absolute()
    os.chdir(project_dir)
    
    print("=" * 60)
    print("记忆3.0 Gitee上传工具")
    print("=" * 60)
    
    # 1. 检查Git是否安装
    success, _ = run_command("git --version", check=False)
    if not success:
        print("错误: Git未安装，请先安装Git")
        sys.exit(1)
    
    # 2. 初始化Git仓库（如果不存在）
    git_dir = project_dir / ".git"
    if not git_dir.exists():
        print("\n[1/6] 初始化Git仓库...")
        run_command("git init")
    else:
        print("\n[1/6] Git仓库已存在")
    
    # 3. 配置.gitignore（确保记忆数据不上传）
    print("\n[2/6] 检查.gitignore配置...")
    gitignore_path = project_dir / ".gitignore"
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding='utf-8')
        if 'data/auto_memory/' in content:
            print("✓ .gitignore已正确配置，记忆数据将被排除")
        else:
            print("⚠ 警告: .gitignore可能未正确配置记忆数据排除")
    else:
        print("⚠ 警告: 未找到.gitignore文件")
    
    # 4. 添加文件到Git
    print("\n[3/6] 添加文件到Git...")
    run_command("git add .")
    
    # 5. 提交更改
    print("\n[4/6] 提交更改...")
    commit_msg = input("请输入提交信息 (默认: '更新记忆3.0项目'): ").strip()
    if not commit_msg:
        commit_msg = "更新记忆3.0项目"
    
    success, output = run_command(f'git commit -m "{commit_msg}"', check=False)
    if not success and "nothing to commit" in output.lower():
        print("没有需要提交的更改")
    elif not success:
        print(f"提交失败: {output}")
        sys.exit(1)
    else:
        print("✓ 提交成功")
    
    # 6. 检查远程仓库
    print("\n[5/6] 检查远程仓库配置...")
    success, output = run_command("git remote -v", check=False)
    
    if "gitee" not in output.lower():
        print("\n未配置Gitee远程仓库")
        remote_url = input("请输入Gitee仓库地址 (例如: https://gitee.com/username/memory-system-v3.git): ").strip()
        if remote_url:
            run_command(f"git remote add origin {remote_url}")
            print("✓ 远程仓库已添加")
        else:
            print("未提供仓库地址，跳过推送")
            sys.exit(0)
    else:
        print("✓ 远程仓库已配置")
    
    # 7. 推送到Gitee
    print("\n[6/6] 推送到Gitee...")
    success, output = run_command("git push origin master", check=False)
    
    if not success:
        # 尝试main分支
        success, output = run_command("git push origin main", check=False)
    
    if success:
        print("\n" + "=" * 60)
        print("✓ 上传成功！记忆3.0项目已推送到Gitee")
        print("=" * 60)
    else:
        print(f"\n推送失败，可能需要先拉取更新:")
        print(f"  git pull origin master --rebase")
        print(f"或者检查网络连接和仓库权限")
        sys.exit(1)

if __name__ == "__main__":
    main()
