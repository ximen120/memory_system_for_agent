"""
记忆系统 v3.0 - 统一入口

整合四层架构：
- 核心层 (Core): 记忆单元、ID生成、验证
- 存储层 (Storage): ChromaDB、JSON存储
- 检索层 (Retrieval): 向量检索、关键词检索、混合检索
- 优化层 (Optimization): 性能监控、缓存、自动优化
- 傻瓜层 (UX): 自动触发、命令解析、标签管理

使用示例：
    >>> from memory_system import MemorySystem
    >>> 
    >>> # 创建系统
    >>> system = MemorySystem.create_default()
    >>> 
    >>> # 添加记忆
    >>> system.remember("我喜欢喝咖啡", tags=["偏好"])
    >>> 
    >>> # 检索记忆
    >>> results = system.recall("咖啡")
    >>> 
    >>> # 获取统计
    >>> print(system.get_stats())
"""

import logging
import os
import sys
from pathlib import Path

# 添加src目录到路径
_src_dir = Path(__file__).parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入各层组件
from core.memory_unit import MemoryUnit
from core.memory_manager import MemoryManager
from core.core_memory_manager import CoreMemoryManager
from storage.chroma_storage import ChromaStorage, chroma_storage_context
from retrieval.retrieval_api import RetrievalAPI, SearchMode
from retrieval.vector_search import VectorSearchResult
from optimization.auto_optimizer import AutoOptimizer
from ux.auto_trigger import AutoTrigger, TriggerDecision
from ux.tag_manager import TagManager
from ux.command_parser import CommandParser, CommandType
from ux.conversation_saver import ConversationSaver, SaveResult


@dataclass
class MemoryStats:
    """记忆统计信息"""
    total_memories: int
    tier_distribution: Dict[str, int]
    tag_count: int
    last_added: Optional[str] = None


