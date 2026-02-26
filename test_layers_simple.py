"""
四层记忆架构简化测试
验证核心功能正常工作
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any


class MemoryLayerType(Enum):
    """记忆层类型枚举"""
    WORKING = "working"       # 工作记忆：当前活跃上下文
    SHORT_TERM = "short"      # 短期记忆：最近7天
    LONG_TERM = "long"        # 长期记忆：重要信息
    PERMANENT = "permanent"   # 永久记忆：核心知识


@dataclass
class SimpleMemoryUnit:
    """简化记忆单元"""
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
class LayerConfig:
    """记忆层配置"""
    name: str
    description: str
    max_age_days: Optional[int] = None
    min_access_frequency: float = 0.0
    min_importance: float = 1.0
    max_capacity: Optional[int] = None


# 默认配置
DEFAULT_CONFIGS = {
    MemoryLayerType.WORKING: LayerConfig(
        name="工作记忆",
        description="当前活跃上下文",
        max_age_days=1,
        min_importance=1.0
    ),
    MemoryLayerType.SHORT_TERM: LayerConfig(
        name="短期记忆",
        description="最近7天的记忆",
        max_age_days=7,
        min_access_frequency=0.1
    ),
    MemoryLayerType.LONG_TERM: LayerConfig(
        name="长期记忆",
        description="重要信息",
        max_age_days=30,
        min_access_frequency=0.05,
        min_importance=3.0
    ),
    MemoryLayerType.PERMANENT: LayerConfig(
        name="永久记忆",
        description="核心知识",
        max_age_days=None,
        min_access_frequency=0.01,
        min_importance=4.5
    ),
}


class MemoryLayer:
    """记忆层"""
    
    def __init__(self, layer_type: MemoryLayerType, data_dir: str):
        self.layer_type = layer_type
        self.config = DEFAULT_CONFIGS[layer_type]
        self.data_dir = Path(data_dir) / "layers" / layer_type.value
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._memories: Dict[str, SimpleMemoryUnit] = {}
        self._load_all()
    
    def _get_file_path(self, memory_id: str) -> Path:
        return self.data_dir / f"{memory_id}.json"
    
    def _load_all(self):
        """加载所有记忆"""
        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    memory = SimpleMemoryUnit(**data)
                    self._memories[memory.memory_id] = memory
            except Exception as e:
                print(f"Load failed {file_path}: {e}")
    
    def add(self, memory: SimpleMemoryUnit) -> str:
        """添加记忆"""
        file_path = self._get_file_path(memory.memory_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(memory), f, ensure_ascii=False, indent=2)
        self._memories[memory.memory_id] = memory
        return memory.memory_id
    
    def get(self, memory_id: str) -> Optional[SimpleMemoryUnit]:
        """获取记忆"""
        if memory_id in self._memories:
            return self._memories[memory_id]
        return None
    
    def get_all(self) -> List[SimpleMemoryUnit]:
        """获取所有记忆"""
        return list(self._memories.values())
    
    def count(self) -> int:
        """获取数量"""
        return len(self._memories)
    
    def remove(self, memory_id: str) -> bool:
        """删除记忆"""
        file_path = self._get_file_path(memory_id)
        try:
            if file_path.exists():
                file_path.unlink()
            self._memories.pop(memory_id, None)
            return True
        except Exception:
            return False


class MemoryLayerManager:
    """四层记忆管理器"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.layers: Dict[MemoryLayerType, MemoryLayer] = {}
        for layer_type in MemoryLayerType:
            self.layers[layer_type] = MemoryLayer(layer_type, str(self.data_dir))
        
        self.stats = {"total_added": 0, "total_accessed": 0}
    
    def _determine_layer(self, memory: SimpleMemoryUnit) -> MemoryLayerType:
        """根据重要性确定层"""
        if memory.importance >= 4.5:
            return MemoryLayerType.PERMANENT
        elif memory.importance >= 3.0:
            return MemoryLayerType.LONG_TERM
        else:
            return MemoryLayerType.SHORT_TERM
    
    def add(self, content: str, memory_type: str, importance: float = 3.0, 
            tags: Optional[List[str]] = None) -> str:
        """添加记忆"""
        memory = SimpleMemoryUnit(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or []
        )
        layer_type = self._determine_layer(memory)
        memory_id = self.layers[layer_type].add(memory)
        self.stats["total_added"] += 1
        return memory_id
    
    def get(self, memory_id: str) -> Optional[SimpleMemoryUnit]:
        """跨层获取"""
        for layer_type in MemoryLayerType:
            memory = self.layers[layer_type].get(memory_id)
            if memory:
                memory.update_access()
                self.stats["total_accessed"] += 1
                return memory
        return None
    
    def query(self, memory_type: Optional[str] = None, 
              min_importance: Optional[float] = None) -> List[SimpleMemoryUnit]:
        """查询记忆"""
        results = []
        for layer in self.layers.values():
            for memory in layer.get_all():
                if memory_type and memory.memory_type != memory_type:
                    continue
                if min_importance and memory.importance < min_importance:
                    continue
                results.append(memory)
        results.sort(key=lambda m: m.importance, reverse=True)
        return results
    
    def search_by_keywords(self, keywords: List[str]) -> List[SimpleMemoryUnit]:
        """关键词搜索"""
        results = []
        for layer in self.layers.values():
            for memory in layer.get_all():
                content_lower = memory.content.lower()
                if any(kw.lower() in content_lower for kw in keywords):
                    results.append(memory)
        return results
    
    def get_timeline(self, days: int = 7) -> List[Dict]:
        """时间线"""
        cutoff = datetime.now() - timedelta(days=days)
        timeline = []
        
        for layer_type, layer in self.layers.items():
            for memory in layer.get_all():
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
        """获取统计"""
        layer_stats = {}
        for layer_type, layer in self.layers.items():
            layer_stats[layer_type.value] = {
                "count": layer.count(),
                "config": {
                    "max_age_days": layer.config.max_age_days,
                    "min_importance": layer.config.min_importance
                }
            }
        
        total = sum(layer.count() for layer in self.layers.values())
        
        return {
            "layers": layer_stats,
            "operations": self.stats.copy(),
            "total_memories": total
        }
    
    def close(self):
        """关闭"""
        pass


