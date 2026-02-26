# -*- coding: utf-8 -*-
"""
M6傻瓜层任务3：标签系统测试（简化版）
不依赖pydantic，直接测试TagManager功能
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src" / "ux"))

from tag_manager import TagManager, TagInfo


def test_tag_system():
    """测试标签系统"""
    print("=" * 60)
    print("M6 Task 3: Tag System Test")
    print("=" * 60)
    
    # 创建标签管理器
    tag_manager = TagManager(auto_extract_enabled=True)
    
    # 模拟记忆数据
    memories = [
        {
            "id": "mem_001",
            "content": "下周三要参加项目评审会议，需要准备PPT和演示文稿",
            "type": "task",
            "tags": []
        },
        {
            "id": "mem_002",
            "content": "我喜欢喝美式咖啡，不喜欢加糖",
            "type": "preference",
            "tags": []
        },
        {
            "id": "mem_003",
            "content": "我的目标是学习Python编程，计划每天练习2小时",
            "type": "goal",
            "tags": []
        },
        {
            "id": "mem_004",
            "content": "今天和朋友去公园散步，天气很好",
            "type": "event",
            "tags": []
        },
    ]
    
    # 测试1: 自动提取标签
    print("\n1. 自动提取标签")
    print("-" * 60)
    
    for memory in memories:
        tags = tag_manager.extract_tags(memory["content"])
        memory["tags"] = tags
        print(f"\n记忆: {memory['content'][:40]}...")
        print(f"  自动标签: {tags}")
    
    # 测试2: 手动添加标签
    print("\n2. 手动添加标签")
    print("-" * 60)
    
    # 给第一条记忆添加额外标签
    memories_dict = {m["id"]: m for m in memories}
    tag_manager.add_tag("mem_001", "紧急", memories_dict)
    tag_manager.add_tag("mem_001", "重要", memories_dict)
    
    print(f"mem_001 添加标签: 紧急, 重要")
    print(f"mem_001 当前标签: {memories_dict['mem_001']['tags']}")
    
    # 测试3: 按标签筛选
    print("\n3. 按标签筛选记忆")
    print("-" * 60)
    
    # 筛选"工作"相关
    work_results = tag_manager.filter_by_tags(memories, ["工作"])
    print(f"筛选'工作': {len(work_results)} 条")
    for m in work_results:
        print(f"  - {m['content'][:35]}...")
    
    # 筛选"喜好"
    pref_results = tag_manager.filter_by_tags(memories, ["喜好"])
    print(f"\n筛选'喜好': {len(pref_results)} 条")
    for m in pref_results:
        print(f"  - {m['content'][:35]}...")
    
    # 筛选"目标"
    goal_results = tag_manager.filter_by_tags(memories, ["目标"])
    print(f"\n筛选'目标': {len(goal_results)} 条")
    for m in goal_results:
        print(f"  - {m['content'][:35]}...")
    
    # 多标签筛选（OR模式）
    multi_results = tag_manager.filter_by_tags(memories, ["工作", "目标"])
    print(f"\n筛选'工作'或'目标': {len(multi_results)} 条")
    
    # 多标签筛选（AND模式）
    and_results = tag_manager.filter_by_tags(memories, ["紧急", "重要"], match_all=True)
    print(f"筛选'紧急'且'重要': {len(and_results)} 条")
    
    # 测试4: 标签统计
    print("\n4. 标签统计")
    print("-" * 60)
    
    tag_infos = tag_manager.get_all_tags(memories)
    print(f"共有 {len(tag_infos)} 个不同标签:")
    for info in tag_infos[:10]:
        category = f"[{info.category}]" if info.category else ""
        print(f"  {info.name} {category}: {info.count} 次")
    
    # 测试5: 标签推荐
    print("\n5. 标签推荐")
    print("-" * 60)
    
    new_contents = [
        "明天要去健身房锻炼，计划跑步5公里",
        "记得下周二要交项目报告，需要整理数据",
        "我想学习摄影，买一台相机",
    ]
    
    for content in new_contents:
        suggested = tag_manager.suggest_tags(content, top_k=3)
        print(f"\n内容: {content}")
        print(f"推荐标签: {suggested}")
    
    # 测试6: 移除标签
    print("\n6. 移除标签")
    print("-" * 60)
    
    print(f"移除前 mem_001 标签: {memories_dict['mem_001']['tags']}")
    tag_manager.remove_tag("mem_001", "紧急", memories_dict)
    print(f"移除后 mem_001 标签: {memories_dict['mem_001']['tags']}")
    
    # 最终报告
    print("\n" + "=" * 60)
    print("测试报告")
    print("=" * 60)
    
    checks = [
        ("自动提取标签", len(memories) > 0 and all(len(m['tags']) > 0 for m in memories)),
        ("手动添加标签", "紧急" in memories_dict['mem_001']['tags']),
        ("按标签筛选", len(work_results) > 0 or len(goal_results) > 0),
        ("标签统计", len(tag_infos) > 0),
        ("标签推荐", len(tag_manager.suggest_tags("测试内容")) > 0),
        ("移除标签", "紧急" not in memories_dict['mem_001']['tags']),
    ]
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for name, result in checks:
        status = "OK" if result else "FAIL"
        print(f"[{status}] {name}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed}/{total} 通过")
    print("=" * 60)
    
    if passed == total:
        print("\n[OK] M6 Task 3 完成！标签系统工作正常")
    
    return passed == total


if __name__ == "__main__":
    success = test_tag_system()
    sys.exit(0 if success else 1)
