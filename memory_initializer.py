#!/usr/bin/env python
"""
记忆初始化器

指令: "加载记忆"
功能: 全自动启动记忆系统并集成到对话

使用方式:
    1. 用户说: "加载记忆"
    2. 系统全自动完成:
       - 启动记忆系统
       - 加载历史记忆
       - 集成到当前对话
       - 返回就绪状态
"""

import sys
sys.path.insert(0, 'src')

from memory_bridge_final import MemoryBridge


class MemoryInitializer:
    """
    记忆初始化器
    
    单例模式，确保全局只有一个记忆系统实例
    """
    
    _instance = None
    _initialized = False
    _bridge = None
    
    @classmethod
    def initialize(cls, show_summary=True) -> dict:
        """
        初始化记忆系统
        
        Returns:
            {
                'success': 是否成功,
                'status': 状态描述,
                'stats': 统计信息,
                'ready': 是否就绪
            }
        """
        result = {
            'success': False,
            'status': '',
            'stats': {},
            'ready': False
        }
        
        try:
            # 1. 检查是否已初始化
            if cls._initialized and cls._bridge is not None:
                result['status'] = '记忆系统已运行'
                result['stats'] = cls._bridge.get_stats()
                result['success'] = True
                result['ready'] = True
                return result
            
            # 2. 创建记忆桥梁
            cls._bridge = MemoryBridge(show_summary=show_summary)
            cls._initialized = True
            cls._instance = cls._bridge
            
            # 3. 加载历史记忆
            from auto_memory_bridge import recent, get_bridge
            recent_memories = recent(10)
            total_memories = get_bridge().stats()['total']
            
            # 3.5 自动加载核心记忆上下文
            try:
                sys.path.insert(0, 'src')
                from core.core_memory_manager import CoreMemoryManager
                core_manager = CoreMemoryManager()
                core_memories = core_manager.get_recent_memories(limit=5, tier="core")
                if core_memories:
                    print()
                    print(core_manager.format_markdown(core_memories))
                    print()
            except Exception as e:
                print(f"注意: 自动加载上下文失败: {e}")
            
            # 4. 生成状态报告
            result['success'] = True
            result['status'] = '记忆系统已就绪'  # 使用统一的"就绪"状态
            result['stats'] = {
                'recent_memories': len(recent_memories),
                'total_memories': total_memories,
                'system_ready': True
            }
            result['ready'] = True
            
        except Exception as e:
            result['status'] = f'启动失败: {str(e)}'
            result['ready'] = False
        
        return result
    
    @classmethod
    def get_bridge(cls) -> MemoryBridge:
        """获取记忆桥梁实例"""
        if not cls._initialized or cls._bridge is None:
            cls.initialize()
        return cls._bridge
    
    @classmethod
    def is_ready(cls) -> bool:
        """检查是否就绪"""
        return cls._initialized and cls._bridge is not None
    
    @classmethod
    def process_user_message(cls, content: str) -> dict:
        """
        处理用户消息
        
        自动初始化（如果未初始化）
        """
        bridge = cls.get_bridge()
        return bridge.user_input(content)
    
    @classmethod
    def process_assistant_message(cls, content: str):
        """处理助手消息"""
        if cls._bridge:
            cls._bridge.assistant_output(content)
    
    @classmethod
    def end_session(cls) -> str:
        """结束会话"""
        if cls._bridge:
            summary = cls._bridge.end()
            cls._initialized = False
            cls._bridge = None
            cls._instance = None
            return summary
        return ""


# 便捷函数
def load_memory() -> dict:
    """
    加载记忆 - 主入口
    
    用户说"加载记忆"时调用此函数
    """
    return MemoryInitializer.initialize()


def is_memory_ready() -> bool:
    """检查记忆系统是否就绪"""
    return MemoryInitializer.is_ready()


def user_speak(content: str) -> dict:
    """用户说话"""
    return MemoryInitializer.process_user_message(content)


def assistant_speak(content: str):
    """助手说话"""
    MemoryInitializer.process_assistant_message(content)


def end_memory_session() -> str:
    """结束记忆会话"""
    return MemoryInitializer.end_session()


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("🧠 记忆初始化器测试")
    print("=" * 60)
    print()
    
    # 测试1: 加载记忆
    print("【测试1】用户说: 加载记忆")
    result = load_memory()
    print(f"  状态: {result['status']}")
    print(f"  就绪: {result['ready']}")
    print(f"  历史记忆: {result['stats'].get('recent_memories', 0)} 条")
    print()
    
    # 测试2: 模拟对话
    print("【测试2】模拟对话")
    
    messages = [
        ("user", "我喜欢喝美式咖啡"),
        ("assistant", "记住了，你喜欢美式咖啡"),
        ("user", "我的生日是12月25日"),
        ("user", "对了，我喜欢什么咖啡？"),
    ]
    
    for speaker, content in messages:
        if speaker == "user":
            result = user_speak(content)
            saved = "💾" if result.get('saved') else "  "
            memories = len(result.get('memories', []))
            print(f"  安哥: {content}")
            print(f"      {saved} 保存:{result.get('saved')} | 相关记忆:{memories}条")
        else:
            assistant_speak(content)
            print(f"  安仔: {content}")
    
    print()
    
    # 测试3: 结束会话
    print("【测试3】结束会话")
    summary = end_memory_session()
    print(summary)
