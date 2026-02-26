#!/usr/bin/env python
"""
暗号指令: 记忆3.0

功能: 一键启动记忆系统，无需关心路径和环境
"""

import sys
import os
import subprocess

# 固定配置 - 不依赖当前路径
VENV_PYTHON = r"C:\Users\Simon\.conda\envs\memory_v3\python.exe"
PROJECT_DIR = r"D:\wordir\memory_system_v3"
BOOT_SCRIPT = os.path.join(PROJECT_DIR, "memory_boot.py")

def main():
    print("🧠 记忆3.0 启动中...")
    print()
    
    # 检查环境
    if not os.path.exists(VENV_PYTHON):
        print(f"❌ 虚拟环境不存在: {VENV_PYTHON}")
        return 1
    
    if not os.path.exists(BOOT_SCRIPT):
        print(f"❌ 启动脚本不存在: {BOOT_SCRIPT}")
        return 1
    
    # 启动记忆系统
    try:
        result = subprocess.run(
            [VENV_PYTHON, BOOT_SCRIPT],
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print()
            print("✅ 记忆3.0 启动成功！")
            return 0
        else:
            print("❌ 启动失败")
            if result.stderr:
                print(result.stderr)
            return 1
            
    except Exception as e:
        print(f"❌ 执行异常: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
