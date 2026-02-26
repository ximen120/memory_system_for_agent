#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
记忆系统 v3.0 启动脚本 (修复版)

使用方法:
    python start_v3_fixed.py
"""

import sys
import os

# 设置编码
sys.stdout.reconfigure(encoding='utf-8')

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.memory_unit import MemoryUnit
from storage.json_storage import JsonStorage


def main():
    print("=" * 60)
    print("  记忆系统 v3.0 - 启动成功")
    print("=" * 60)
    
    # 创建存储
    data_dir = os.path.join(os.path.dirname(__file__), 'data', 'my_memories')
    storage = JsonStorage(data_dir)
    print("\n[1] 存储已初始化")
    print(f"    数据目录: {data_dir}")
    
    # 添加示例记忆
    print("\n[2] 添加示例记忆...")
    
    m1 = MemoryUnit(
        content="安哥喜欢简洁高效的沟通方式",
        memory_type="preference",
        importance=4.0,
        tags=["沟通", "喜好"]
    )
    id1 = storage.save(m1)
    print(f"    已保存: {m1.content}")
    
    m2 = MemoryUnit(
        content="记忆系统v3.0开发完成",
        memory_type="event",
        importance=5.0,
        tags=["项目", "里程碑"]
    )
    id2 = storage.save(m2)
    print(f"    已保存: {m2.content}")
    
    # 列出所有记忆
    print("\n[3] 所有记忆:")
    memories = storage.query(limit=100)
    for i, m in enumerate(memories, 1):
        print(f"    {i}. [{m.memory_type}] {m.content}")
    
    # 搜索记忆
    print("\n[4] 搜索 '沟通':")
    results = [m for m in memories if "沟通" in m.content]
    if results:
        for m in results:
            print(f"    - {m.content}")
    else:
        print("    未找到相关记忆")
    
    print("\n" + "=" * 60)
    print("  系统运行正常！")
    print("=" * 60)
    print(f"\n数据保存在: {data_dir}")
    print("\n可用功能:")
    print("  - 记忆保存/查询/删除")
    print("  - 关键词搜索")
    print("  - 向量检索")
    print("  - 四层记忆架构")


if __name__ == "__main__":
    main()
