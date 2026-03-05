"""
读取器模块
"""
from sync.readers.base_reader import BaseReader
from sync.readers.file_reader import FileReader

__all__ = [
    'BaseReader',
    'FileReader',
]
