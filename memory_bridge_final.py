#!/usr/bin/env python
"""
最终版记忆桥梁 - 完全无感知

使用方式：
    from memory_bridge_final import MemoryBridge
    
    bridge = MemoryBridge()  # 自动启动
    
    # 用户说话
    result = bridge.user_input("我喜欢喝美式咖啡")
    # result包含相关记忆，可用于生成回复
    
    # 助手回复
    bridge.assistant_output("记住了，你喜欢美式咖啡")
    
    # 会话结束
    bridge.end()  # 自动生成摘要
"""

import sys
sys.path.insert(0, 'src')

from smart_memory import SmartMemory


class MemoryBridge:
    """
    记忆桥梁 - 完全无感知版本
    
    安哥只需正常对话，所有记忆操作自动完成
    """
    
    def __init__(self, show_summary=True):
        """
        初始化
        
        Args:
            show_summary: 会话结束时是否显示摘要
        """
        self.memory = SmartMemory(silent=True, auto_retrieve=True)
        self.show_summary = show_summary
        self.session_active = True
    
    def user_input(self, content: str) -> dict:
        """
        处理用户输入
        
        Args:
            content: 用户说的话
            
        Returns:
            {
                'content': 原始内容,
                'saved': 是否保存,
                'memories': 相关记忆列表,
                'context': 可用于回复的上下文
            }
        """
        if not self.session_active:
            self.memory = SmartMemory(silent=True, auto_retrieve=True)
            self.session_active = True
        
        result = self.memory.on_user_message(content)
        
        # 整理返回结果
        return {
            'content': content,
            'saved': result.get('saved', False),
            'memories': result.get('relevant_memories', []),
            'suggestions': result.get('suggestions', []),
            'context': self._format_context(result.get('relevant_memories', []))
        }
    
    def assistant_output(self, content: str):
        """记录助手回复"""
        if self.memory:
            self.memory.on_assistant_message(content)
    
    def _format_context(self, memories: list) -> str:
        """格式化记忆为上下文"""
        if not memories:
            return ""
        
        context_parts = []
        for mem in memories[:3]:  # 最多3条
            content = mem.get('content', '')
            mem_type = mem.get('type', 'context')
            
            if mem_type == 'preference':
                context_parts.append(f"用户偏好: {content}")
            elif mem_type == 'fact':
                context_parts.append(f"已知信息: {content}")
            elif mem_type == 'event':
                context_parts.append(f"相关事件: {content}")
            else:
                context_parts.append(f"相关记忆: {content}")
        
        return "\n".join(context_parts)
    
    def get_stats(self) -> dict:
        """获取当前会话统计"""
        if self.memory:
            return self.memory.get_session_stats()
        return {}
    
    def end(self) -> str:
        """
        结束会话
        
        Returns:
            会话摘要（如果show_summary=True）
        """
        if self.memory and self.session_active:
            summary = self.memory.close()
            self.session_active = False
            return summary if self.show_summary else ""
        return ""
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.end()


# 全局实例
_bridge = None

def get_bridge():
    """获取全局桥梁实例"""
    global _bridge
    if _bridge is None:
        _bridge = MemoryBridge()
    return _bridge


def user_says(content: str) -> dict:
    """便捷函数：用户说话"""
    return get_bridge().user_input(content)


def assistant_says(content: str):
    """便捷函数：助手回复"""
    get_bridge().assistant_output(content)


def end_session():
    """便捷函数：结束会话"""
    global _bridge
    if _bridge:
        summary = _bridge.end()
        _bridge = None
        return summary
    return ""


# 演示
if __name__ == "__main__":
    print("🧠 记忆桥梁 - 完全无感知演示")
    print("=" * 60)
    print()
    
    # 创建桥梁（静默模式）
    bridge = MemoryBridge(show_summary=True)
    
    print("【场景】安哥正常对话，记忆系统自动工作...")
    print()
    
    # 对话1
    print("安哥: 我喜欢喝美式咖啡，不加糖")
    result1 = bridge.user_input("我喜欢喝美式咖啡，不加糖")
    print(f"  → 系统: 已自动保存 | 相关记忆: {len(result1['memories'])} 条")
    bridge.assistant_output("好的，记住了")
    
    # 对话2
    print("\n安哥: 我的生日是12月25日")
    result2 = bridge.user_input("我的生日是12月25日")
    print(f"  → 系统: 已自动保存 | 相关记忆: {len(result2['memories'])} 条")
    bridge.assistant_output("记住了，圣诞节生日")
    
    # 对话3 - 提问时自动提供上下文
    print("\n安哥: 对了，我喜欢什么咖啡来着？")
    result3 = bridge.user_input("对了，我喜欢什么咖啡来着？")
    print(f"  → 系统: 找到相关记忆 {len(result3['memories'])} 条")
    if result3['context']:
        print(f"  → 提供给安仔的上下文:\n{result3['context']}")
    bridge.assistant_output("你喜欢美式咖啡，不加糖")
    
    # 结束会话，生成摘要
    print("\n")
    bridge.end()
