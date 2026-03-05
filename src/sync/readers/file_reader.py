"""
文件读取器
"""
import hashlib
import logging
from pathlib import Path
from typing import Dict
from sync.exceptions import SourceNotFoundError, SourceReadError
from .base_reader import BaseReader

logger = logging.getLogger(__name__)

class FileReader(BaseReader):
    """文件读取器"""
    
    def exists(self, source_config: Dict) -> bool:
        """检查文件是否存在"""
        path = Path(source_config['path'])
        return path.exists() and path.is_file()
    
    def read(self, source_config: Dict) -> str:
        """读取文件内容"""
        path = Path(source_config['path'])
        
        if not path.exists():
            raise SourceNotFoundError(f"文件不存在: {path}")
        
        if not path.is_file():
            raise SourceNotFoundError(f"路径不是文件: {path}")
        
        try:
            encoding = source_config.get('encoding', 'utf-8')
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            logger.debug(f"成功读取文件: {path}, 大小: {len(content)} 字符")
            return content
        except UnicodeDecodeError as e:
            raise SourceReadError(f"文件编码错误: {path}, 尝试使用 {encoding} 编码, 错误: {e}")
        except PermissionError as e:
            raise SourceReadError(f"文件权限不足: {path}, 错误: {e}")
        except Exception as e:
            raise SourceReadError(f"读取文件失败: {path}, 错误: {e}")
    
    def get_hash(self, source_config: Dict) -> str:
        """获取文件内容哈希"""
        try:
            content = self.read(source_config)
            normalized = content.strip().replace('\r\n', '\n')
            hash_value = hashlib.md5(normalized.encode()).hexdigest()
            logger.debug(f"文件哈希: {hash_value}")
            return hash_value
        except Exception as e:
            logger.error(f"计算哈希失败: {e}")
            raise
