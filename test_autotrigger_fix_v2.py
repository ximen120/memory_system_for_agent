"""
AutoTrigger修复验证测试 V2
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

from ux.auto_trigger_fixed import AutoTrigger


def test_like_keyword():
    """测试'喜欢'关键词触发"""
    print("=" * 60)
    print("AutoTrigger '喜欢'关键词修复验证")
    print("=" * 60)
    
    trigger = AutoTrigger()
    
    test_cases = [
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


def main():
    success = test_like_keyword()
    return 0 if success else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
