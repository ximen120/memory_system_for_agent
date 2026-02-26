#!/usr/bin/env python
"""
加载记忆 - 主入口脚本（终极版）

指令: "加载记忆"
功能: 
    1. 自动寻找虚拟环境
    2. 自动启动记忆系统
    3. 自动加载历史记忆
    4. 返回完整执行结果

使用方法:
    python D:\wordir\memory_system_v3\LOAD_MEMORY.py
    
安仔执行后会返回:
    - 虚拟环境路径
    - 启动状态
    - 历史记忆数量
    - 关键记忆摘要
"""

import sys
import os
import subprocess
import json

# 配置
VENV_PYTHON = r"C:\Users\Simon\.conda\envs\memory_v3\python.exe"
PROJECT_DIR = r"D:\wordir\memory_system_v3"
MEMORY_SCRIPT = os.path.join(PROJECT_DIR, "memory_boot.py")


def find_venv():
    """寻找虚拟环境"""
    venv_paths = [
        r"C:\Users\Simon\.conda\envs\memory_v3\python.exe",
        r"D:\wordir\memory_system_v3\memory_v3\Scripts\python.exe",
        r"C:\Users\Simon\anaconda3\envs\memory_v3\python.exe",
    ]
    
    for path in venv_paths:
        if os.path.exists(path):
            return path
    
    # 尝试系统默认python
    return sys.executable


def boot_memory_system():
    """启动记忆系统"""
    python_exe = find_venv()
    
    result = {
        "venv_found": python_exe,
        "venv_exists": os.path.exists(python_exe),
        "boot_success": False,
        "history_count": 0,
        "key_memories": [],
        "errors": []
    }
    
    if not result["venv_exists"]:
        result["errors"].append(f"虚拟环境不存在: {python_exe}")
        return result
    
    try:
        # 执行启动脚本
        cmd = [python_exe, MEMORY_SCRIPT]
        process = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        result["stdout"] = process.stdout
        result["stderr"] = process.stderr
        result["returncode"] = process.returncode
        
        # 解析启动结果
        if process.returncode == 0 and "启动成功" in process.stdout:
            result["boot_success"] = True
            
            # 提取历史记忆数量
            for line in process.stdout.split('\n'):
                if '已加载' in line and '条' in line:
                    try:
                        count = int(line.split('已加载')[1].split('条')[0].strip())
                        result["history_count"] = count
                    except:
                        pass
        else:
            result["errors"].append("启动脚本执行失败")
            
    except subprocess.TimeoutExpired:
        result["errors"].append("启动超时（30秒）")
    except Exception as e:
        result["errors"].append(f"执行异常: {str(e)}")
    
    return result


def get_key_memories():
    """获取关键记忆"""
    try:
        python_exe = find_venv()
        cmd = [
            python_exe, "-c",
            "import sys; sys.path.insert(0, 'src'); from auto_memory_bridge import recall; " +
            "results = recall('安哥', top_k=5); " +
            "print('---KEY_MEMORIES_START---'); " +
            "[print(r.get('content', '')) for r in results]; " +
            "print('---KEY_MEMORIES_END---')"
        ]
        
        process = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # 解析关键记忆
        memories = []
        in_section = False
        for line in process.stdout.split('\n'):
            if '---KEY_MEMORIES_START---' in line:
                in_section = True
                continue
            if '---KEY_MEMORIES_END---' in line:
                break
            if in_section and line.strip():
                memories.append(line.strip())
        
        return memories[:3]  # 最多3条
        
    except Exception as e:
        return [f"获取关键记忆失败: {str(e)}"]


def generate_report(result):
    """生成执行报告"""
    report = []
    report.append("=" * 60)
    report.append("🧠 加载记忆 - 执行报告")
    report.append("=" * 60)
    report.append("")
    
    # 1. 虚拟环境信息
    report.append("📍 虚拟环境")
    report.append(f"   路径: {result['venv_found']}")
    report.append(f"   状态: {'✅ 存在' if result['venv_exists'] else '❌ 不存在'}")
    report.append("")
    
    # 2. 启动状态
    report.append("🚀 记忆系统启动")
    if result['boot_success']:
        report.append("   状态: ✅ 启动成功")
        report.append(f"   历史记忆: {result['history_count']} 条")
    else:
        report.append("   状态: ❌ 启动失败")
        if result.get('errors'):
            for error in result['errors']:
                report.append(f"   错误: {error}")
    report.append("")
    
    # 3. 关键记忆
    if result.get('key_memories'):
        report.append("🔑 关键记忆")
        for i, mem in enumerate(result['key_memories'], 1):
            report.append(f"   {i}. {mem[:50]}...")
        report.append("")
    
    # 4. 执行输出（可选）
    if result.get('stdout'):
        report.append("📝 执行输出")
        for line in result['stdout'].strip().split('\n')[:5]:
            report.append(f"   {line}")
        report.append("")
    
    report.append("=" * 60)
    
    return "\n".join(report)


def main():
    """主函数 - 加载记忆指令入口"""
    # 1. 启动记忆系统
    result = boot_memory_system()
    
    # 2. 获取关键记忆
    if result['boot_success']:
        result['key_memories'] = get_key_memories()
    
    # 3. 生成并打印报告
    report = generate_report(result)
    print(report)
    
    # 4. 返回JSON格式结果（供程序调用）
    result_json = json.dumps(result, ensure_ascii=False, indent=2)
    
    # 保存结果到文件（方便查看）
    result_file = os.path.join(PROJECT_DIR, "last_load_result.json")
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(result_json)
    
    return 0 if result['boot_success'] else 1


if __name__ == "__main__":
    sys.exit(main())
