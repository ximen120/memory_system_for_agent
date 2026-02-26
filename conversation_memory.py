#!/usr/bin/env python
"""
会话级自动记忆管理器

功能：
1. 新会话自动启动记忆系统
2. 实时分析对话内容
3. 自动保存重要信息
4. 上下文感知检索
"""

import sys
sys.path.insert(0, 'src')

from ux.auto_trigger import AutoTrigger, TriggerDecision
from auto_memory_bridge import remember, recall, recent
from datetime import datetime


class ConversationMemory:
    """
    会话记忆管理器
    
    每个会话自动初始化，实时处理对话
    """
    
    def __init__(self):
        """初始化会话记忆"""
        self.trigger = AutoTrigger()
        self.session_start = datetime.now()
        self.message_count = 0
        self.saved_count = 0
        
        print(f"🧠 记忆系统已启动 | 会话时间: {self.session_start.strftime('%H:%M:%S')}")
    
    def process_message(self, speaker: str, content: str) -> dict:
        """
        处理单条消息
        
        Args:
            speaker: 说话者 ('安哥' 或 '安仔')
            content: 消息内容
            
        Returns:
            处理结果
        """
        self.message_count += 1
        
        result = {
            'speaker': speaker,
            'content': content,
            'saved': False,
            'memory_id': None,
            'trigger_info': None
        }
        
        # 只处理安哥说的话（安仔的回复不需要保存）
        if speaker == '安哥':
            # 使用自动触发器分析
            decision = self.trigger.should_save(content)
            
            result['trigger_info'] = {
                'should_save': decision.should_save,
                'confidence': decision.confidence,
                'reason': decision.reason,
                'strategy': decision.strategy
            }
            
            # 如果触发保存
            if decision.should_save:
                memory_id = self._save_memory(content, decision)
                result['saved'] = True
                result['memory_id'] = memory_id
                self.saved_count += 1
        
        return result
    
    def _save_memory(self, content: str, decision: TriggerDecision) -> str:
        """保存记忆"""
        # 根据策略确定记忆类型
        memory_type = self._determine_type(content, decision.strategy)
        
        # 根据置信度确定重要性
        importance = min(5.0, max(3.0, decision.confidence * 5))
        
        # 提取标签
        tags = self._extract_tags(content)
        
        # 保存
        memory_id = remember(content, memory_type, importance, tags)
        
        return memory_id
    
    def _determine_type(self, content: str, strategy: str) -> str:
        """确定记忆类型"""
        if 'preference' in strategy or any(kw in content for kw in ['喜欢', '讨厌', '爱好']):
            return 'preference'
        elif 'fact' in strategy or any(kw in content for kw in ['是', '叫', '生日']):
            return 'fact'
        elif 'event' in strategy or any(kw in content for kw in ['今天', '完成', '做了']):
            return 'event'
        elif 'task' in strategy or any(kw in content for kw in ['计划', '目标', '要']):
            return 'task'
        else:
            return 'context'
    
    def _extract_tags(self, content: str) -> list:
        """提取标签"""
        tags = []
        
        # 常见标签关键词
        tag_keywords = {
            '工作': ['工作', '项目', '任务', '会议'],
            '生活': ['生活', '日常', '家里', '家人'],
            '学习': ['学习', '读书', '课程', '技能'],
            '健康': ['健康', '运动', '饮食', '睡眠'],
            '兴趣': ['兴趣', '爱好', '喜欢', '娱乐'],
            '重要': ['重要', '关键', '必须', '核心']
        }
        
        for tag, keywords in tag_keywords.items():
            if any(kw in content for kw in keywords):
                tags.append(tag)
        
        return tags[:3]  # 最多3个标签
    
    def get_relevant_memories(self, query: str, top_k: int = 3) -> list:
        """获取相关记忆"""
        return recall(query, top_k)
    
    def get_session_stats(self) -> dict:
        """获取会话统计"""
        return {
            'session_start': self.session_start.strftime('%Y-%m-%d %H:%M:%S'),
            'message_count': self.message_count,
            'saved_count': self.saved_count,
            'recent_memories': recent(5)
        }
    
    def close(self):
        """关闭会话"""
        duration = (datetime.now() - self.session_start).total_seconds()
        print(f"\n👋 会话结束 | 时长: {duration:.0f}秒 | 保存: {self.saved_count}条记忆")


# 全局会话实例
_session = None

def start_session():
    """启动新会话"""
    global _session
    _session = ConversationMemory()
    return _session

def get_session():
    """获取当前会话"""
    global _session
    if _session is None:
        _session = start_session()
    return _session

def process(speaker: str, content: str) -> dict:
    """便捷函数：处理消息"""
    return get_session().process_message(speaker, content)

def relevant(query: str, top_k: int = 3) -> list:
    """便捷函数：获取相关记忆"""
    return get_session().get_relevant_memories(query, top_k)

def stats():
    """便捷函数：获取统计"""
    return get_session().get_session_stats()


# 演示
if __name__ == "__main__":
    print("=" * 60)
    print("🧠 会话级自动记忆管理器 - 演示")
    print("=" * 60)
    print()
    
    # 启动会话
    session = start_session()
    
    # 模拟对话
    conversations = [
        ("安哥", "你好安仔，今天天气不错"),
        ("安仔", "是的，适合出去走走"),
        ("安哥", "我喜欢喝美式咖啡，不加糖"),
        ("安仔", "记住了，你喜欢美式咖啡"),
        ("安哥", "我的生日是12月25日"),
        ("安仔", "好的，圣诞节生日，记住了"),
        ("安哥", "今天完成了记忆系统的开发"),
    ]
    
    for speaker, content in conversations:
        print(f"\n{speaker}: {content}")
        
        result = session.process_message(speaker, content)
        
        if result.get('saved'):
            info = result['trigger_info']
            print(f"  💾 [自动保存] 置信度: {info['confidence']:.2f} | 原因: {info['reason']}")
    
    # 显示统计
    print("\n" + "=" * 60)
    print("📊 会话统计:")
    stats = session.get_session_stats()
    print(f"  消息数: {stats['message_count']}")
    print(f"  保存数: {stats['saved_count']}")
    print(f"  最近记忆:")
    for m in stats['recent_memories'][:3]:
        print(f"    - {m['content'][:40]}...")
    
    session.close()
