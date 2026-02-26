#!/usr/bin/env python
"""
MemOS ↔ 记忆3.0 集成桥梁

功能：
1. 将记忆3.0的数据同步到MemOS格式
2. 让MemOS Skill能读取记忆3.0的数据
3. 统一两个系统的接口
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# 路径配置
MEMOS_BASE = Path("D:/wordir/.xiaoyue_memory")
MEMORY3_BASE = Path("D:/wordir/memory_system_v3")
MEMORY3_DATA = MEMORY3_BASE / "data" / "auto_memory"


class MemosBridge:
    """
    MemOS与记忆3.0的集成桥梁
    """
    
    def __init__(self, user_id="simon"):
        self.user_id = user_id
        self.memos_user_dir = MEMOS_BASE / "users" / user_id
        self.memory3_data_dir = MEMORY3_DATA
        
        # 确保目录存在
        self.memos_user_dir.mkdir(parents=True, exist_ok=True)
    
    def sync_from_memory3(self) -> dict:
        """
        从记忆3.0同步数据到MemOS
        
        Returns:
            同步统计
        """
        stats = {
            'memories_synced': 0,
            'preferences_added': [],
            'facts_added': []
        }
        
        try:
            # 加载记忆3.0的数据
            sys.path.insert(0, str(MEMORY3_BASE / "src"))
            from auto_memory_bridge import recall
            
            # 检索所有关于安哥的记忆
            results = recall("安哥", top_k=20)
            
            # 更新MemOS用户档案
            profile_path = self.memos_user_dir / "profile.md"
            
            if profile_path.exists():
                content = profile_path.read_text(encoding='utf-8')
                
                # 提取偏好和事实
                for mem in results:
                    mem_content = mem.get('content', '')
                    mem_type = mem.get('type', 'context')
                    
                    if mem_type == 'preference' and '喜好' not in content:
                        # 添加偏好到档案
                        stats['preferences_added'].append(mem_content)
                        
                    elif mem_type == 'fact' and '生日' in mem_content:
                        # 添加事实到档案
                        stats['facts_added'].append(mem_content)
                
                stats['memories_synced'] = len(results)
            
        except Exception as e:
            print(f"同步失败: {e}")
        
        return stats
    
    def get_combined_memories(self, query: str, top_k: int = 5) -> list:
        """
        获取组合记忆（MemOS + 记忆3.0）
        
        Args:
            query: 查询关键词
            top_k: 返回数量
            
        Returns:
            记忆列表
        """
        memories = []
        
        # 1. 从MemOS获取（档案信息）
        profile_path = self.memos_user_dir / "profile.md"
        if profile_path.exists():
            content = profile_path.read_text(encoding='utf-8')
            # 简单关键词匹配
            if query.lower() in content.lower():
                memories.append({
                    'source': 'MemOS',
                    'type': 'profile',
                    'content': f'档案中包含: {query}'
                })
        
        # 2. 从记忆3.0获取（实时记忆）
        try:
            sys.path.insert(0, str(MEMORY3_BASE / "src"))
            from auto_memory_bridge import recall
            results = recall(query, top_k=top_k)
            
            for mem in results:
                memories.append({
                    'source': 'Memory3.0',
                    'type': mem.get('type', 'context'),
                    'content': mem.get('content', '')
                })
        except Exception as e:
            pass
        
        return memories[:top_k]
    
    def auto_load(self) -> dict:
        """
        自动加载记忆（供MemOS Skill调用）
        
        Returns:
            加载的记忆数据
        """
        result = {
            'user_profile': {},
            'recent_memories': [],
            'memory3_ready': False
        }
        
        # 1. 加载MemOS档案
        profile_path = self.memos_user_dir / "profile.md"
        if profile_path.exists():
            result['user_profile']['exists'] = True
            result['user_profile']['path'] = str(profile_path)
        
        # 2. 尝试加载记忆3.0
        try:
            sys.path.insert(0, str(MEMORY3_BASE / "src"))
            from memory_initializer import load_memory
            
            memory_result = load_memory()
            result['memory3_ready'] = memory_result.get('ready', False)
            
            if result['memory3_ready']:
                # 获取最近记忆
                from auto_memory_bridge import recent
                result['recent_memories'] = recent(5)
        except Exception as e:
            result['memory3_error'] = str(e)
        
        return result


# 便捷函数
def auto_load_memory(user_id="simon") -> dict:
    """
    自动加载记忆 - 主入口
    
    供MemOS Skill在对话开始时调用
    """
    bridge = MemosBridge(user_id)
    return bridge.auto_load()


def sync_memory_systems() -> dict:
    """
    同步两个记忆系统
    """
    bridge = MemosBridge()
    return bridge.sync_from_memory3()


if __name__ == "__main__":
    # 测试
    print("🧠 MemOS ↔ 记忆3.0 集成桥梁测试")
    print("=" * 60)
    
    # 测试自动加载
    print("\n【测试】自动加载记忆")
    result = auto_load_memory()
    
    print(f"MemOS档案: {'✅' if result['user_profile'].get('exists') else '❌'}")
    print(f"记忆3.0就绪: {'✅' if result['memory3_ready'] else '❌'}")
    print(f"最近记忆: {len(result['recent_memories'])} 条")
    
    if result['recent_memories']:
        print("\n最新记忆:")
        for mem in result['recent_memories'][:3]:
            print(f"  - {mem.get('content', '')[:40]}...")
