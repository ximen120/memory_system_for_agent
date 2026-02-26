#!/usr/bin/env python3
"""
记忆3.0自动同步脚本
自动检测变更并推送到Gitee
"""

import subprocess
import os
import sys
import time
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent.absolute()
LOG_FILE = PROJECT_DIR / "sync.log"

def log(msg):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

def run_git(cmd):
    """执行Git命令"""
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )
    return result.returncode == 0, result.stdout, result.stderr

def sync():
    """执行同步"""
    log("=" * 60)
    log("开始同步...")
    
    # 1. 检查是否有变更
    success, stdout, stderr = run_git("git status --porcelain")
    if not success:
        log(f"检查状态失败: {stderr}")
        return False
    
    if not stdout.strip():
        log("没有需要同步的变更")
        return True
    
    # 2. 添加所有变更
    log("添加变更...")
    success, _, stderr = run_git("git add .")
    if not success:
        log(f"添加失败: {stderr}")
        return False
    
    # 3. 提交
    log("提交变更...")
    commit_msg = f"自动同步 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    success, _, stderr = run_git(f'git commit -m "{commit_msg}"')
    if not success:
        log(f"提交失败: {stderr}")
        return False
    
    # 4. 推送（使用凭证管理器，无需在脚本中存储密码）
    log("推送到Gitee...")
    success, _, stderr = run_git("git push origin master")
    if not success:
        if "Authentication failed" in stderr or "403" in stderr:
            log("认证失败，请运行 setup_secure_git.bat 配置凭证")
        log(f"推送失败: {stderr}")
        return False
    
    log("✓ 同步成功!")
    return True

def watch_and_sync(interval=300):
    """持续监控并同步"""
    log("=" * 60)
    log(f"启动自动同步监控 (每{interval}秒检查一次)")
    log("按 Ctrl+C 停止")
    log("=" * 60)
    
    try:
        while True:
            sync()
            time.sleep(interval)
    except KeyboardInterrupt:
        log("\n监控已停止")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="记忆3.0自动同步工具")
    parser.add_argument("--watch", "-w", action="store_true", help="持续监控模式")
    parser.add_argument("--interval", "-i", type=int, default=300, help="检查间隔(秒)")
    args = parser.parse_args()
    
    if args.watch:
        watch_and_sync(args.interval)
    else:
        sync()
