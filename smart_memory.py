#!/usr/bin/env python
"""
智能记忆系统 v2.0

三大优化：
1. 静默模式 - 保存无感知
2. 智能检索 - 自动提供上下文
3. 记忆摘要 - 会话结束自动生成
"""

import sys
sys.path.insert(0, 'src')

from ux.auto_trigger import AutoTrigger
from auto_memory_bridge import remember, recall, recent
from datetime import datetime
import re


class SmartMemory:
    """
    智能记忆系统
    
    完全自动化的记忆管理，用户无感知
    """
    
    def __init__(self, silent=True, auto_retrieve=True):
        """
        初始化
        
        Args:
            silent: 是否静默模式（不显示保存提示）
            auto_retrieve: 是否自动检索相关记忆
        """
        self.trigger = AutoTrigger()
        self.silent = silent
        self.auto_retrieve = auto_retrieve
        
        self.session_start = datetime.now()
        self.conversation_history = []
        self.saved_memories = []
        
        if not silent:
            print(f"🧠 智能记忆系统已启动")
    
    def on_user_message(self, content: str) -> dict:
        """
        处理用户消息
        
        Args:
            content: 用户输入内容
            
        Returns:
            包含相关记忆和处理结果的字典
        """
        result = {
            'content': content,
            'saved': False,
            'relevant_memories': [],
            'suggestions': []
        }
        
        # 1. 保存重要信息（静默）
        decision = self.trigger.should_save(content)
        if decision.should_save:
            memory_id = self._save_memory(content, decision)
            result['saved'] = True
            result['memory_id'] = memory_id
            
            if not self.silent:
                print(f"  💾 [已记忆] {content[:30]}...")
        
        # 2. 自动检索相关记忆
        if self.auto_retrieve:
            relevant = self._get_relevant_context(content)
            result['relevant_memories'] = relevant
            
            # 3. 生成建议回复
            if relevant:
                result['suggestions'] = self._generate_suggestions(content, relevant)
        
        # 记录对话历史
        self.conversation_history.append({
            'time': datetime.now(),
            'speaker': 'user',
            'content': content,
            'saved': result['saved']
        })
        
        return result
    
    def on_assistant_message(self, content: str):
        """记录助手回复"""
        self.conversation_history.append({
            'time': datetime.now(),
            'speaker': 'assistant',
            'content': content,
            'saved': False
        })
    
    def _save_memory(self, content: str, decision) -> str:
        """保存记忆"""
        memory_type = self._determine_type(content)
        importance = min(5.0, max(3.0, decision.confidence * 5))
        tags = self._extract_tags(content)
        
        memory_id = remember(content, memory_type, importance, tags)
        
        self.saved_memories.append({
            'id': memory_id,
            'content': content,
            'type': memory_type,
            'time': datetime.now()
        })
        
        return memory_id
    
    def _get_relevant_context(self, query: str, top_k: int = 3) -> list:
        """获取相关上下文"""
        # 提取关键词
        keywords = self._extract_keywords(query)
        
        # 检索相关记忆
        results = []
        for keyword in keywords[:2]:  # 用前2个关键词检索
            memories = recall(keyword, top_k=2)
            results.extend(memories)
        
        # 去重并按相关性排序
        seen = set()
        unique_results = []
        for r in results:
            if r['id'] not in seen:
                seen.add(r['id'])
                unique_results.append(r)
        
        return unique_results[:top_k]
    
    def _generate_suggestions(self, query: str, memories: list) -> list:
        """生成回复建议"""
        suggestions = []
        
        for mem in memories:
            content = mem['content']
            
            # 根据记忆类型生成建议
            if mem['type'] == 'preference':
                if any(kw in query for kw in ['喜欢', '想', '要']):
                    suggestions.append(f"记得你{content}，需要我推荐相关的内容吗？")
            
            elif mem['type'] == 'fact':
                if any(kw in query for kw in ['是', '什么', '谁']):
                    suggestions.append(f"根据之前的记录，{content}")
            
            elif mem['type'] == 'event':
                suggestions.append(f"之前你提到{content}，现在进展如何？")
        
        return suggestions
    
    def _determine_type(self, content: str) -> str:
        """确定记忆类型"""
        if any(kw in content for kw in ['喜欢', '讨厌', '爱好']):
            return 'preference'
        elif any(kw in content for kw in ['是', '叫', '生日', '身份']):
            return 'fact'
        elif any(kw in content for kw in ['今天', '完成', '做了', '发生']):
            return 'event'
        elif any(kw in content for kw in ['计划', '目标', '要', '准备']):
            return 'task'
        return 'context'
    
    def _extract_tags(self, content: str) -> list:
        """提取标签"""
        tags = []
        tag_map = {
            '工作': ['工作', '项目', '任务', '会议', '职业'],
            '生活': ['生活', '日常', '家里', '家人', '朋友'],
            '学习': ['学习', '读书', '课程', '技能', '知识'],
            '健康': ['健康', '运动', '饮食', '睡眠', '身体'],
            '兴趣': ['兴趣', '爱好', '喜欢', '娱乐', '游戏'],
            '重要': ['重要', '关键', '必须', '核心', '记住']
        }
        
        for tag, keywords in tag_map.items():
            if any(kw in content for kw in keywords):
                tags.append(tag)
        
        return tags[:3]
    
    def _extract_keywords(self, content: str) -> list:
        """提取关键词"""
        # 简单关键词提取
        words = re.findall(r'[\u4e00-\u9fa5]{2,}', content)
        
        # 过滤停用词
        stop_words = {'这个', '那个', '什么', '怎么', '今天', '明天'}
        words = [w for w in words if w not in stop_words and len(w) >= 2]
        
        return words[:5]
    
    def generate_summary(self) -> str:
        """生成会话摘要"""
        duration = (datetime.now() - self.session_start).total_seconds()
        
        summary = []
        summary.append("=" * 60)
        summary.append("📋 会话记忆摘要")
        summary.append("=" * 60)
        summary.append(f"\n⏱️  会话时长: {duration/60:.1f} 分钟")
        summary.append(f"💬 对话轮数: {len([m for m in self.conversation_history if m['speaker'] == 'user'])} 轮")
        summary.append(f"🧠 新增记忆: {len(self.saved_memories)} 条")
        
        if self.saved_memories:
            summary.append("\n📝 本次保存的记忆:")
            
            # 按类型分组
            by_type = {}
            for mem in self.saved_memories:
                t = mem['type']
                if t not in by_type:
                    by_type[t] = []
                by_type[t].append(mem)
            
            type_names = {
                'preference': '偏好',
                'fact': '事实',
                'event': '事件',
                'task': '任务',
                'context': '上下文'
            }
            
            for mem_type, memories in by_type.items():
                summary.append(f"\n  [{type_names.get(mem_type, mem_type)}]")
                for mem in memories:
                    summary.append(f"    • {mem['content'][:50]}")
        
        # 关键信息提取
        key_facts = [m for m in self.saved_memories if m['type'] in ['fact', 'preference']]
        if key_facts:
            summary.append("\n🔑 关键信息:")
            for mem in key_facts:
                summary.append(f"  • {mem['content']}")
        
        summary.append("\n" + "=" * 60)
        
        return "\n".join(summary)
    
    def close(self):
        """结束会话，生成摘要"""
        summary = self.generate_summary()
        print(summary)
        return summary


