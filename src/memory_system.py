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
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入各层组件
try:
    from core.memory_unit import MemoryUnit
    from core.memory_manager import MemoryManager
    from storage.chroma_storage import ChromaStorage, chroma_storage_context
    from retrieval.retrieval_api import RetrievalAPI, SearchMode
    from retrieval.vector_search import VectorSearchResult
    from optimization.auto_optimizer import AutoOptimizer
    from ux.auto_trigger import AutoTrigger, TriggerDecision
    from ux.tag_manager import TagManager
    from ux.command_parser import CommandParser, CommandType
except ImportError:
    from src.core.memory_unit import MemoryUnit
    from src.core.memory_manager import MemoryManager
    from src.storage.chroma_storage import ChromaStorage, chroma_storage_context
    from src.retrieval.retrieval_api import RetrievalAPI, SearchMode
    from src.retrieval.vector_search import VectorSearchResult
    from src.optimization.auto_optimizer import AutoOptimizer
    from src.ux.auto_trigger import AutoTrigger, TriggerDecision
    from src.ux.tag_manager import TagManager
    from src.ux.command_parser import CommandParser, CommandType


@dataclass
class MemorySystemConfig:
    """记忆系统配置"""
    storage_path: str = "./data/memory_db"
    collection_name: str = "memories"
    model_name: str = "all-MiniLM-L6-v2"
    enable_auto_optimize: bool = True
    enable_auto_trigger: bool = True
    cache_size: int = 1000
    min_confidence: float = 0.6


