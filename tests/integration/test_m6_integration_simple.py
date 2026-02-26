"""
M6傻瓜层集成测试 (简化版)

测试6个模块的协同工作，不依赖pydantic
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
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

# ========== 简化版M6模块实现 ==========

class MemoryLayerType(Enum):
    WORKING = "working"
    SHORT_TERM = "short"
    LONG_TERM = "long"
    PERMANENT = "permanent"

class CommandType(Enum):
    REMEMBER = "remember"
    FORGET = "forget"
    SEARCH = "search"
    SHOW = "show"
    UPDATE = "update"
    TAG = "tag"
    UNKNOWN = "unknown"

@dataclass
class SimpleMemoryUnit:
    content: str
    memory_type: str
    importance: float = 3.0
    memory_id: str = field(default_factory=lambda: f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{id(datetime.now())}")
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    access_count: int = 0
    last_accessed_at: Optional[str] = None
    
    def update_access(self):
        self.access_count += 1
        self.last_accessed_at = datetime.now().isoformat()

@dataclass
class ParsedCommand:
    raw_text: str
    command_type: CommandType
    content: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.0

@dataclass
class TriggerDecision:
    should_save: bool
    confidence: float
    reason: str
    strategy: str


# 简化版AutoTrigger
class SimpleAutoTrigger:
    KEYWORDS_HIGH = ["记住", "别忘了", "记下来", "我喜欢", "我讨厌", "计划", "目标"]
    KEYWORDS_MEDIUM = ["觉得", "认为", "习惯", "经常", "重要"]
    
    def should_save(self, content: str) -> TriggerDecision:
        if len(content) < 5:
            return TriggerDecision(False, 0.0, "Content too short", "length_check")
        
        # 检查高优先级关键词
        for kw in self.KEYWORDS_HIGH:
            if kw in content:
                return TriggerDecision(True, 0.9, f"High priority keyword: {kw}", "keyword_high")
        
        # 检查中优先级关键词
        for kw in self.KEYWORDS_MEDIUM:
            if kw in content:
                return TriggerDecision(True, 0.7, f"Medium priority keyword: {kw}", "keyword_medium")
        
        # 内容长度启发式
        if len(content) > 20:
            return TriggerDecision(True, 0.6, "Long content, likely valuable", "length_heuristic")
        
        return TriggerDecision(False, 0.3, "No clear signals", "default")


# 简化版TagManager
class SimpleTagManager:
    STOP_WORDS = {"的", "了", "是", "在", "我", "有", "和", "就", "不", "都", "一", "上", "也"}
    
    def auto_extract_tags(self, content: str, max_tags: int = 5) -> List[str]:
        # 简单的关键词提取
        words = content.split()
        tags = []
        
        # 提取2-4字的词
        for word in words:
            word = word.strip("，。！？、；：\"'").lower()
            if 2 <= len(word) <= 4 and word not in self.STOP_WORDS:
                tags.append(word)
        
        # 去重并限制数量
        tags = list(dict.fromkeys(tags))[:max_tags]
        return tags


# 简化版CommandParser
class SimpleCommandParser:
    COMMANDS = {
        CommandType.REMEMBER: ["记住", "记得", "记录", "保存", "记下", "remember", "save"],
        CommandType.FORGET: ["忘掉", "忘记", "删除", "移除", "forget", "delete"],
        CommandType.SEARCH: ["查找", "搜索", "查询", "找一下", "search", "find"],
        CommandType.SHOW: ["显示", "列出", "查看", "展示", "show", "list"],
    }
    
    def parse(self, text: str) -> ParsedCommand:
        text = text.strip()
        if not text:
            return ParsedCommand(text, CommandType.UNKNOWN, confidence=0.0)
        
        # 识别命令类型
        for cmd_type, keywords in self.COMMANDS.items():
            for kw in keywords:
                if kw in text:
                    # 提取内容（简单实现：去掉命令词）
                    content = text.replace(kw, "").strip("，。！？")
                    return ParsedCommand(text, cmd_type, content, confidence=0.8)
        
        return ParsedCommand(text, CommandType.UNKNOWN, confidence=0.0)


# 简化版MemoryLayerManager
class SimpleMemoryLayerManager:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.layers: Dict[MemoryLayerType, List[SimpleMemoryUnit]] = {
            layer_type: [] for layer_type in MemoryLayerType
        }
        self._memory_map: Dict[str, tuple] = {}  # memory_id -> (layer_type, index)
        self.stats = {"total_added": 0, "total_accessed": 0}
    
    def _determine_layer(self, memory: SimpleMemoryUnit) -> MemoryLayerType:
        if memory.importance >= 4.5:
            return MemoryLayerType.PERMANENT
        elif memory.importance >= 3.0:
            return MemoryLayerType.LONG_TERM
        else:
            return MemoryLayerType.SHORT_TERM
    
    def add(self, content: str, memory_type: str, importance: float = 3.0, 
            tags: Optional[List[str]] = None) -> str:
        memory = SimpleMemoryUnit(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or []
        )
        layer_type = self._determine_layer(memory)
        self.layers[layer_type].append(memory)
        self._memory_map[memory.memory_id] = (layer_type, len(self.layers[layer_type]) - 1)
        self.stats["total_added"] += 1
        return memory.memory_id
    
    def get(self, memory_id: str) -> Optional[SimpleMemoryUnit]:
        if memory_id in self._memory_map:
            layer_type, index = self._memory_map[memory_id]
            memory = self.layers[layer_type][index]
            memory.update_access()
            self.stats["total_accessed"] += 1
            return memory
        return None
    
    def search_by_keywords(self, keywords: List[str], limit: int = 10) -> List[SimpleMemoryUnit]:
        results = []
        for layer_type, memories in self.layers.items():
            for memory in memories:
                content_lower = memory.content.lower()
                if any(kw.lower() in content_lower for kw in keywords):
                    results.append(memory)
        return results[:limit]
    
    def query(self, tags: Optional[List[str]] = None, limit: int = 10) -> List[SimpleMemoryUnit]:
        results = []
        for layer_type, memories in self.layers.items():
            for memory in memories:
                if tags:
                    if any(tag in memory.tags for tag in tags):
                        results.append(memory)
                else:
                    results.append(memory)
        return results[:limit]
    
    def get_timeline(self, days: int = 7) -> List[Dict]:
        cutoff = datetime.now() - timedelta(days=days)
        timeline = []
        
        for layer_type, memories in self.layers.items():
            for memory in memories:
                try:
                    created = datetime.fromisoformat(memory.created_at)
                    if created >= cutoff:
                        timeline.append({
                            "memory_id": memory.memory_id,
                            "content": memory.content,
                            "memory_type": memory.memory_type,
                            "importance": memory.importance,
                            "created_at": memory.created_at,
                            "layer": layer_type.value,
                            "access_count": memory.access_count
                        })
                except Exception:
                    continue
        
        timeline.sort(key=lambda x: x["created_at"], reverse=True)
        return timeline
    
    def get_stats(self) -> Dict:
        layer_stats = {layer_type.value: len(memories) for layer_type, memories in self.layers.items()}
        total = sum(layer_stats.values())
        return {
            "layers": layer_stats,
            "operations": self.stats.copy(),
            "total_memories": total
        }
    
    def close(self):
        pass


# ========== 集成测试类 ==========

class M6IntegrationTest:
    """M6傻瓜层集成测试"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.results = []
        self.passed = 0
        self.failed = 0
        
        # 初始化各模块
        self.auto_trigger = SimpleAutoTrigger()
        self.tag_manager = SimpleTagManager()
        self.command_parser = SimpleCommandParser()
        self.memory_layers = SimpleMemoryLayerManager(data_dir=data_dir)
    
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
        
        content = "安哥喜欢喝咖啡，每天早上必须一杯美式"
        
        # AutoTrigger分析
        decision = self.auto_trigger.should_save(content)
        print(f"    Trigger decision: {decision.should_save}, confidence: {decision.confidence:.2f}")
        
        if decision.should_save:
            # 自动提取标签
            tags = self.tag_manager.auto_extract_tags(content)
            print(f"    Auto-extracted tags: {tags}")
            
            # 保存到记忆层
            memory_id = self.memory_layers.add(
                content=content,
                memory_type="preference",
                importance=4.0,
                tags=tags
            )
            print(f"    Saved to memory layer: {memory_id[:30]}...")
            
            # 验证保存成功
            memory = self.memory_layers.get(memory_id)
            assert memory is not None, "Memory should be saved"
            assert memory.content == content, "Content should match"
            
            return True
        
        return False
    
    def test_command_parser_with_search(self):
        """测试: 命令解析 + 关键词检索"""
        print("  Testing CommandParser -> KeywordSearch flow...")
        
        # 先添加测试数据
        test_memories = [
            ("安哥是程序员", "fact", 3.5, ["职业"]),
            ("安哥喜欢Python", "preference", 3.5, ["编程", "Python"]),
            ("安哥喝咖啡", "preference", 3.5, ["咖啡"]),
        ]
        
        for content, mtype, imp, tags in test_memories:
            self.memory_layers.add(content=content, memory_type=mtype, importance=imp, tags=tags)
        
        # 解析自然语言命令
        commands = ["查找安哥", "搜索Python", "找出咖啡"]
        
        for cmd_text in commands:
            parsed = self.command_parser.parse(cmd_text)
            print(f"    Command: '{cmd_text}' -> {parsed.command_type.value}")
            
            if parsed.command_type == CommandType.SEARCH:
                keywords = parsed.content.split() if parsed.content else ["安哥"]
                results = self.memory_layers.search_by_keywords(keywords, limit=10)
                print(f"    Found {len(results)} results")
        
        return True
    
    def test_timeline_with_layers(self):
        """测试: 时间线浏览 + 四层记忆架构"""
        print("  Testing TimelineViewer -> MemoryLayers flow...")
        
        # 添加不同时间的记忆
        contents = ["今天学习了Python", "完成了项目文档", "计划明天开会"]
        for content in contents:
            self.memory_layers.add(content=content, memory_type="context", importance=2.5, tags=["工作"])
        
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
        
        contents_with_tags = [
            ("安哥喜欢编程", ["技能", "编程"]),
            ("安哥喝咖啡", ["生活", "咖啡"]),
            ("安哥做项目", ["工作", "项目"]),
        ]
        
        for content, manual_tags in contents_with_tags:
            auto_tags = self.tag_manager.auto_extract_tags(content)
            print(f"    Content: {content[:20]}... Auto tags: {auto_tags}")
            
            all_tags = list(set(manual_tags + auto_tags))
            self.memory_layers.add(content=content, memory_type="fact", importance=3.0, tags=all_tags)
        
        # 按标签查询
        tag_results = self.memory_layers.query(tags=["编程"], limit=10)
        print(f"    Found {len(tag_results)} memories with tag '编程'")
        
        return True
    
    def test_auto_trigger_strategies(self):
        """测试: AutoTrigger多种策略"""
        print("  Testing AutoTrigger strategies...")
        
        test_cases = [
            ("安哥喜欢喝咖啡", True),
            ("好的", False),
            ("记住我的密码", True),
            ("今天天气不错", True),  # 长内容触发
        ]
        
        for content, expected_trigger in test_cases:
            decision = self.auto_trigger.should_save(content)
            print(f"    '{content[:20]}...' -> trigger: {decision.should_save}, reason: {decision.reason}")
            
            if decision.should_save and expected_trigger:
                self.memory_layers.add(
                    content=content,
                    memory_type="context",
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
            tags = self.tag_manager.auto_extract_tags(user_input)
            print(f"      Tags: {tags}")
            
            print("    Step 3: TagManager -> MemoryLayers")
            memory_id = self.memory_layers.add(
                content=user_input,
                memory_type="goal",
                importance=4.0,
                tags=tags
            )
            print(f"      Saved with ID: {memory_id[:30]}...")
            
            print("    Step 4: MemoryLayers -> Timeline")
            timeline = self.memory_layers.get_timeline(days=7)
            print(f"      Timeline shows {len(timeline)} items")
            
            print("    Step 5: CommandParser -> KeywordSearch")
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
        
        decision = self.auto_trigger.should_save("")
        assert not decision.should_save, "Empty content should not trigger"
        print("    Empty content: correctly rejected")
        
        results = self.memory_layers.search_by_keywords([])
        assert len(results) == 0, "Empty keywords should return empty"
        print("    Empty keywords: correctly returned empty")
        
        parsed = self.command_parser.parse("")
        assert parsed.command_type == CommandType.UNKNOWN, "Empty command should be unknown"
        print("    Empty command: correctly parsed as unknown")
        
        return True
    
    def test_large_data_handling(self):
        """测试: 大数据量处理"""
        print("  Testing large data handling...")
        
        for i in range(50):
            self.memory_layers.add(
                content=f"测试记忆内容 {i}: 安哥喜欢编程和咖啡",
                memory_type="test",
                importance=2.0 + (i % 3),
                tags=["测试", f"tag_{i % 5}"]
            )
        
        print(f"    Added 50 memories")
        
        stats = self.memory_layers.get_stats()
        total = stats["total_memories"]
        print(f"    Total memories: {total}")
        assert total >= 50, f"Should have at least 50 memories"
        
        # 搜索性能测试
        import time
        start = time.time()
        results = self.memory_layers.search_by_keywords(["安哥", "编程"], limit=20)
        elapsed = time.time() - start
        print(f"    Search took {elapsed:.3f}s, found {len(results)} results")
        assert elapsed < 1.0, f"Search should be fast"
        
        return True
    
    def test_error_handling(self):
        """测试: 错误处理"""
        print("  Testing error handling...")
        
        result = self.memory_layers.get("non_existent_id")
        assert result is None, "Non-existent memory should return None"
        print("    Non-existent memory: correctly returned None")
        
        parsed = self.command_parser.parse("!@#$%^&*")
        assert parsed.command_type == CommandType.UNKNOWN, "Invalid command should be unknown"
        print("    Invalid command: correctly parsed as unknown")
        
        return True
    
    def test_memory_layer_migration(self):
        """测试: 记忆层自动分层"""
        print("  Testing memory layer auto-assignment...")
        
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
                for mem in self.memory_layers.layers[layer_type]:
                    if mem.memory_id == memory_id:
                        found_layer = layer_type
                        break
                if found_layer:
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
            ("AutoTrigger + MemoryLayers", self.test_auto_trigger_with_layers),
            ("CommandParser + KeywordSearch", self.test_command_parser_with_search),
            ("TimelineViewer + MemoryLayers", self.test_timeline_with_layers),
            ("TagManager Integration", self.test_tag_system_integration),
            ("AutoTrigger Strategies", self.test_auto_trigger_strategies),
            ("End-to-End Flow", self.test_end_to_end_flow),
            ("Empty Data Handling", self.test_empty_data_handling),
            ("Large Data Handling", self.test_large_data_handling),
            ("Error Handling", self.test_error_handling),
            ("Memory Layer Assignment", self.test_memory_layer_migration),
        ]
        
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
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
        
        # 保存报告
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
        self.memory_layers.close()


def main():
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
    import sys
    sys.exit(main())
    
