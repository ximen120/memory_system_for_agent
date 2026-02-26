"""
AutoTrigger修复验证测试

验证"喜欢"关键词触发问题已修复
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

from ux.auto_trigger import AutoTrigger


def test_like_keyword():
    """测试'喜欢'关键词触发"""
    print("=" * 60)
    print("AutoTrigger '喜欢'关键词修复验证")
    print("=" * 60)
    
    trigger = AutoTrigger(min_confidence=0.5)
    
    # 测试用例
    test_cases = [
        # (内容, 期望触发, 说明)
        ("安哥喜欢喝咖啡", True, "包含'喜欢'，应该触发"),
        ("我喜欢Python编程", True, "包含'喜欢'，应该触发"),
        ("安哥喜欢喝茶", True, "包含'喜欢'，应该触发"),
        ("记住这个重要信息", True, "包含'记住'，应该触发"),
        ("计划下周去旅行", True, "包含'计划'，应该触发"),
        ("好的", False, "太短，不应该触发"),
        ("今天天气不错", False, "无关键词，可能不触发"),
        ("安哥是程序员", True, "包含'是'身份信息，应该触发"),
        ("我讨厌等待", True, "包含'讨厌'，应该触发"),
        ("我要学习Rust", True, "包含'我要'，应该触发"),
    ]
    
    passed = 0
    failed = 0
    
    for content, expected, description in test_cases:
        decision = trigger.should_save(content)
        actual = decision.should_save
        
        status = "[OK]" if actual == expected else "[FAIL]"
        
        print(f"\n{status} 测试: {description}")
        print(f"   内容: '{content}'")
        print(f"   期望: {'触发' if expected else '不触发'}")
        print(f"   实际: {'触发' if actual else '不触发'} (置信度: {decision.confidence:.2f})")
        print(f"   原因: {decision.reason}")
        
        if actual == expected:
            passed += 1
        else:
            failed += 1
    
    # 统计
    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)
    total = passed + failed
    print(f"总测试: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {passed/total*100:.1f}%")
    
    if failed == 0:
        print("\n[OK] 所有测试通过！'喜欢'关键词修复成功！")
    else:
        print(f"\n[WARN] 有 {failed} 个测试失败")
    
    return failed == 0


def test_keyword_coverage():
    """测试关键词覆盖范围"""
    print("\n" + "=" * 60)
    print("关键词覆盖验证")
    print("=" * 60)
    
    trigger = AutoTrigger()
    
    # 高优先级关键词
    high_priority_keywords = [
        "喜欢", "爱好", "偏好", "讨厌", "厌恶",
        "记住", "计划", "目标", "重要", "我是"
    ]
    
    print("\n高优先级关键词测试:")
    for kw in high_priority_keywords:
        content = f"安哥{kw}测试内容"
        decision = trigger.should_save(content)
        status = "[OK]" if decision.should_save else "[NO]"
        print(f"  {status} '{kw}' -> {'触发' if decision.should_save else '不触发'} (置信度: {decision.confidence:.2f})")
    
    # 中优先级关键词
    medium_priority_keywords = [
        "觉得", "习惯", "经常", "明天", "非常"
    ]
    
    print("\n中优先级关键词测试:")
    for kw in medium_priority_keywords:
        content = f"安哥{kw}测试内容，这个内容比较长"
        decision = trigger.should_save(content)
        print(f"  '{kw}' -> {'触发' if decision.should_save else '不触发'} (置信度: {decision.confidence:.2f})")


def main():
    """主函数"""
    success1 = test_like_keyword()
    test_keyword_coverage()
    
    print("\n" + "=" * 60)
    print("AutoTrigger修复验证完成")
    print("=" * 60)
    
    return 0 if success1 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
