#!/usr/bin/env python
"""测试修复后的记忆系统"""

import sys
import os

# 切换到正确目录
os.chdir(r'D:\wordir\memory_system_v3')
sys.path.insert(0, r'D:\wordir\memory_system_v3')
sys.path.insert(0, r'D:\wordir\memory_system_v3\src')

from auto_memory_bridge import get_bridge, recent, recall

print("🧠 测试记忆系统修复...")
print()

# 获取桥梁
bridge = get_bridge()

# 测试1: 获取最近记忆
print("【测试1】获取最近记忆:")
memories = recent(10)
print(f"  找到 {len(memories)} 条记忆:")
for m in memories:
    print(f"    - {m['content']}")

print()

# 测试2: 检索特定记忆
print("【测试2】检索'天天':")
results = recall("天天", top_k=3)
print(f"  找到 {len(results)} 条相关记忆:")
for r in results:
    print(f"    - {r['content']} (类型: {r['type']})")

print()

# 测试3: 检索生日
print("【测试3】检索'生日':")
results = recall("生日", top_k=3)
print(f"  找到 {len(results)} 条相关记忆:")
for r in results:
    print(f"    - {r['content']} (类型: {r['type']})")

print()
print("✅ 测试完成!")
