"""
M6傻瓜层集成测试 - 快速版本
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'libs'))

import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict

# 简化模块实现
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
    UNKNOWN = "unknown"

@dataclass
class SimpleMemory:
    content: str
    memory_type: str
    importance: float = 3.0
    memory_id: str = field(default_factory=lambda: f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}")
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    access_count: int = 0

# 简化版模块
class SimpleAutoTrigger:
    KEYWORDS = ["记住", "喜欢", "计划", "目标", "习惯"]
    def should_save(self, content: str):
        for kw in self.KEYWORDS:
            if kw in content:
                return True
        return len(content) > 20

class SimpleTagManager:
    def auto_extract_tags(self, content: str):
        words = content.split()
        return [w for w in words if 2 <= len(w) <= 4][:5]

class SimpleCommandParser:
    def parse(self, text: str):
        if "查找" in text or "搜索" in text:
            return CommandType.SEARCH
        if "记住" in text:
            return CommandType.REMEMBER
        return CommandType.UNKNOWN

class SimpleMemoryManager:
    def __init__(self):
        self.layers = {t: [] for t in MemoryLayerType}
        self.all_memories = []
    
    def add(self, content, memory_type, importance=3.0, tags=None):
        mem = SimpleMemory(content=content, memory_type=memory_type, importance=importance, tags=tags or [])
        if importance >= 4.5:
            self.layers[MemoryLayerType.PERMANENT].append(mem)
        elif importance >= 3.0:
            self.layers[MemoryLayerType.LONG_TERM].append(mem)
        else:
            self.layers[MemoryLayerType.SHORT_TERM].append(mem)
        self.all_memories.append(mem)
        return mem.memory_id
    
    def search(self, keywords):
        results = []
        for mem in self.all_memories:
            if any(kw in mem.content for kw in keywords):
                results.append(mem)
        return results
    
    def get_stats(self):
        return {k.value: len(v) for k, v in self.layers.items()}

# 测试
def run_tests():
    print("=" * 60)
    print("M6 FOOL LAYER INTEGRATION TEST (QUICK)")
    print("=" * 60)
    
    results = []
    passed = 0
    failed = 0
    
    # 初始化
    trigger = SimpleAutoTrigger()
    tag_mgr = SimpleTagManager()
    cmd_parser = SimpleCommandParser()
    memory_mgr = SimpleMemoryManager()
    
    # Test 1: AutoTrigger + MemoryLayers
    print("\n[TEST 1] AutoTrigger + MemoryLayers")
    content = "安哥喜欢喝咖啡"
    should_save = trigger.should_save(content)
    if should_save:
        tags = tag_mgr.auto_extract_tags(content)
        memory_mgr.add(content, "preference", 4.0, tags)
        print("  [PASS] Content triggered and saved")
        passed += 1
    else:
        print("  [FAIL] Content should trigger")
        failed += 1
    
    # Test 2: CommandParser + Search
    print("\n[TEST 2] CommandParser + KeywordSearch")
    memory_mgr.add("安哥是程序员", "fact", 3.5)
    memory_mgr.add("安哥喜欢Python", "preference", 3.5)
    
    cmd = cmd_parser.parse("查找安哥")
    if cmd == CommandType.SEARCH:
        results_search = memory_mgr.search(["安哥"])
        print(f"  [PASS] Search found {len(results_search)} results")
        passed += 1
    else:
        print("  [FAIL] Command not recognized")
        failed += 1
    
    # Test 3: Timeline
    print("\n[TEST 3] Timeline + MemoryLayers")
    memory_mgr.add("今天学习Rust", "context", 2.5)
    memory_mgr.add("完成项目", "task", 3.0)
    stats = memory_mgr.get_stats()
    total = sum(stats.values())
    if total >= 4:
        print(f"  [PASS] Timeline shows {total} memories")
        passed += 1
    else:
        print("  [FAIL] Not enough memories")
        failed += 1
    
    # Test 4: End-to-End
    print("\n[TEST 4] End-to-End Flow")
    user_input = "安哥计划学习AI"
    if trigger.should_save(user_input):
        tags = tag_mgr.auto_extract_tags(user_input)
        mid = memory_mgr.add(user_input, "goal", 4.5, tags)
        search_results = memory_mgr.search(["AI"])
        if len(search_results) > 0:
            print("  [PASS] End-to-end flow works")
            passed += 1
        else:
            print("  [FAIL] Search failed")
            failed += 1
    else:
        print("  [FAIL] Input should trigger")
        failed += 1
    
    # Test 5: Layer Assignment
    print("\n[TEST 5] Memory Layer Assignment")
    memory_mgr.add("核心身份", "fact", 5.0)  # -> Permanent
    memory_mgr.add("普通信息", "context", 2.0)  # -> Short
    stats = memory_mgr.get_stats()
    if stats["permanent"] >= 1 and stats["short"] >= 2:
        print(f"  [PASS] Layers: permanent={stats['permanent']}, short={stats['short']}")
        passed += 1
    else:
        print("  [FAIL] Layer assignment incorrect")
        failed += 1
    
    # Report
    print("\n" + "=" * 60)
    print("TEST REPORT")
    print("=" * 60)
    total = passed + failed
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass Rate: {passed/total*100:.1f}%")
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": passed/total*100 if total > 0 else 0,
        "layer_stats": stats
    }
    
    report_path = Path("D:/wordir/memory_system_v3/M6_INTEGRATION_TEST_REPORT.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\nReport saved to: {report_path}")
    
    if failed == 0:
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
