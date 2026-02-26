# -*- coding: utf-8 -*-
"""
M6傻瓜层任务1测试报告
AutoTrigger全自动保存集成测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src" / "ux"))

from auto_trigger import AutoTrigger, TriggerDecision


def test_auto_trigger():
    """测试AutoTrigger核心功能"""
    print("M6 Task 1: AutoTrigger Integration Test")
    print("=" * 60)
    
    trigger = AutoTrigger(min_confidence=0.5)
    
    # 测试用例
    test_cases = [
        ("ni hao", False, "Too short"),
        ("An ge xi huan he ka fei, mei tian zao shang bi xu yi bei", True, "Keywords + good length"),
        ("Ji zhu, wo xia zhou yao shen qing", True, "High priority keyword"),
        ("Jin tian tian qi bu cuo", False, "Common content"),
    ]
    
    results = []
    for content, expected, description in test_cases:
        decision = trigger.should_save(content)
        passed = decision.should_save == expected
        results.append(passed)
        
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {description}")
        print(f"      Content: {content[:40]}...")
        print(f"      Expected: {expected}, Got: {decision.should_save}, Confidence: {decision.confidence}")
        print()
    
    passed_count = sum(results)
    total = len(results)
    
    print("=" * 60)
    print(f"Results: {passed_count}/{total} tests passed")
    print("=" * 60)
    
    return passed_count == total


def test_integration():
    """测试集成效果"""
    print("\nIntegration Test:")
    print("-" * 60)
    
    # 模拟对话流程
    trigger = AutoTrigger(min_confidence=0.5)
    
    # 模拟多轮对话
    messages = [
        "Hello",
        "I like drinking coffee every morning",
        "Remember my meeting next week",
        "Thanks",
    ]
    
    saved_count = 0
    for msg in messages:
        decision = trigger.should_save(msg)
        if decision.should_save:
            saved_count += 1
            print(f"[SAVED] {msg[:40]}... (confidence: {decision.confidence})")
        else:
            print(f"[SKIP]  {msg[:40]}... (confidence: {decision.confidence})")
    
    print(f"\nTotal saved: {saved_count}/{len(messages)}")
    
    # 预期应该保存2条（咖啡喜好、会议提醒）
    return saved_count >= 2


if __name__ == "__main__":
    test1_passed = test_auto_trigger()
    test2_passed = test_integration()
    
    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(f"AutoTrigger Core: {'PASS' if test1_passed else 'FAIL'}")
    print(f"Integration Test: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n[OK] M6 Task 1 completed successfully!")
        sys.exit(0)
    else:
        print("\n[FAIL] Some tests failed")
        sys.exit(1)
