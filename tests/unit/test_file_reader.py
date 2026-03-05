"""
文件读取器单元测试
"""
import sys
import pytest
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sync.readers.file_reader import FileReader
from sync.exceptions import SourceNotFoundError, SourceReadError


def test_file_reader_exists():
    """测试文件存在检查"""
    reader = FileReader()
    
    # 存在的文件
    assert reader.exists({'path': 'tests/fixtures/test_todo.md'}) is True
    
    # 不存在的文件
    assert reader.exists({'path': 'tests/fixtures/nonexistent.txt'}) is False
    
    # 目录（不是文件）
    assert reader.exists({'path': 'tests/fixtures'}) is False


def test_file_reader_read():
    """测试读取文件"""
    reader = FileReader()
    
    content = reader.read({'path': 'tests/fixtures/test_todo.md', 'encoding': 'utf-8'})
    assert "测试待办清单" in content
    assert "测试任务1" in content


def test_file_reader_read_not_found():
    """测试读取不存在的文件"""
    reader = FileReader()
    
    with pytest.raises(SourceNotFoundError) as exc_info:
        reader.read({'path': 'tests/fixtures/nonexistent.txt'})
    assert "文件不存在" in str(exc_info.value)


def test_file_reader_get_hash():
    """测试获取文件哈希"""
    reader = FileReader()
    
    hash1 = reader.get_hash({'path': 'tests/fixtures/test_todo.md', 'encoding': 'utf-8'})
    hash2 = reader.get_hash({'path': 'tests/fixtures/test_todo.md', 'encoding': 'utf-8'})
    
    # 相同内容，哈希相同
    assert hash1 == hash2
    assert len(hash1) == 32  # MD5哈希长度


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
