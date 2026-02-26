# -*- coding: utf-8 -*-
"""
M6傻瓜层任务3：标签系统测试
测试标签管理与MemoryUnit的集成
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src" / "core"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "ux"))

from memory_unit import MemoryUnit
from tag_manager import TagManager


def test_memory_with_tags():
    """测试带标签的记忆"""
    print("=" * 60)
    print("M6 Task 3: Tag System Integration Test")
    print("=" * 60)
    
    # 创建标签管理器
    tag_manager = TagManager(auto_extract_enabled=True)
    
    # 创建带标签的记忆
    print("\n1. 创建带标签的记忆")
    print("-" * 60)
    
    memories = []
    
    # 记忆1：工作相关
    content1 = "下周三要参加项目评审会议，需要准备PPT和演示文稿"
    tags1 = tag_manager.extract_tags(content1)
    memory1 = MemoryUnit(
        content=content1,
        memory_type="task",
        importance=4.5,
        tags=tags1
    )
    memories.append(memory1)
    print(f"记忆1: {content1}")
    print(f"  自动标签: {tags1}")
    print(f"  记忆ID: {memory1.memory_id}")
    
    # 记忆2：生活喜好
    content2 = "我喜欢喝美式咖啡，不喜欢加糖"
    tags2 = tag_manager.extract_tags(content2)
    memory2 = MemoryUnit(
        content=content2,
        memory_type="preference",
        importance=3.0,
        tags=tags2
    )
    memories.append(memory2)
    print(f"\n记忆2: {content2}")
    print(f"  自动标签: {tags2}")
    print(f"  记忆ID: {memory2.memory_id}")
    
    # 记忆3：学习目标
    content3 = "我的目标是学习Python编程，计划每天练习2小时"
    tags3 = tag_manager.extract_tags(content3)
    memory3 = MemoryUnit(
        content=content3,
        memory_type="goal",
        importance=4.0,
        tags=tags3
    )
    memories.append(memory3)
    print(f"\n记忆3: {content3}")
    print(f"  自动标签: {tags3}")
    print(f"  记忆ID: {memory3.memory_id}")
    
    # 测试2：手动添加标签
    print("\n2. 手动添加标签")
    print("-" * 60)
    
    # 给记忆1添加额外标签
    extra_tags = ["紧急", "工作"]
    for tag in extra_tags:
        if tag not in memory1.tags:
            memory1.tags.append(tag)
    print(f"记忆1添加标签: {extra_tags}")
    print(f"记忆1当前标签: {memory1.tags}")
    
    # 测试3：按标签筛选
    print("\n3. 按标签筛选记忆")
    print("-" * 60)
    
    # 转换为字典列表用于筛选
    memory_dicts = [m.model_dump() for m in memories]
    
    # 筛选"工作"标签
    work_memories = tag_manager.filter_by_tags(memory_dicts, ["工作"])
    print(f"筛选'工作'标签: {len(work_memories)} 条记忆")
    for m in work_memories:
        print(f"  - {m['content'][:30]}...")
    
    # 筛选"目标"标签
    goal_memories = tag_manager.filter_by_tags(memory_dicts, ["目标"])
    print(f"\n筛选'目标'标签: {len(goal_memories)} 条记忆")
    for m in goal_memories:
        print(f"  - {m['content'][:30]}...")
    
    # 筛选多个标签（OR模式）
    multi_memories = tag_manager.filter_by_tags(memory_dicts, ["工作", "喜好"])
    print(f"\n筛选'工作'或'喜好': {len(multi_memories)} 条记忆")
    
    # 测试4：标签统计
    print("\n4. 标签统计")
    print("-" * 60)
    
    tag_infos = tag_manager.get_all_tags(memory_dicts)
    print(f"共有 {len(tag_infos)} 个不同标签:")
    for info in tag_infos[:10]:  # 只显示前10个
        print(f"  {info.name}: {info.count} 次")
    
    # 测试5：标签推荐
    print("\n5. 标签推荐")
    print("-" * 60)
    
    new_content = "明天要去健身房锻炼，计划跑步5公里"
    suggested_tags = tag_manager.suggest_tags(new_content, top_k=3)
    print(f"内容: {new_content}")
    print(f"推荐标签: {suggested_tags}")
    
    # 测试6：ChromaDB格式转换
    print("\n6. ChromaDB格式转换")
    print("-" * 60)
    
    chroma_doc = memory1.to_chroma_document()
    print(f"记忆1的ChromaDB格式:")
    print(f"  ID: {chroma_doc['id']}")
    print(f"  内容: {chroma_doc['document'][:30]}...")
    print(f"  标签: {chroma_doc['metadata']['tags']}")
    print(f"  类型: {chroma_doc['metadata']['memory_type']}")
    
    # 最终报告
    print("\n" + "=" * 60)
    print("测试报告")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 6
    
    if len(memories) == 3:
        print("[OK] 创建带标签的记忆")
        tests_passed += 1
    else:
        print("[FAIL] 创建带标签的记忆")
    
    if len(memory1.tags) > len(tags1):
        print("[OK] 手动添加标签")
        tests_passed += 1
    else:
        print("[FAIL] 手动添加标签")
    
    if len(work_memories) > 0:
        print("[OK] 按标签筛选")
        tests_passed += 1
    else:
        print("[FAIL] 按标签筛选")
    
    if len(tag_infos) > 0:
        print("[OK] 标签统计")
        tests_passed += 1
    else:
        print("[FAIL] 标签统计")
    
    if len(suggested_tags) > 0:
        print("[OK] 标签推荐")
        tests_passed += 1
    else:
        print("[FAIL] 标签推荐")
    
    if "tags" in chroma_doc["metadata"]:
        print("[OK] ChromaDB格式转换")
        tests_passed += 1
    else:
        print("[FAIL] ChromaDB格式转换")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {tests_passed}/{tests_total} 通过")
    print("=" * 60)
    
    return tests_passed == tests_total


if __name__ == "__main__":
    success = test_memory_with_tags()
    sys.exit(0 if success else 1)