# 便捷函数
_memory = None

def init(silent=True, auto_retrieve=True):
    """初始化智能记忆"""
    global _memory
    _memory = SmartMemory(silent=silent, auto_retrieve=auto_retrieve)
    return _memory

def user_says(content: str) -> dict:
    """用户说话"""
    global _memory
    if _memory is None:
        _memory = init()
    return _memory.on_user_message(content)

def assistant_says(content: str):
    """助手回复"""
    global _memory
    if _memory:
        _memory.on_assistant_message(content)

def end_session() -> str:
    """结束会话"""
    global _memory
    if _memory:
        summary = _memory.close()
        _memory = None
        return summary
    return ""


# 演示
if __name__ == "__main__":
    print("🧠 智能记忆系统 v2.0 - 演示")
    print("=" * 60)
    print()
    
    # 初始化（静默模式 + 自动检索）
    memory = init(silent=False, auto_retrieve=True)
    
    # 模拟对话
    test_messages = [
        "你好安仔",
        "我喜欢喝美式咖啡，不加糖",
        "我的生日是12月25日",
        "今天完成了记忆系统的开发",
        "我计划下周开始学习Python",
        "对了，我喜欢什么咖啡来着？",
    ]
    
    for msg in test_messages:
        print(f"\n安哥: {msg}")
        
        result = memory.on_user_message(msg)
        
        # 显示相关记忆（如果有）
        if result['relevant_memories']:
            print("  🔍 [相关记忆]")
            for mem in result['relevant_memories']:
                print(f"     • {mem['content'][:40]}...")
        
        # 显示建议回复
        if result['suggestions']:
            print("  💡 [建议回复]")
            for sug in result['suggestions'][:1]:
                print(f"     → {sug}")
        
        # 模拟安仔回复
        assistant_reply = f"收到，我记下了"
        memory.on_assistant_message(assistant_reply)
    
    # 生成摘要
    print("\n")
    memory.close()
