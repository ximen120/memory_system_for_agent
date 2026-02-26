"""
ID生成器单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from core.id_generator import generate_memory_id, validate_memory_id


class TestIdGenerator:
    """测试ID生成器"""
    
    def test_generate_memory_id_format(self):
        """测试生成的ID格式正确"""
        memory_id = generate_memory_id()
        parts = memory_id.split("_")
        
        # 格式: mem_{timestamp}_{random}
        assert len(parts) == 3
        assert parts[0] == "mem"
        assert len(parts[1]) == 14  # 时间戳: YYYYMMDDHHMMSS
        assert parts[1].isdigit()
        assert len(parts[2]) == 8   # 随机部分
        assert all(c.islower() or c.isdigit() for c in parts[2])
    
    def test_generate_memory_id_unique(self):
        """测试生成的ID唯一性（10000次）"""
        ids = [generate_memory_id() for _ in range(10000)]
        assert len(set(ids)) == 10000, "存在重复ID"
    
    def test_generate_memory_id_different_calls(self):
        """测试多次调用生成不同ID"""
        id1 = generate_memory_id()
        id2 = generate_memory_id()
        assert id1 != id2
    
    def test_validate_memory_id_valid(self):
        """测试验证有效的ID"""
        valid_id = "mem_20260223103000_a1b2c3d4"
        assert validate_memory_id(valid_id) is True
    
    def test_validate_memory_id_invalid_prefix(self):
        """测试验证错误前缀"""
        assert validate_memory_id("invalid_20260223103000_a1b2c3d4") is False
    
    def test_validate_memory_id_invalid_timestamp_length(self):
        """测试验证时间戳长度错误"""
        assert validate_memory_id("mem_20260223_a1b2c3d4") is False  # 太短
        assert validate_memory_id("mem_20260223103000000_a1b2c3d4") is False  # 太长
    
    def test_validate_memory_id_invalid_timestamp_chars(self):
        """测试验证时间戳包含非数字"""
        assert validate_memory_id("mem_2026AB23103000_a1b2c3d4") is False
    
    def test_validate_memory_id_invalid_random_length(self):
        """测试验证随机部分长度错误"""
        assert validate_memory_id("mem_20260223103000_a1b2c3") is False  # 太短
        assert validate_memory_id("mem_20260223103000_a1b2c3d4e5") is False  # 太长
    
    def test_validate_memory_id_invalid_random_chars(self):
        """测试验证随机部分包含大写字母"""
        assert validate_memory_id("mem_20260223103000_A1B2C3D4") is False
    
    def test_validate_memory_id_empty(self):
        """测试验证空字符串"""
        assert validate_memory_id("") is False
    
    def test_validate_memory_id_none(self):
        """测试验证None"""
        assert validate_memory_id(None) is False
    
    def test_validate_memory_id_wrong_parts_count(self):
        """测试验证部分数量错误"""
        assert validate_memory_id("mem_20260223103000") is False  # 缺少随机部分
        assert validate_memory_id("mem_20260223103000_a1b2c3d4_extra") is False  # 多余部分
    
    def test_validate_memory_id_non_string_input(self):
        """测试验证非字符串输入"""
        assert validate_memory_id(None) is False
        assert validate_memory_id(123) is False
        assert validate_memory_id([]) is False
        assert validate_memory_id({}) is False
    
    def test_validate_memory_id_empty_string(self):
        """测试验证空字符串"""
        assert validate_memory_id("") is False
    
    def test_validate_memory_id_random_part_uppercase(self):
        """测试验证随机部分包含大写字母"""
        assert validate_memory_id("mem_20260223103000_A1B2C3D4") is False
    
    def test_validate_memory_id_random_part_special_chars(self):
        """测试验证随机部分包含特殊字符"""
        assert validate_memory_id("mem_20260223103000_a1b2!@#$") is False
    
    def test_validate_memory_id_timestamp_leading_zeros(self):
        """测试验证时间戳前导零"""
        # 时间戳可以有前导零，只要14位数字
        assert validate_memory_id("mem_00000000000000_a1b2c3d4") is True
    
    def test_generate_id_contains_only_valid_chars(self):
        """测试生成的ID只包含有效字符"""
        for _ in range(100):
            memory_id = generate_memory_id()
            # 检查整体格式
            assert memory_id.startswith("mem_")
            # 检查没有大写字母
            assert memory_id == memory_id.lower() or memory_id[4:].islower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