class MemorySystem:
    """
    记忆系统统一入口
    
    整合四层架构，提供简洁的API。
    """
    
    def __init__(
        self,
        storage: ChromaStorage,
        retrieval_api: RetrievalAPI,
        auto_optimizer: Optional[AutoOptimizer] = None,
        auto_trigger: Optional[AutoTrigger] = None,
        tag_manager: Optional[TagManager] = None,
        config: Optional[MemorySystemConfig] = None
    ):
        """
        初始化记忆系统
        
        Args:
            storage: 存储后端
            retrieval_api: 检索API
            auto_optimizer: 自动优化器
            auto_trigger: 自动触发器
            tag_manager: 标签管理器
            config: 配置
        """
        self.storage = storage
        self.retrieval_api = retrieval_api
        self.auto_optimizer = auto_optimizer
        self.auto_trigger = auto_trigger
        self.tag_manager = tag_manager
        self.config = config or MemorySystemConfig()
        
        # 启动自动优化
        if self.auto_optimizer and self.config.enable_auto_optimize:
            self.auto_optimizer.start()
        
        logger.info("记忆系统初始化完成")
    
    @classmethod
    def create_default(
        cls,
        storage_path: str = "./data/memory_db",
        collection_name: str = "memories"
    ) -> "MemorySystem":
        """
        创建默认配置的记忆系统
        
        Args:
            storage_path: 存储路径
            collection_name: 集合名称
            
        Returns:
            MemorySystem实例
        """
        logger.info(f"创建记忆系统: path={storage_path}, collection={collection_name}")
        
        # 创建存储
        storage = ChromaStorage(storage_path, collection_name)
        
        # 创建检索API
        retrieval_api = RetrievalAPI.create_default(
            storage_path=storage_path,
            collection_name=collection_name
        )
        
        # 创建自动优化器
        auto_optimizer = AutoOptimizer(
            storage=storage,
            enable_monitoring=True,
            enable_auto_optimize=True
        )
        
        # 创建自动触发器
        auto_trigger = AutoTrigger(min_confidence=0.6)
        
        # 创建标签管理器
        tag_manager = TagManager()
        
        return cls(
            storage=storage,
            retrieval_api=retrieval_api,
            auto_optimizer=auto_optimizer,
            auto_trigger=auto_trigger,
            tag_manager=tag_manager
        )
    
    def remember(
        self,
        content: str,
        memory_type: str = "fact",
        tags: Optional[List[str]] = None,
        importance: float = 3.0,
        source: str = "user"
    ) -> Optional[str]:
        """
        记住内容（傻瓜式API）
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            tags: 标签列表
            importance: 重要度
            source: 来源
            
        Returns:
            记忆ID或None
        """
        try:
            # 使用检索API添加记忆
            memory_id = self.retrieval_api.add_memory(
                content=content,
                memory_type=memory_type,
                tags=tags or [],
                importance=importance,
                source=source
            )
            
            if memory_id:
                logger.info(f"已记住: {content[:30]}... (ID: {memory_id})")
            
            return memory_id
            
        except Exception as e:
            logger.error(f"记住失败: {e}")
            return None
    
    def recall(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.5,
        use_hybrid: bool = True
    ) -> List[Union[VectorSearchResult, Any]]:
        """
        回忆内容（傻瓜式API）
        
        Args:
            query: 查询文本
            top_k: 返回数量
            min_score: 最小分数
            use_hybrid: 使用混合检索
            
        Returns:
            记忆列表
        """
        try:
            if use_hybrid:
                response = self.retrieval_api.hybrid_search(
                    query=query,
                    top_k=top_k,
                    min_score=min_score
                )
            else:
                response = self.retrieval_api.vector_search(
                    query=query,
                    top_k=top_k,
                    min_similarity=min_score
                )
            
            results = response.results
            logger.info(f"回忆: '{query}' -> {len(results)}条结果")
            
            return results
            
        except Exception as e:
            logger.error(f"回忆失败: {e}")
            return []
    
    def forget(self, memory_id: str) -> bool:
        """
        遗忘内容（傻瓜式API）
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否成功
        """
        try:
            result = self.retrieval_api.remove_memory(memory_id)
            
            if result:
                logger.info(f"已遗忘: {memory_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"遗忘失败: {e}")
            return False
    
    def should_remember(self, content: str, context: Optional[Dict] = None) -> TriggerDecision:
        """
        判断是否值得记住（自动触发）
        
        Args:
            content: 内容
            context: 上下文
            
        Returns:
            触发决策
        """
        if not self.auto_trigger:
            return TriggerDecision(
                should_save=True,
                confidence=1.0,
                reason="无自动触发器，默认保存",
                strategy="default"
            )
        
        return self.auto_trigger.should_save(content, context)
    
    def process_message(
        self,
        role: str,
        content: str,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        处理消息（全自动模式）
        
        Args:
            role: 角色 (user/assistant)
            content: 消息内容
            auto_save: 自动保存
            
        Returns:
            处理结果
        """
        result = {
            "saved": False,
            "memory_id": None,
            "decision": None
        }
        
        # 解析命令
        parser = CommandParser()
        command = parser.parse(content)
        
        # 处理命令
        if command.command_type == CommandType.REMEMBER:
            # 明确保存指令
            memory_id = self.remember(
                content=command.content,
                tags=command.tags
            )
            result["saved"] = memory_id is not None
            result["memory_id"] = memory_id
            
        elif command.command_type == CommandType.FORGET:
            # 删除指令
            if command.memory_id:
                result["forgotten"] = self.forget(command.memory_id)
                
        elif command.command_type == CommandType.SEARCH:
            # 搜索指令
            results = self.recall(command.query)
            result["search_results"] = results
            
        elif auto_save and role == "user":
            # 自动判断是否保存
            decision = self.should_remember(content)
            result["decision"] = decision
            
            if decision.should_save:
                memory_id = self.remember(content)
                result["saved"] = memory_id is not None
                result["memory_id"] = memory_id
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取系统统计
        
        Returns:
            统计信息
        """
        stats = {
            "storage": {},
            "retrieval": {},
            "optimization": {},
            "timestamp": None
        }
        
        try:
            # 存储统计
            stats["storage"] = {
                "total_memories": self.storage.count(),
                "collection_name": self.storage.collection_name
            }
        except Exception as e:
            logger.warning(f"获取存储统计失败: {e}")
        
        try:
            # 检索统计
            stats["retrieval"] = self.retrieval_api.get_stats()
        except Exception as e:
            logger.warning(f"获取检索统计失败: {e}")
        
        try:
            # 优化统计
            if self.auto_optimizer:
                stats["optimization"] = {
                    "performance": self.auto_optimizer.get_performance_stats(),
                    "cache": self.auto_optimizer.get_cache_stats()
                }
        except Exception as e:
            logger.warning(f"获取优化统计失败: {e}")
        
        from datetime import datetime
        stats["timestamp"] = datetime.now().isoformat()
        
        return stats
    
    def get_optimization_report(self) -> str:
        """
        获取优化报告
        
        Returns:
            优化报告
        """
        if self.auto_optimizer:
            return self.auto_optimizer.get_optimization_report()
        return "自动优化器未启用"
    
    def close(self):
        """关闭系统"""
        logger.info("关闭记忆系统...")
        
        if self.auto_optimizer:
            self.auto_optimizer.stop()
        
        # 关闭存储连接
        try:
            self.storage.close()
        except:
            pass
        
        logger.info("记忆系统已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False


# 便捷函数
def quick_remember(content: str, **kwargs) -> Optional[str]:
    """
    快速记住（无需创建系统实例）
    
    Args:
        content: 内容
        **kwargs: 其他参数
        
    Returns:
        记忆ID
    """
    system = MemorySystem.create_default()
    with system:
        return system.remember(content, **kwargs)


def quick_recall(query: str, **kwargs) -> List[Any]:
    """
    快速回忆（无需创建系统实例）
    
    Args:
        query: 查询
        **kwargs: 其他参数
        
    Returns:
        结果列表
    """
    system = MemorySystem.create_default()
    with system:
        return system.recall(query, **kwargs)


if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("记忆系统 v3.0 测试")
    print("=" * 50)
    
    # 创建系统
    system = MemorySystem.create_default("./test_data", "test_memories")
    
    print("\n1. 测试记住")
    memory_id = system.remember(
        content="我喜欢在早晨喝咖啡",
        tags=["饮食", "偏好"],
        importance=4.0
    )
    print(f"   记忆ID: {memory_id}")
    
    print("\n2. 测试回忆")
    results = system.recall("咖啡", top_k=5)
    print(f"   找到 {len(results)} 条记忆")
    for r in results:
        print(f"   - {r.content[:30]}...")
    
    print("\n3. 测试统计")
    stats = system.get_stats()
    print(f"   存储: {stats['storage']}")
    
    print("\n4. 关闭系统")
    system.close()
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
