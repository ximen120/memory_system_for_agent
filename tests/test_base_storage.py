"""
存储抽象基类单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from storage.base_storage import BaseStorage, StorageError, MemoryNotFoundError


class TestBaseStorageAbstract:
    """测试 BaseStorage 抽象类"""
    
    def test_base_storage_cannot_instantiate(self):
        """测试抽象类不能被实例化"""
        with pytest.raises(TypeError) as exc_info:
            BaseStorage("test")
        assert "abstract" in str(exc_info.value).lower()
    
    def test_storage_error_is_exception(self):
        """测试 StorageError 是 Exception 子类"""
        assert issubclass(StorageError, Exception)
        
        # 可以抛出和捕获
        with pytest.raises(StorageError):
            raise StorageError("测试错误")
    
    def test_memory_not_found_error_is_storage_error(self):
        """测试 MemoryNotFoundError 是 StorageError 子类"""
        assert issubclass(MemoryNotFoundError, StorageError)
        
        # 可以抛出和捕获
        with pytest.raises(MemoryNotFoundError):
            raise MemoryNotFoundError("记忆不存在")
        
        # 也可以用 StorageError 捕获
        with pytest.raises(StorageError):
            raise MemoryNotFoundError("记忆不存在")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