def test_all():
    """运行所有测试"""
    print("=" * 60)
    print("Four-Layer Memory Architecture Test")
    print("=" * 60)
    
    tmpdir = tempfile.mkdtemp()
    print(f"\nTemp dir: {tmpdir}")
    
    try:
        # Test 1: Create manager
        print("\n[Test 1] Create four-layer memory manager")
        manager = MemoryLayerManager(data_dir=tmpdir)
        for layer_type in MemoryLayerType:
            assert layer_type in manager.layers
            print(f"  [OK] {layer_type.value} layer created")
        
        # Test 2: Add memories with different importance
        print("\n[Test 2] Auto layer assignment")
        perm_id = manager.add("Ange is Simon", "fact", 5.0, ["identity"])
        long_id = manager.add("Ange likes coffee", "preference", 4.0, ["coffee"])
        short_id = manager.add("Weather is good today", "context", 2.0, ["weather"])
        print(f"  [OK] Permanent memory: {perm_id[:30]}...")
        print(f"  [OK] Long-term memory: {long_id[:30]}...")
        print(f"  [OK] Short-term memory: {short_id[:30]}...")
        
        # Test 3: Verify layer assignment
        print("\n[Test 3] Verify layer assignment")
        stats = manager.get_stats()
        for layer_name, layer_stat in stats["layers"].items():
            print(f"  [OK] {layer_name}: {layer_stat['count']} items")
        
        assert stats["layers"]["permanent"]["count"] >= 1
        assert stats["layers"]["long"]["count"] >= 1
        assert stats["layers"]["short"]["count"] >= 1
        
        # Test 4: Cross-layer retrieval
        print("\n[Test 4] Cross-layer retrieval")
        memory = manager.get(perm_id)
        assert memory is not None
        assert memory.content == "Ange is Simon"
        print(f"  [OK] Retrieved: {memory.content}")
        print(f"  [OK] Access count: {memory.access_count}")
        
        # Test 5: Keyword search
        print("\n[Test 5] Keyword search")
        results = manager.search_by_keywords(["Ange"])
        print(f"  [OK] Found {len(results)} memories with 'Ange'")
        for r in results:
            print(f"    - {r.content}")
        
        # Test 6: Query by type
        print("\n[Test 6] Query by type")
        results = manager.query(memory_type="preference")
        print(f"  [OK] Found {len(results)} preference memories")
        
        # Test 7: Timeline
        print("\n[Test 7] Timeline view")
        timeline = manager.get_timeline(days=7)
        print(f"  [OK] Last 7 days: {len(timeline)} records")
        for item in timeline[:3]:
            print(f"    - [{item['layer']}] {item['content'][:30]}...")
        
        # Test 8: Statistics
        print("\n[Test 8] Statistics")
        final_stats = manager.get_stats()
        print(f"  [OK] Total memories: {final_stats['total_memories']}")
        print(f"  [OK] Add operations: {final_stats['operations']['total_added']}")
        print(f"  [OK] Access operations: {final_stats['operations']['total_accessed']}")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        manager.close()
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    success = test_all()
    exit(0 if success else 1)
