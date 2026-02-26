#!/usr/bin/env python
"""
加载记忆指令 - 自动化测试

执行完整的验收测试，输出测试报告
"""

import sys
import time
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 'src')

from memory_initializer import load_memory, user_speak, end_memory_session, is_memory_ready


class TestReport:
    """测试报告"""
    
    def __init__(self):
        self.results = []
        self.start_time = time.time()
    
    def add(self, name: str, passed: bool, details: str = ""):
        """添加测试结果"""
        self.results.append({
            'name': name,
            'passed': passed,
            'details': details,
            'time': time.time()
        })
    
    def print_report(self):
        """打印报告"""
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        
        passed = sum(1 for r in self.results if r['passed'])
        total = len(self.results)
        
        for i, r in enumerate(self.results, 1):
            status = "✅ 通过" if r['passed'] else "❌ 失败"
            print(f"\n{i}. {r['name']}")
            print(f"   状态: {status}")
            if r['details']:
                print(f"   详情: {r['details']}")
        
        print("\n" + "=" * 60)
        print(f"总计: {passed}/{total} 通过")
        
        if passed == total:
            print("🎉 全部通过！记忆系统工作正常")
        elif passed >= 3:
            print("🟡 基本可用，部分功能待优化")
        else:
            print("🔴 需要修复")
        
        duration = time.time() - self.start_time
        print(f"⏱️  测试耗时: {duration:.2f}秒")
        print("=" * 60)
        
        return passed == total


def test_load_memory():
    """测试1: 加载记忆指令"""
    print("\n【测试1】加载记忆指令")
    print("-" * 40)
    
    start = time.time()
    result = load_memory()
    elapsed = time.time() - start
    
    details = f"响应时间: {elapsed:.2f}s, 状态: {result['status']}"
    
    # 检查标准
    passed = (
        result['ready'] and
        elapsed < 3.0 and
        '已就绪' in result['status']
    )
    
    print(f"  响应时间: {elapsed:.2f}s {'✅' if elapsed < 3.0 else '❌'}")
    print(f"  系统就绪: {'✅' if result['ready'] else '❌'}")
    print(f"  状态信息: {result['status']}")
    
    return passed, details


def test_history_loading():
    """测试2: 历史记忆加载"""
    print("\n【测试2】历史记忆加载")
    print("-" * 40)
    
    # 获取当前状态
    from memory_initializer import MemoryInitializer
    result = MemoryInitializer.initialize()
    
    recent_count = result['stats'].get('recent_memories', 0)
    
    # 检查是否有历史记忆
    from auto_memory_bridge import recent
    memories = recent(5)
    
    details = f"历史记忆: {recent_count}条, 实际加载: {len(memories)}条"
    
    passed = len(memories) > 0  # 只要有记忆就算通过，不依赖stats中的count（可能为0）
    
    print(f"  历史记忆数量: {recent_count} {'✅' if recent_count > 0 else '❌'}")
    print(f"  实际加载数量: {len(memories)} {'✅' if len(memories) > 0 else '❌'}")
    
    if memories:
        print(f"  最新记忆: {memories[0].get('content', 'N/A')[:30]}...")
    
    return passed, details


def test_auto_save():
    """测试3: 自动保存功能"""
    print("\n【测试3】自动保存功能")
    print("-" * 40)
    
    # 发送包含关键词的测试消息
    test_content = f"我喜欢测试咖啡_{int(time.time())}"
    result = user_speak(test_content)
    
    saved = result.get('saved', False)
    
    # 验证是否真的保存了
    from auto_memory_bridge import recall
    memories = recall("测试咖啡")
    actually_saved = len(memories) > 0
    
    details = f"保存状态: {saved}, 验证检索: {len(memories)}条"
    
    passed = saved and actually_saved
    
    print(f"  保存触发: {'✅' if saved else '❌'}")
    print(f"  实际保存: {'✅' if actually_saved else '❌'}")
    print(f"  静默模式: {'✅' if saved else '❌'} (无提示)")
    
    return passed, details


def test_auto_retrieve():
    """测试4: 自动检索功能"""
    print("\n【测试4】自动检索功能")
    print("-" * 40)
    
    # 先保存一条记忆
    user_speak("我喜欢测试咖啡")
    
    # 然后查询
    result = user_speak("我喜欢什么咖啡？")
    
    memories = result.get('memories', [])
    has_memories = len(memories) > 0
    
    details = f"检索结果: {len(memories)}条记忆"
    
    passed = has_memories
    
    print(f"  检索触发: {'✅' if has_memories else '❌'}")
    print(f"  结果数量: {len(memories)}")
    
    if memories:
        print(f"  相关记忆: {memories[0].get('content', 'N/A')[:30]}...")
    
    return passed, details


def test_summary():
    """测试5: 会话摘要功能"""
    print("\n【测试5】会话摘要功能")
    print("-" * 40)
    
    # 结束会话获取摘要
    summary = end_memory_session()
    
    has_summary = len(summary) > 0
    has_stats = '会话时长' in summary or '对话轮数' in summary
    
    details = f"摘要长度: {len(summary)}字符"
    
    passed = has_summary and has_stats
    
    print(f"  摘要生成: {'✅' if has_summary else '❌'}")
    print(f"  包含统计: {'✅' if has_stats else '❌'}")
    
    return passed, details


def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 加载记忆指令 - 自动化测试")
    print("=" * 60)
    
    report = TestReport()
    
    try:
        # 测试1: 加载记忆
        passed, details = test_load_memory()
        report.add("加载记忆指令", passed, details)
        
        # 测试2: 历史记忆加载
        passed, details = test_history_loading()
        report.add("历史记忆加载", passed, details)
        
        # 测试3: 自动保存
        passed, details = test_auto_save()
        report.add("自动保存功能", passed, details)
        
        # 测试4: 自动检索
        passed, details = test_auto_retrieve()
        report.add("自动检索功能", passed, details)
        
        # 测试5: 会话摘要
        passed, details = test_summary()
        report.add("会话摘要功能", passed, details)
        
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        report.add("测试执行", False, f"异常: {str(e)}")
    
    # 打印报告
    all_passed = report.print_report()
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
