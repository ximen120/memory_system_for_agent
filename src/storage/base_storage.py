"""
存储抽象基类

定义所有存储后端的通用接口。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class StorageError(Exception):
    """存储操作错误"""
    pass


class MemoryNotFoundError(StorageError):
    """记忆不存在错误"""
    pass


class BaseStorage(ABC):
    """
    存储抽象基类
    
    所有存储后端（JSON文件、ChromaDB等）必须实现此接口。
    
    Attributes:
        storage_name: 存储后端名称
    """
    
    def __init__(self, storage_name: str):
        """
        初始化存储
        
        Args:
            storage_name: 存储后端名称，用于标识
        """
        self.storage_name = storage_name
    
    @abstractmethod
    def save(self, memory_unit: "MemoryUnit") -> str:
        """
        保存记忆单元
        
        Args:
            memory_unit: 要保存的记忆单元
            
        Returns:
            str: 保存的记忆ID
            
        Raises:
            StorageError: 保存失败时抛出
        """
        pass
    
    @abstractmethod
    def load(self, memory_id: str) -> "MemoryUnit":
        """
        加载指定ID的记忆
        
        Args:
            memory_id: 记忆唯一标识符
            
        Returns:
            MemoryUnit: 加载的记忆单元
            
        Raises:
            MemoryNotFoundError: 记忆不存在时抛出
            StorageError: 加载失败时抛出
        """
        pass
    
    @abstractmethod
    def delete(self, memory_id: str) -> bool:
        """
        删除指定ID的记忆
        
        Args:
            memory_id: 记忆唯一标识符
            
        Returns:
            bool: 删除成功返回True，记忆不存在返回False
            
        Raises:
            StorageError: 删除失败时抛出
        """
        pass
    
    @abstractmethod
    def query(
        self,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_importance: Optional[float] = None,
        limit: int = 10
    ) -> List["MemoryUnit"]:
        """
        条件查询记忆
        
        Args:
            memory_type: 按类型过滤（可选）
            tags: 按标签过滤，包含任一标签即可（可选）
            min_importance: 最小重要度（可选）
            limit: 返回结果数量上限，默认10
            
        Returns:
            List[MemoryUnit]: 符合条件的记忆列表
            
        Raises:
            StorageError: 查询失败时抛出
        """
        pass
    
    @abstractmethod
    def exists(self, memory_id: str) -> bool:
        """
        检查记忆是否存在
        
        Args:
            memory_id: 记忆唯一标识符
            
        Returns:
            bool: 存在返回True，否则返回False
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """
        获取存储的记忆总数
        
        Returns:
            int: 记忆总数
        """
        pass
    
    @abstractmethod
    def close(self) -> None:
        """
        关闭存储连接，释放资源
        
        应在程序退出前调用，确保数据持久化。
        """
        pass
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出，自动关闭"""
        self.close()


if __name__ == "__main__":
    # 简单测试：验证抽象类不能被实例化
    print("测试 BaseStorage 抽象类:")
    
    try:
        storage = BaseStorage("test")
        print("❌ 错误：抽象类不应该能被实例化")
    except TypeError as e:
        print(f"✅ 正确：抽象类无法实例化 - {e}")
    
    print("\nBaseStorage 定义的抽象方法:")
    for method_name in ['save', 'load', 'delete', 'query', 'exists', 'count', 'close']:
        print(f"  - {method_name}")
