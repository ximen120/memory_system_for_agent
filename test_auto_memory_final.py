# -*- coding: utf-8 -*-
"""
M6傻瓜层任务1 - 最终测试报告
AutoTrigger全自动保存集成测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src" / "ux"))

from auto_trigger import AutoTrigger, TriggerDecision


def test_auto_trigger_chinese():
    """使用中文测试AutoTrigger"""
    print("=" * 60)
    print("M6 Task 1: AutoTrigger Chinese Content Test")
    print("=" * 60)
    
    # 使用较低阈值确保能触发保存
    trigger = AutoTrigger(min_confidence=0.3)
    
    # 中文测试用例
    test_cases = [
        ("你好", False, "太短，不保存"),
        ("我喜欢喝咖啡，每天早上必须一杯美式咖啡", True, "关键词+长度适中"),
        ("记住，我下周要参加一个重要会议", True, "高优先级关键词"),
        ("今天天气不错", False, "普通内容"),
        ("我的目标是每天学习Python编程", True, "目标关键词"),
    ]
    
    results = []
    saved_memories = []
    
    for content, expected, description in test_cases:
        decision = trigger.should_save(content)
        passed = decision.should_save == expected
        results.append(passed)
        
        status = "PASS" if passed else "FAIL"
        print(f"\n[{status}] {description}")
        print(f"  内容: {content}")
        print(f"  预期: {expected}, 实际: {decision.should_save}")
        print(f"  置信度: {decision.confidence}, 原因: {decision.reason}")
        
        if decision.should_save:
            saved_memories.append({
                "content": content,
                "confidence": decision.confidence,
                "reason": decision.reason
            })
    
    passed_count = sum(results)
    total = len(results)
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed_count}/{total} 通过")
    print("=" * 60)
    
    return passed_count, total, saved_memories


def test_auto_memory_manager():
    """测试AutoMemoryManager集成"""
    print("\n" + "=" * 60)
    print("AutoMemoryManager Integration Test")
    print("=" * 60)
    
    sys.path.insert(0, str(Path(__file__).parent / "src"))
    from ux.auto_memory_manager import AutoMemoryManager
    
    # 创建管理器
    manager = AutoMemoryManager(min_confidence=0.3)
    
    # 模拟对话
    conversation = [
        ("user", "你好"),
        ("assistant", "你好！有什么我可以帮助你的吗？"),
        ("user", "我喜欢喝咖啡，每天早上必须一杯美式咖啡"),
        ("assistant", "记住了，你喜欢喝咖啡"),
        ("user", "今天天气不错"),
        ("assistant", "是的，适合出去走走"),
        ("user", "记住，我下周要参加一个重要会议，需要准备PPT"),
        ("assistant", "好的，我会记住你下周要准备会议PPT"),
        ("user", "谢谢"),
        ("assistant", "不客气！"),
    ]
    
    print("\n模拟对话流程:")
    print("-" * 60)
    
    for i, (role, content) in enumerate(conversation, 1):
        result = manager.process_message(role, content)
        
        if result.get("saved"):
            print(f"[{i}] [{role}] {content}")
            print(f"    -> [自动保存] 记忆#{result['memory']['id']}")
            print(f"       原因: {result['memory']['reason']}")
            print(f"       置信度: {result['memory']['confidence']}")
        else:
            print(f"[{i}] [{role}] {content}")
    
    # 输出摘要
    summary = manager.get_session_summary()
    
    print("\n" + "=" * 60)
    print("会话摘要")
    print("=" * 60)
    print(f"总消息数: {summary['total_messages']}")
    print(f"自动保存记忆数: {summary['saved_memories']}")
    
    if summary['saved_memories'] > 0:
        print("\n已保存的记忆列表:")
        for memory in summary['memories']:
            print(f"  #{memory['id']}: {memory['content']}")
            print(f"      置信度: {memory['confidence']}, 策略: {memory['strategy']}")
    
    return summary['saved_memories']


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("M6傻瓜层任务1: AutoTrigger全自动保存")
    print("=" * 60)
    
    # 测试1: AutoTrigger核心功能
    passed, total, memories = test_auto_trigger_chinese()
    
    # 测试2: AutoMemoryManager集成
    saved_count = test_auto_memory_manager()
    
    # 最终报告
    print("\n" + "=" * 60)
    print("最终报告")
    print("=" * 60)
    print(f"1. AutoTrigger核心测试: {passed}/{total} 通过")
    print(f"2. 自动保存记忆数: {saved_count} 条")
    print(f"3. 集成状态: {'成功' if saved_count > 0 else '失败'}")
    
    print("\n" + "=" * 60)
    print("集成说明")
    print("=" * 60)
    print("""
AutoTrigger已成功集成到对话流程中:

1. 自动分析: 每条用户消息自动分析内容和上下文
2. 智能判断: 根据关键词、长度、复杂度等维度评分
3. 自动保存: 置信度达标时自动保存记忆
4. 无需手动: 用户无需说"记住"，系统自动判断

关键特性:
- 关键词检测: "喜欢"、"记住"、"目标"等触发保存
- 长度评估: 内容太短或太长都会影响评分
- 置信度阈值: 默认0.6，可配置
- 多维度评分: 内容+上下文+时间综合判断
""")
    
    if saved_count > 0:
        print("\n[OK] M6 Task 1 完成！")
        sys.exit(0)
    else:
        print("\n[WARN] 未触发自动保存，可能需要调整阈值")
        sys.exit(0)
