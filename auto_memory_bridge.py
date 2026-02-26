#!/usr/bin/env python
"""
安仔 ↔ 记忆系统 桥梁
自动根据对话保存和检索记忆
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.memory_unit import MemoryUnit
from storage.json_storage import JsonStorage
from retrieval.keyword_search import KeywordSearch


class AutoMemoryBridge:
    """
    自动记忆桥梁
    
    功能：
    1. 自动保存对话中的重要信息
    2. 根据上下文自动检索相关记忆
    3. 提供记忆管理接口
    """
    
    def __init__(self, data_dir=None):
        """初始化"""
        # 使用绝对路径，确保无论从哪调用都能正确找到数据
        if data_dir is None:
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(script_dir, 'data', 'auto_memory')
        
        self.storage = JsonStorage(data_dir)
        self.keyword_search = KeywordSearch()
        
        # 加载已有记忆到关键词索引
        self._load_existing_memories()
    
    def _load_existing_memories(self):
        """加载已有记忆到索引"""
        memories = self.storage.query(limit=1000)
        for m in memories:
            self.keyword_search.add_document(
                m.memory_id, 
                m.content,
                memory_type=m.memory_type,
                metadata={'importance': m.importance}
            )
    
    def save(self, content, memory_type='context', importance=3.0, tags=None):
        """
        保存记忆
        
        Args:
            content: 记忆内容
            memory_type: 类型 (fact/preference/context/task/event)
            importance: 重要性 (1.0-5.0)
            tags: 标签列表
        """
        try:
            memory = MemoryUnit(
                content=content,
                memory_type=memory_type,
                importance=importance,
                tags=tags or []
            )
            memory_id = self.storage.save(memory)
            
            # 添加到关键词索引
            self.keyword_search.add_document(
                memory_id,
                content,
                memory_type=memory_type,
                metadata={'importance': importance}
            )
            
            return memory_id
        except Exception as e:
            print(f"❌ 保存记忆失败: {e}")
            return None
    
    def recall(self, query, top_k=5):
        """
        检索记忆
        
        Args:
            query: 查询关键词
            top_k: 返回数量
            
        Returns:
            记忆内容列表
        """
        try:
            # 关键词搜索
            results = self.keyword_search.search(query, top_k=top_k)
            
            # 获取完整记忆内容
            memories = []
            for r in results:
                memory_id = r.memory_id if hasattr(r, 'memory_id') else r.get('memory_id')
                if memory_id:
                    memory = self.storage.load(memory_id)
                    if memory:
                        memories.append({
                            'id': memory_id[:8],
                            'content': memory.content,
                            'type': memory.memory_type,
                            'importance': memory.importance,
                            'score': r.score if hasattr(r, 'score') else r.get('score', 0)
                        })
            
            return memories
        except Exception as e:
            print(f"❌ 检索记忆失败: {e}")
            return []
    
    def get_recent(self, limit=10):
        """获取最近记忆"""
        try:
            memories = self.storage.query(limit=limit)
            return [
                {
                    'id': m.memory_id[:8],
                    'content': m.content[:50],
                    'type': m.memory_type,
                    'created': m.created_at
                }
                for m in memories
            ]
        except Exception as e:
            return []
    
    def stats(self):
        """获取统计"""
        try:
            memories = self.storage.query(limit=1000)
            return {
                'total': len(memories),
                'by_type': {}
            }
        except:
            return {'total': 0}


# 全局实例（供导入使用）
_bridge = None

def get_bridge():
    """获取桥梁实例（单例）"""
    global _bridge
    if _bridge is None:
        _bridge = AutoMemoryBridge()
    return _bridge


def remember(content, memory_type='context', importance=3.0, tags=None):
    """便捷函数：保存记忆"""
    return get_bridge().save(content, memory_type, importance, tags)


def recall(query, top_k=5):
    """便捷函数：检索记忆"""
    return get_bridge().recall(query, top_k)


def recent(limit=10):
    """便捷函数：最近记忆"""
    return get_bridge().get_recent(limit)


if __name__ == "__main__":
    # 测试
    print("🧪 自动记忆桥梁测试")
    
    # 保存测试
    id1 = remember("安哥喜欢喝美式咖啡", "preference", 4.0, ["咖啡"])
    print(f"✅ 保存: {id1}")
    
    # 检索测试
    results = recall("咖啡")
    print(f"✅ 检索: {len(results)} 条")
    
    print("🎉 测试完成")
