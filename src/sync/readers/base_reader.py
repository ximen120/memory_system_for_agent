"""
数据源读取器基类
"""
from abc import ABC, abstractmethod
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class BaseReader(ABC):
    """数据源读取器基类"""
    
    @abstractmethod
    def read(self, source_config: Dict) -> str:
        """
        读取数据源内容
        
        Args:
            source_config: 数据源配置
        
        Returns:
            str: 数据源内容
        
        Raises:
            SourceNotFoundError: 数据源不存在
            SourceReadError: 读取失败
        """
        pass
    
    @abstractmethod
    def get_hash(self, source_config: Dict) -> str:
        """
        获取内容哈希（用于变化检测）
        
        Args:
            source_config: 数据源配置
        
        Returns:
            str: 内容的MD5哈希值
        """
        pass
    
    @abstractmethod
    def exists(self, source_config: Dict) -> bool:
        """
        检查数据源是否存在
        
        Args:
            source_config: 数据源配置
        
        Returns:
            bool: 是否存在
        """
        pass
