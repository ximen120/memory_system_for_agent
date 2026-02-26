"""
验证工具单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from core.validators import (
    validate_memory_content,
    validate_memory_type,
    validate_importance,
    validate_memory_unit,
    ValidationError
)


class TestValidators:
    """测试验证工具"""
    
    # ========== 内容验证测试 ==========
    
    def test_validate_content_valid(self):
        """测试有效内容通过验证"""
        is_valid, error = validate_memory_content("这是一条有效内容")
        assert is_valid is True
        assert error == ""
    
    def test_validate_content_empty_string(self):
        """测试空字符串被拒绝"""
        is_valid, error = validate_memory_content("")
        assert is_valid is False
        assert "不能为空" in error
    
    def test_validate_content_whitespace_only(self):
        """测试仅空白字符被拒绝"""
        is_valid, error = validate_memory_content("   \n\t  ")
        assert is_valid is False
    
    def test_validate_content_none(self):
        """测试None被拒绝"""
        is_valid, error = validate_memory_content(None)
        assert is_valid is False
        assert "不能为空" in error
    
    def test_validate_content_non_string(self):
        """测试非字符串类型被拒绝"""
        is_valid, error = validate_memory_content(123)
        assert is_valid is False
        assert "必须是字符串" in error
    
    def test_validate_content_too_long(self):
        """测试超长内容被拒绝"""
        long_content = "x" * 10001
        is_valid, error = validate_memory_content(long_content)
        assert is_valid is False
        assert "超过限制" in error
    
    def test_validate_content_max_length_exact(self):
        """测试恰好最大长度通过"""
        content = "x" * 10000
        is_valid, error = validate_memory_content(content)
        assert is_valid is True
    
    # ========== 类型验证测试 ==========
    
    def test_validate_type_valid(self):
        """测试有效类型通过验证"""
        valid_types = ["fact", "preference", "context", "task", "event"]
        for mtype in valid_types:
            is_valid, error = validate_memory_type(mtype)
            assert is_valid is True, f"类型 {mtype} 应该有效"
    
    def test_validate_type_invalid(self):
        """测试无效类型被拒绝"""
        is_valid, error = validate_memory_type("invalid_type")
        assert is_valid is False
        assert "无效的类型" in error
    
    def test_validate_type_none(self):
        """测试None类型被拒绝"""
        is_valid, error = validate_memory_type(None)
        assert is_valid is False
    
    def test_validate_type_non_string(self):
        """测试非字符串类型被拒绝"""
        is_valid, error = validate_memory_type(123)
        assert is_valid is False
    
    # ========== 重要度验证测试 ==========
    
    def test_validate_importance_valid(self):
        """测试有效重要度通过验证"""
        for score in [1.0, 3.5, 5.0]:
            is_valid, error = validate_importance(score)
            assert is_valid is True, f"重要度 {score} 应该有效"
    
    def test_validate_importance_boundary(self):
        """测试边界值"""
        assert validate_importance(1.0)[0] is True  # 最小值
        assert validate_importance(5.0)[0] is True  # 最大值
    
    def test_validate_importance_out_of_range(self):
        """测试超出范围被拒绝"""
        assert validate_importance(0.5)[0] is False  # 太小
        assert validate_importance(5.5)[0] is False  # 太大
    
    def test_validate_importance_none(self):
        """测试None被拒绝"""
        is_valid, error = validate_importance(None)
        assert is_valid is False
    
    def test_validate_importance_non_number(self):
        """测试非数字被拒绝"""
        is_valid, error = validate_importance("high")
        assert is_valid is False
        assert "必须是数字" in error
    
    # ========== 完整MemoryUnit验证测试 ==========
    
    def test_validate_memory_unit_valid(self):
        """测试有效完整数据通过验证"""
        data = {
            "content": "测试内容",
            "memory_type": "fact",
            "importance": 4.5
        }
        is_valid, errors = validate_memory_unit(data)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_memory_unit_missing_required(self):
        """测试缺少必填字段被拒绝"""
        data = {"content": "测试内容"}  # 缺少 memory_type 和 importance
        is_valid, errors = validate_memory_unit(data)
        assert is_valid is False
        assert any("memory_type" in e for e in errors)
        assert any("importance" in e for e in errors)
    
    def test_validate_memory_unit_multiple_errors(self):
        """测试多个错误同时返回"""
        data = {
            "content": "",
            "memory_type": "invalid",
            "importance": 10.0
        }
        is_valid, errors = validate_memory_unit(data)
        assert is_valid is False
        assert len(errors) >= 3  # 内容、类型、重要度都有问题


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
