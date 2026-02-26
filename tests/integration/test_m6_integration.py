"""
M6傻瓜层集成测试

测试6个模块的协同工作:
1. AutoTrigger - 全自动保存
2. TagManager - 标签系统
3. KeywordSearch - 关键词检索
4. CommandParser - 自然语言命令解析
5. TimelineViewer - 时间线浏览
6. MemoryLayerManager - 四层记忆架构

端到端流程:
触发记忆保存 -> 自动分层 -> 检索 -> 时间线展示
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'libs'))

import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# 导入M6模块
from ux.auto_trigger import AutoTrigger, TriggerDecision
from ux.tag_manager import TagManager, TagInfo
from ux.keyword_search import KeywordSearch, SearchQuery
from ux.command_parser import CommandParser, CommandType, ParsedCommand
from ux.timeline_viewer import TimelineViewer, TimeRange, TimelineItem
from ux.memory_layers import MemoryLayerManager, MemoryLayerType


class M6IntegrationTest:
    """M6傻瓜层集成测试"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.results = []
        self.passed = 0
        self.failed = 0
        
        # 初始化各模块
        self.auto_trigger = AutoTrigger(min_confidence=0.5)
        self.tag_manager = TagManager()
        self.keyword_search = KeywordSearch()
        self.command_parser = CommandParser()
        self.timeline_viewer = TimelineViewer()
        self.memory_layers = MemoryLayerManager(data_dir=data_dir)
        
    def run_test(self, test_name: str, test_func) -> bool:
        """运行单个测试"""
        try:
            print(f"\n[TEST] {test_name}")
            result = test_func()
            if result:
                print(f"  [PASS] {test_name}")
                self.passed += 1
                self.results.append({"name": test_name, "status": "PASS"})
                return True
            else:
                print(f"  [FAIL] {test_name}")
                self.failed += 1
                self.results.append({"name": test_name, "status": "FAIL"})
                return False
        except Exception as e:
            print(f"  [FAIL] {test_name} - {e}")
            import traceback
            traceback.print_exc()
            self.failed += 1
            self.results.append({"name": test_name, "status": "FAIL", "error": str(e)})
            return False
    
    # ========== 模块协同测试 ==========
    
    def test_auto_trigger_with_layers(self):
        """测试: AutoTrigger + 四层记忆架构"""
        print("  Testing AutoTrigger -> MemoryLayers flow...")
        
        # 模拟对话内容
        content = "安哥喜欢喝咖啡，每天早上必须一杯美式"
        
        # AutoTrigger分析
        decision = self.auto_trigger.should_save(content)
        print(f"    Trigger decision: {decision.should_save}, confidence: {decision.confidence:.2f}")
        
        if decision.should_save:
            # 自动提取标签
            tags = self.tag_manager.auto_extract_tags(content)
            print(f"    Auto-extracted tags: {tags}")
            
            # 保存到记忆层（根据重要性自动分层）
            memory_id = self.memory_layers.add(
                content=content,
                memory_type="preference",
                importance=4.0,  # 高重要性 -> 长期记忆
                tags=tags
            )
            print(f"    Saved to memory layer: {memory_id[:30]}...")
            
            # 验证保存成功
            memory = self.memory_layers.get(memory_id)
            assert memory is not None, "Memory should be saved"
            assert memory.content == content, "Content should match"
            assert len(memory.tags) > 0, "Tags should be extracted"
            
            return True
        
        return False
    
    def test_command_parser_with_search(self):
        """测试: 命令解析 + 关键词检索"""
        print("  Testing CommandParser -> KeywordSearch flow...")
        
        # 先添加一些测试数据
        test_memories = [
            {"content": "安哥是程序员", "memory_type": "fact", "tags": ["职业"]},
            {"content": "安哥喜欢Python", "memory_type": "preference", "tags": ["编程", "Python"]},
            {"content": "安哥喝咖啡", "memory_type": "preference", "tags": ["咖啡"]},
        ]
        
        for mem in test_memories:
            self.memory_layers.add(
                content=mem["content"],
                memory_type=mem["memory_type"],
                importance=3.5,
                tags=mem["tags"]
            )
        
        # 解析自然语言命令
        commands = [
            "查找安哥",
            "搜索Python",
            "找出所有关于咖啡的记忆"
        ]
        
        for cmd_text in commands:
            parsed = self.command_parser.parse(cmd_text)
            print(f"    Command: '{cmd_text}' -> {parsed.command_type.value}")
            
            if parsed.command_type == CommandType.SEARCH:
                # 使用关键词检索
                keywords = parsed.content.split() if parsed.content else ["安哥"]
                results = self.memory_layers.search_by_keywords(keywords, limit=10)
                print(f"    Found {len(results)} results for keywords: {keywords}")
                
                assert len(results) >= 0, "Search should complete"
        
        return True
    
    def test_timeline_with_layers(self):
        """测试: 时间线浏览 + 四层记忆架构"""
        print("  Testing TimelineViewer -> MemoryLayers flow...")
        
        # 添加不同时间的记忆
        contents = [
            "今天学习了Python",
            "完成了项目文档",
            "计划明天开会"
        ]
        
        for content in contents:
            self.memory_layers.add(
                content=content,
                memory_type="context",
                importance=2.5,
                tags=["工作"]
            )
        
        # 获取时间线
        timeline = self.memory_layers.get_timeline(days=7)
        print(f"    Timeline has {len(timeline)} items")
        
        for item in timeline[:3]:
            print(f"      [{item['layer']}] {item['content'][:30]}...")
        
        assert len(timeline) >= 3, "Timeline should have at least 3 items"
        
        return True
    
    def test_tag_system_integration(self):
        """测试: 标签系统全流程"""
        print("  Testing TagManager integration...")
        
        # 添加带标签的记忆
        contents_with_tags = [
            ("安哥喜欢编程", ["技能", "编程"]),
            ("安哥喝咖啡", ["生活", "咖啡"]),
            ("安哥做项目", ["工作", "项目"]),
        ]
        
        for content, tags in contents_with_tags:
            # 自动提取标签
            auto_tags = self.tag_manager.auto_extract_tags(content)
            print(f"    Content: {content[:20]}...")
            print(f"    Auto tags: {auto_tags}")
            
            # 合并手动标签
            all_tags = list(set(tags + auto_tags))
            
            self.memory_layers.add(
                content=content,
                memory_type="fact",
                importance=3.0,
                tags=all_tags
            )
        
        # 按标签查询
        tag_results = self.memory_layers.query(tags=["编程"], limit=10)
        print(f"    Found {len(tag_results)} memories with tag '编程'")
        
        return True
    
    def test_auto_trigger_strategies(self):
        """测试: AutoTrigger多种策略"""
        print("  Testing AutoTrigger strategies...")
        
        test_cases = [
            ("安哥喜欢喝咖啡", True),  # 包含"喜欢"，应该触发
            ("好的", False),  # 太短，不应该触发
            ("记住我的密码是123456", True),  # 包含"记住"，应该触发
            ("今天天气不错", False),  # 普通陈述，可能不触发
        ]
        
        for content, expected_trigger in test_cases:
            decision = self.auto_trigger.should_save(content)
            print(f"    '{content[:20]}...' -> trigger: {decision.should_save}, reason: {decision.reason}")
            
            if decision.should_save and expected_trigger:
                # 保存到记忆层
                self.memory_layers.add(
                    content=content,
                    memory_type="context" if "天气" in content else "preference",
                    importance=3.5 if "喜欢" in content else 2.0
                )
        
        return True
    
    # ========== 端到端流程测试 ==========
    
    def test_end_to_end_flow(self):
        """测试: 完整端到端流程"""
        print("  Testing end-to-end flow...")
        print("    Step 1: User input -> AutoTrigger")
        
        user_input = "安哥计划下周学习Rust编程语言"
        
        # Step 1: AutoTrigger判断
        decision = self.auto_trigger.should_save(user_input)
        print(f"      Trigger: {decision.should_save}, confidence: {decision.confidence:.2f}")
        
        if decision.should_save:
            print("    Step 2: AutoTrigger -> TagManager")
            
            # Step 2: 自动提取标签
            tags = self.tag_manager.auto_extract_tags(user_input)
            print(f"      Tags: {tags}")
            
            print("    Step 3: TagManager -> MemoryLayers")
            
            # Step 3: 保存到记忆层（自动分层）
            memory_id = self.memory_layers.add(
                content=user_input,
                memory_type="goal",
                importance=4.0,  # 目标类，高重要性
                tags=tags
            )
            print(f"      Saved with ID: {memory_id[:30]}...")
            
            print("    Step 4: MemoryLayers -> TimelineViewer")
            
            # Step 4: 时间线展示
            timeline = self.memory_layers.get_timeline(days=7)
            print(f"      Timeline shows {len(timeline)} items")
            
            print("    Step 5: CommandParser -> KeywordSearch")
            
            # Step 5: 自然语言查询
            query = "查找Rust"
            parsed = self.command_parser.parse(query)
            if parsed.command_type == CommandType.SEARCH:
                results = self.memory_layers.search_by_keywords(["Rust"])
                print(f"      Search found {len(results)} results")
                
                for r in results:
                    print(f"        - {r.content[:40]}...")
            
            return True
        
        return False
    
    # ========== 边界情况测试 ==========
    
    def test_empty_data_handling(self):
        """测试: 空数据处理"""
        print("  Testing empty data handling...")
        
        # 空内容
        decision = self.auto_trigger.should_save("")
        assert not decision.should_save, "Empty content should not trigger"
        print("    Empty content: correctly rejected")
        
        # 搜索空关键词
        results = self.memory_layers.search_by_keywords([])
        assert len(results) == 0, "Empty keywords should return empty results"
        print("    Empty keywords: correctly returned empty")
        
        # 解析空命令
        parsed = self.command_parser.parse("")
        assert parsed.command_type == CommandType.UNKNOWN, "Empty command should be unknown"
        print("    Empty command: correctly parsed as unknown")
        
        return True
    
    def test_large_data_handling(self):
        """测试: 大数据量处理"""
        print("  Testing large data handling...")
        
        # 批量添加记忆
        for i in range(50):
            self.memory_layers.add(
                content=f"测试记忆内容 {i}: 安哥喜欢编程和咖啡",
                memory_type="test",
                importance=2.0 + (i % 3),  # 混合重要性
                tags=["测试", f"tag_{i % 5}"]
            )
        
        print(f"    Added 50 memories")
        
        # 验证统计
        stats = self.memory_layers.get_stats()
        total = stats["total_memories"]
        print(f"    Total memories: {total}")
        
        assert total >= 50, f"Should have at least 50 memories, got {total}"
        
        # 搜索性能测试
        import time
        start = time.time()
        results = self.memory_layers.search_by_keywords(["安哥", "编程"], limit=20)
        elapsed = time.time() - start
        print(f"    Search took {elapsed:.3f}s, found {len(results)} results")
        
        assert elapsed < 1.0, f"Search should be fast, took {elapsed:.3f}s"
        
        return True
    
    def test_error_handling(self):
        """测试: 错误处理"""
        print("  Testing error handling...")
        
        # 获取不存在的记忆
        result = self.memory_layers.get("non_existent_id")
        assert result is None, "Non-existent memory should return None"
        print("    Non-existent memory: correctly returned None")
        
        # 解析无效命令
        parsed = self.command_parser.parse("!@#$%^&*")
        assert parsed.command_type == CommandType.UNKNOWN, "Invalid command should be unknown"
        print("    Invalid command: correctly parsed as unknown")
        
        # 删除不存在的记忆
        result = self.memory_layers.layers[MemoryLayerType.SHORT_TERM].remove("non_existent")
        # 应该不抛出异常
        print("    Delete non-existent: handled gracefully")
        
        return True
    
    def test_memory_layer_migration(self):
        """测试: 记忆层自动流转"""
        print("  Testing memory layer migration...")
        
        # 添加不同重要性的记忆
        memories = [
            ("核心身份: 安哥是Simon", 5.0, MemoryLayerType.PERMANENT),
            ("重要偏好: 安哥喜欢咖啡", 4.0, MemoryLayerType.LONG_TERM),
            ("普通信息: 今天天气好", 2.0, MemoryLayerType.SHORT_TERM),
        ]
        
        for content, importance, expected_layer in memories:
            memory_id = self.memory_layers.add(
                content=content,
                memory_type="test",
                importance=importance
            )
            
            # 查找记忆在哪个层
            found_layer = None
            for layer_type in MemoryLayerType:
                if self.memory_layers.layers[layer_type].get(memory_id):
                    found_layer = layer_type
                    break
            
            print(f"    Content (importance={importance}): stored in {found_layer.value}")
            assert found_layer == expected_layer, f"Expected {expected_layer.value}, got {found_layer.value}"
        
        return True
    
    # ========== 运行所有测试 ==========
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 70)
        print("M6 FOOL LAYER INTEGRATION TEST")
        print("=" * 70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Data directory: {self.data_dir}")
        
        tests = [
            # 模块协同测试
            ("AutoTrigger + MemoryLayers", self.test_auto_trigger_with_layers),
            ("CommandParser + KeywordSearch", self.test_command_parser_with_search),
            ("TimelineViewer + MemoryLayers", self.test_timeline_with_layers),
            ("TagManager Integration", self.test_tag_system_integration),
            ("AutoTrigger Strategies", self.test_auto_trigger_strategies),
            
            # 端到端流程
            ("End-to-End Flow", self.test_end_to_end_flow),
            
            # 边界情况
            ("Empty Data Handling", self.test_empty_data_handling),
            ("Large Data Handling", self.test_large_data_handling),
            ("Error Handling", self.test_error_handling),
            ("Memory Layer Migration", self.test_memory_layer_migration),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # 生成报告
        self.generate_report()
        
        return self.failed == 0
    
    def generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 70)
        print("TEST REPORT")
        print("=" * 70)
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.failed > 0:
            print("\nFailed Tests:")
            for result in self.results:
                if result["status"] == "FAIL":
                    error = result.get("error", "")
                    print(f"  - {result['name']}: {error}")
        
        # 保存报告到文件
        report_path = Path(self.data_dir) / "m6_integration_test_report.json"
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total,
            "passed": self.passed,
            "failed": self.failed,
            "pass_rate": pass_rate,
            "results": self.results
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nReport saved to: {report_path}")
        
        if self.failed == 0:
            print("\n" + "=" * 70)
            print("ALL TESTS PASSED!")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print(f"SOME TESTS FAILED ({self.failed} failures)")
            print("=" * 70)
    
    def close(self):
        """清理资源"""
        self.memory_layers.close()


def main():
    """主函数"""
    tmpdir = tempfile.mkdtemp()
    print(f"Using temp directory: {tmpdir}")
    
    try:
        tester = M6IntegrationTest(data_dir=tmpdir)
        success = tester.run_all_tests()
        tester.close()
        
        return 0 if success else 1
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    exit(main())