class MemorySystem:
    """
    记忆系统统一入口
    
    整合所有组件，提供简洁的API供外部调用。
    """
    
    def __init__(
        self,
        data_dir: Optional[str] = None,
        enable_chroma: bool = False,
        enable_optimizer: bool = False
    ):
        """
        初始化记忆系统
        
        Args:
            data_dir: 数据目录，默认使用环境变量或默认路径
            enable_chroma: 是否启用ChromaDB向量存储
            enable_optimizer: 是否启用自动优化
        """
        # 解析数据目录
        self.data_dir = Path(data_dir) if data_dir else self._resolve_data_dir()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"MemorySystem 初始化: data_dir={self.data_dir}")
        
        # 初始化各组件
        self.memory_manager = MemoryManager(str(self.data_dir))
        self.core_manager = CoreMemoryManager()
        self.tag_manager = TagManager(str(self.data_dir))
        self.command_parser = CommandParser()
        
        # 初始化对话保存器（T2新增）
        self._conversation_saver = ConversationSaver()
        
        # 可选组件
        self.chroma_storage = None
        self.retrieval_api = None
        self.auto_optimizer = None
        self.auto_trigger = None
        
        if enable_chroma:
            try:
                self.chroma_storage = ChromaStorage(str(self.data_dir / "chroma_db"))
                self.retrieval_api = RetrievalAPI(self.chroma_storage)
                logger.info("ChromaDB 已启用")
            except Exception as e:
                logger.warning(f"ChromaDB 启用失败: {e}")
        
        if enable_optimizer:
            self.auto_optimizer = AutoOptimizer(self.memory_manager)
            self.auto_trigger = AutoTrigger(self.memory_manager)
            logger.info("自动优化已启用")
    
    def _resolve_data_dir(self) -> Path:
        """解析数据目录"""
        # 优先从环境变量读取
        env_path = os.getenv("MEMORY_DATA_DIR")
        if env_path:
            return Path(env_path)
        
        # 默认路径
        return Path("D:/AnZai_JieYue/memory/data")
    
    @classmethod
    def create_default(cls) -> "MemorySystem":
        """创建默认配置的记忆系统"""
        return cls()
    
    # ========== 核心API ==========
    
    def remember(
        self,
        content: str,
        tags: Optional[List[str]] = None,
        importance: float = 1.0
    ) -> str:
        """
        记住内容
        
        Args:
            content: 记忆内容
            tags: 标签列表
            importance: 重要性（1-5）
            
        Returns:
            记忆ID
        """
        memory = self.memory_manager.add_memory(
            content=content,
            tags=tags or [],
            importance=importance
        )
        
        # 如果启用了ChromaDB，同步添加
        if self.chroma_storage and memory.embedding:
            try:
                self.chroma_storage.add_memory(memory)
            except Exception as e:
                logger.warning(f"ChromaDB同步失败: {e}")
        
        return memory.id
    
    def recall(
        self,
        query: str,
        limit: int = 5,
        mode: str = "hybrid"
    ) -> List[MemoryUnit]:
        """
        回忆内容
        
        Args:
            query: 查询内容
            limit: 返回数量
            mode: 检索模式（keyword/vector/hybrid）
            
        Returns:
            记忆列表
        """
        if mode == "keyword":
            return self.memory_manager.search_by_keywords(query, limit)
        elif mode == "vector" and self.retrieval_api:
            return self.retrieval_api.vector_search(query, limit)
        else:
            # 默认使用关键词搜索
            return self.memory_manager.search_by_keywords(query, limit)
    
    def get_stats(self) -> MemoryStats:
        """获取统计信息"""
        stats = self.memory_manager.get_stats()
        return MemoryStats(
            total_memories=stats.get("total", 0),
            tier_distribution=stats.get("tiers", {}),
            tag_count=len(self.tag_manager.get_all_tags()),
            last_added=stats.get("last_added")
        )
    
    # ========== 自动加载上下文（T1新增） ==========
    
    def auto_load_context(
        self,
        limit: int = 5,
        output_format: str = "markdown"
    ) -> str:
        """
        自动加载最近核心记忆
        
        在对话启动时调用，返回格式化的上下文摘要。
        
        Args:
            limit: 加载记忆数量，默认5条
            output_format: 输出格式，"markdown"或"json"
            
        Returns:
            格式化的上下文摘要字符串
            
        Example:
            >>> system = MemorySystem.create_default()
            >>> context = system.auto_load_context(limit=5)
            >>> print(context)
        """
        try:
            # 检查是否已加载过（避免重复加载）
            if os.getenv("MEMORY_AUTO_LOAD_DONE"):
                return ""
            
            # 获取最近记忆
            memories = self.core_manager.get_recent_memories(limit=limit, tier="core")
            
            # 格式化为指定格式
            if output_format == "json":
                result = self.core_manager.format_json(memories)
            else:
                result = self.core_manager.format_markdown(memories)
            
            # 标记已加载
            os.environ["MEMORY_AUTO_LOAD_DONE"] = "1"
            
            return result
            
        except Exception as e:
            logger.warning(f"自动加载上下文失败: {e}")
            return "已自动加载上下文：\n\n暂无核心记忆\n\n---\n安哥，已准备好继续。"
    
    def reset_auto_load_flag(self):
        """重置自动加载标记（用于测试）"""
        if "MEMORY_AUTO_LOAD_DONE" in os.environ:
            del os.environ["MEMORY_AUTO_LOAD_DONE"]
    
    def on_message(self, role: str, content: str) -> SaveResult:
        """
        对话消息入口（T2新增）
        
        每条消息都经过这个方法，自动处理保存逻辑。
        
        Args:
            role: "user" 或 "assistant"
            content: 消息内容
            
        Returns:
            SaveResult
        """
        logger.info(f"处理消息: role={role}, content={content[:50]}...")
        return self._conversation_saver.on_message(role, content)
    
    def end_conversation(self) -> str:
        """
        结束对话（T2新增）
        
        强制保存并生成会话摘要。
        
        Returns:
            保存的文件路径
        """
        logger.info("结束对话，强制保存")
        file_path = self._conversation_saver.force_save()
        
        # 生成摘要
        summary = self._conversation_saver.get_session_summary()
        logger.info(f"会话摘要: {summary}")
        
        return file_path
    
    def close(self):
        """关闭系统，释放资源"""
        if self.chroma_storage:
            try:
                # ChromaDB不需要显式关闭
                pass
            except Exception as e:
                logger.warning(f"关闭ChromaDB失败: {e}")
        logger.info("MemorySystem 已关闭")


# 向后兼容
AutoMemory = MemorySystem
