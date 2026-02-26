"""
自动记忆管理器

集成 AutoTrigger 到对话流程，实现全自动记忆保存。
傻瓜层核心组件 - 用户无需手动操作。
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ux.auto_trigger import AutoTrigger, TriggerDecision


class AutoMemoryManager:
    """
    自动记忆管理器
    
    集成 AutoTrigger，实现对话内容的自动分析和保存。
    用户无需手动触发，系统自动判断何时保存记忆。
    
    Attributes:
        trigger: AutoTrigger 实例
        memory_buffer: 记忆缓冲区
        saved_memories: 已保存的记忆列表
    """
    
    def __init__(
        self,
        min_confidence: float = 0.6,
        buffer_size: int = 5
    ):
        """
        初始化自动记忆管理器
        
        Args:
            min_confidence: 最小置信度阈值
            buffer_size: 缓冲区大小
        """
        self.trigger = AutoTrigger(min_confidence=min_confidence)
        self.buffer_size = buffer_size
        self.memory_buffer: List[Dict[str, Any]] = []
        self.saved_memories: List[Dict[str, Any]] = []
        self.session_start = datetime.now()
        
        print(f"[AutoMemoryManager] 初始化完成")
        print(f"  - 最小置信度: {min_confidence}")
        print(f"  - 缓冲区大小: {buffer_size}")
    
    def process_message(
        self,
        role: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        处理单条消息
        
        Args:
            role: 角色 (user/assistant)
            content: 消息内容
            context: 上下文信息
            
        Returns:
            Dict: 处理结果，包含是否保存、决策详情等
        """
        # 构建消息记录
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        # 添加到缓冲区
        self.memory_buffer.append(message)
        
        # 保持缓冲区大小
        if len(self.memory_buffer) > self.buffer_size:
            self.memory_buffer.pop(0)
        
        # 只分析用户消息
        result = {
            "message": message,
            "saved": False,
            "decision": None
        }
        
        if role == "user":
            # 使用 AutoTrigger 分析
            decision = self.trigger.should_save(content, context)
            result["decision"] = decision
            
            if decision.should_save:
                # 保存记忆
                memory = self._save_memory(content, decision)
                result["saved"] = True
                result["memory"] = memory
                print(f"\n[自动保存] {decision.reason} (置信度: {decision.confidence})")
        
        return result
    
    def _save_memory(
        self,
        content: str,
        decision: TriggerDecision
    ) -> Dict[str, Any]:
        """
        保存记忆
        
        Args:
            content: 内容
            decision: 触发决策
            
        Returns:
            Dict: 保存的记忆
        """
        memory = {
            "id": len(self.saved_memories) + 1,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "confidence": decision.confidence,
            "reason": decision.reason,
            "strategy": decision.strategy
        }
        
        self.saved_memories.append(memory)
        return memory
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要"""
        return {
            "session_start": self.session_start.isoformat(),
            "session_end": datetime.now().isoformat(),
            "total_messages": len(self.memory_buffer),
            "saved_memories": len(self.saved_memories),
            "memories": self.saved_memories
        }
    
    def reset(self):
        """重置会话"""
        self.trigger.reset_session()
        self.memory_buffer.clear()
        self.saved_memories.clear()
        self.session_start = datetime.now()
        print("[AutoMemoryManager] 已重置")


def test_auto_memory():
    """测试自动记忆功能"""
    print("=" * 60)
    print("AutoMemoryManager 集成测试")
    print("=" * 60)
    
    # 创建管理器
    manager = AutoMemoryManager(min_confidence=0.5)
    
    # 模拟对话
    conversation = [
        ("user", "你好"),
        ("assistant", "你好！有什么我可以帮助你的吗？"),
        ("user", "安哥喜欢喝咖啡，每天早上必须一杯美式咖啡"),
        ("assistant", "记住了，你喜欢喝咖啡"),
        ("user", "今天天气不错"),
        ("assistant", "是的，适合出去走走"),
        ("user", "记住，我下周要参加一个重要会议，需要准备PPT"),
        ("assistant", "好的，我会记住你下周要准备会议PPT"),
        ("user", "谢谢"),
        ("assistant", "不客气！"),
    ]
    
    print("\n开始模拟对话...\n")
    
    for i, (role, content) in enumerate(conversation, 1):
        print(f"[{i}] {role}: {content}")
        
        result = manager.process_message(role, content)
        
        if result.get("saved"):
            print(f"    -> 自动保存记忆 #{result['memory']['id']}")
    
    # 输出会话摘要
    print("\n" + "=" * 60)
    print("会话摘要")
    print("=" * 60)
    summary = manager.get_session_summary()
    print(f"总消息数: {summary['total_messages']}")
    print(f"自动保存记忆数: {summary['saved_memories']}")
    
    if summary['saved_memories'] > 0:
        print("\n已保存的记忆:")
        for memory in summary['memories']:
            print(f"  #{memory['id']}: {memory['content'][:40]}...")
            print(f"      原因: {memory['reason']}, 置信度: {memory['confidence']}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    return summary['saved_memories'] > 0


if __name__ == "__main__":
    success = test_auto_memory()
    sys.exit(0 if success else 1)
