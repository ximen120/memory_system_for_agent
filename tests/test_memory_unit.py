"""
MemoryUnit 模型单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from pydantic import ValidationError
from core.memory_unit import MemoryUnit


class TestMemoryUnitCreation:
    """测试 MemoryUnit 创建"""
    
    def test_create_valid_memory(self):
        """测试创建有效记忆"""
        memory = MemoryUnit(
            content="测试内容",
            memory_type="fact",
            importance=3.5
        )
        assert memory.content == "测试内容"
        assert memory.memory_type == "fact"
        assert memory.importance == 3.5
        assert memory.memory_id.startswith("mem_")
        assert memory.created_at is not None
    
    def test_create_with_all_fields(self):
        """测试创建包含所有字段的记忆"""
        memory = MemoryUnit(
            content="完整测试",
            memory_type="preference",
            importance=4.0,
            source="test_dialog_001",
            tags=["测试", "完整"],
            embedding=[0.1, 0.2, 0.3]
        )
        assert memory.source == "test_dialog_001"
        assert "测试" in memory.tags
        assert memory.embedding == [0.1, 0.2, 0.3]
    
    def test_auto_generate_id(self):
        """测试自动生成唯一ID"""
        memory1 = MemoryUnit(content="内容1", memory_type="fact", importance=3)
        memory2 = MemoryUnit(content="内容2", memory_type="fact", importance=3)
        assert memory1.memory_id != memory2.memory_id
        assert len(memory1.memory_id.split("_")) == 3
    
    def test_auto_generate_timestamp(self):
        """测试自动生成时间戳"""
        memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
        assert memory.created_at is not None
        assert "T" in memory.created_at  # ISO格式包含T
    
    def test_default_values(self):
        """测试默认值"""
        memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
        assert memory.tags == []
        assert memory.embedding is None
        assert memory.source is None
        assert memory.access_count == 0
        assert memory.updated_at is None
        assert memory.last_accessed_at is None


class TestMemoryUnitValidation:
    """测试字段验证"""
    
    def test_content_required(self):
        """测试内容必填"""
        with pytest.raises(ValidationError) as exc_info:
            MemoryUnit(content="", memory_type="fact", importance=3)
        # Pydantic 的 min_length=1 会拦截空字符串
        assert "string_too_short" in str(exc_info.value) or "不能为空" in str(exc_info.value)
    
    def test_content_whitespace_only_rejected(self):
        """测试仅空白内容被拒绝"""
        with pytest.raises(ValidationError):
            MemoryUnit(content="   \n\t  ", memory_type="fact", importance=3)
    
    def test_content_too_long(self):
        """测试内容过长被拒绝"""
        with pytest.raises(ValidationError):
            MemoryUnit(content="x" * 10001, memory_type="fact", importance=3)
    
    def test_memory_type_valid_values(self):
        """测试有效记忆类型"""
        valid_types = ["fact", "preference", "context", "task", "event"]
        for mtype in valid_types:
            memory = MemoryUnit(content="测试", memory_type=mtype, importance=3)
            assert memory.memory_type == mtype
    
    def test_memory_type_invalid_rejected(self):
        """测试无效记忆类型被拒绝"""
        with pytest.raises(ValidationError) as exc_info:
            MemoryUnit(content="测试", memory_type="invalid", importance=3)
        assert "无效的记忆类型" in str(exc_info.value)
    
    def test_importance_range(self):
        """测试重要度范围 1.0-5.0"""
        # 边界值
        MemoryUnit(content="测试", memory_type="fact", importance=1.0)
        MemoryUnit(content="测试", memory_type="fact", importance=5.0)
        
        # 超出范围
        with pytest.raises(ValidationError):
            MemoryUnit(content="测试", memory_type="fact", importance=0.5)
        with pytest.raises(ValidationError):
            MemoryUnit(content="测试", memory_type="fact", importance=5.5)
    
    def test_tags_deduplication(self):
        """测试标签去重"""
        memory = MemoryUnit(
            content="测试",
            memory_type="fact",
            importance=3,
            tags=["A", "B", "A", "C", "B"]
        )
        assert len(memory.tags) == 3
        assert set(memory.tags) == {"A", "B", "C"}
    
    def test_tags_whitespace_cleaning(self):
        """测试标签空白清理"""
        memory = MemoryUnit(
            content="测试",
            memory_type="fact",
            importance=3,
            tags=["  A  ", "", "  ", "B"]
        )
        assert "A" in memory.tags
        assert "B" in memory.tags
        assert "" not in memory.tags


class TestMemoryUnitMethods:
    """测试 MemoryUnit 方法"""
    
    def test_update_access(self):
        """测试更新访问统计"""
        memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
        assert memory.access_count == 0
        assert memory.last_accessed_at is None
        
        memory.update_access()
        assert memory.access_count == 1
        assert memory.last_accessed_at is not None
        
        memory.update_access()
        assert memory.access_count == 2
    
    def test_update_content(self):
        """测试更新内容"""
        memory = MemoryUnit(content="旧内容", memory_type="fact", importance=3)
        original_updated_at = memory.updated_at
        
        memory.update_content("新内容")
        assert memory.content == "新内容"
        assert memory.updated_at is not None
        assert memory.embedding is None  # embedding 应该被清除
    
    def test_update_content_strips_whitespace(self):
        """测试更新内容时去除空白"""
        memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
        memory.update_content("  新内容  ")
        assert memory.content == "新内容"


class TestChromaDBConversion:
    """测试 ChromaDB 格式转换"""
    
    def test_to_chroma_document(self):
        """测试转换为 ChromaDB 格式"""
        memory = MemoryUnit(
            content="测试内容",
            memory_type="fact",
            importance=3.5,
            source="dialog_001",
            tags=["测试"],
            embedding=[0.1, 0.2, 0.3]
        )
        memory.update_access()  # 增加访问计数
        
        doc = memory.to_chroma_document()
        
        assert doc["id"] == memory.memory_id
        assert doc["document"] == "测试内容"
        assert doc["metadata"]["memory_type"] == "fact"
        assert doc["metadata"]["importance"] == 3.5
        assert doc["metadata"]["source"] == "dialog_001"
        assert doc["metadata"]["access_count"] == 1
        assert doc["embedding"] == [0.1, 0.2, 0.3]
    
    def test_from_chroma_document(self):
        """测试从 ChromaDB 格式重建"""
        original = MemoryUnit(
            content="原始内容",
            memory_type="preference",
            importance=4.0,
            source="source_001",
            tags=["标签1", "标签2"]
        )
        
        doc = original.to_chroma_document()
        restored = MemoryUnit.from_chroma_document(doc)
        
        assert restored.memory_id == original.memory_id
        assert restored.content == original.content
        assert restored.memory_type == original.memory_type
        assert restored.importance == original.importance
        assert restored.source == original.source
        assert set(restored.tags) == set(original.tags)
    
    def test_from_chroma_document_with_defaults(self):
        """测试从不完整文档重建（使用默认值）"""
        doc = {
            "id": "test_id",
            "document": "内容",
            "metadata": {}
        }
        
        memory = MemoryUnit.from_chroma_document(doc)
        assert memory.memory_id == "test_id"
        assert memory.content == "内容"
        assert memory.memory_type == "fact"  # 默认值
        assert memory.importance == 3.0  # 默认值


class TestMemoryUnitStringRepresentation:
    """测试字符串表示"""
    
    def test_str_representation(self):
        """测试简洁字符串表示"""
        memory = MemoryUnit(content="短内容", memory_type="fact", importance=3)
        str_repr = str(memory)
        assert "MemoryUnit" in str_repr
        assert memory.memory_id in str_repr
        assert "短内容" in str_repr
    
    def test_str_truncates_long_content(self):
        """测试长内容截断"""
        long_content = "A" * 100
        memory = MemoryUnit(content=long_content, memory_type="fact", importance=3)
        str_repr = str(memory)
        assert "..." in str_repr
        assert len(str_repr) < len(long_content) + 50
    
    def test_repr_representation(self):
        """测试详细字符串表示"""
        memory = MemoryUnit(content="测试内容", memory_type="fact", importance=3)
        repr_str = repr(memory)
        assert "MemoryUnit(" in repr_str
        assert "fact" in repr_str
        assert "3" in repr_str


class TestMemoryUnitValidation:
    """测试验证器"""
    
    def test_memory_type_validator_rejects_invalid(self):
        """测试验证器拒绝无效类型"""
        with pytest.raises(Exception) as exc_info:
            MemoryUnit(content="测试", memory_type="invalid_type", importance=3)
        assert "无效的记忆类型" in str(exc_info.value)
    
    def test_content_validator_strips_whitespace(self):
        """测试内容验证器去除空白"""
        memory = MemoryUnit(content="  测试内容  ", memory_type="fact", importance=3)
        assert memory.content == "测试内容"
    
    def test_tags_validator_removes_duplicates(self):
        """测试标签验证器去重"""
        memory = MemoryUnit(
            content="测试",
            memory_type="fact",
            importance=3,
            tags=["A", "B", "A", "C"]
        )
        assert len(memory.tags) == 3
        assert set(memory.tags) == {"A", "B", "C"}
    
    def test_tags_validator_removes_empty(self):
        """测试标签验证器去除空标签"""
        memory = MemoryUnit(
            content="测试",
            memory_type="fact",
            importance=3,
            tags=["A", "", "  ", "B"]
        )
        assert "" not in memory.tags
        assert "  " not in memory.tags


class TestMemoryUnitEdgeCases:
    """测试边界情况"""
    
    def test_update_access_multiple_times(self):
        """测试多次更新访问"""
        memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
        
        for i in range(5):
            memory.update_access()
        
        assert memory.access_count == 5
        assert memory.last_accessed_at is not None
    
    def test_update_content_clears_embedding(self):
        """测试更新内容清除 embedding"""
        memory = MemoryUnit(
            content="原始内容",
            memory_type="fact",
            importance=3,
            embedding=[0.1, 0.2, 0.3]
        )
        
        memory.update_content("新内容")
        
        assert memory.embedding is None
        assert memory.updated_at is not None
    
    def test_to_chroma_document_with_none_embedding(self):
        """测试 to_chroma_document 处理 None embedding"""
        memory = MemoryUnit(content="测试", memory_type="fact", importance=3)
        
        doc = memory.to_chroma_document()
        
        assert doc["embedding"] is None
    
    def test_from_chroma_document_with_none_embedding(self):
        """测试 from_chroma_document 处理 None embedding"""
        doc = {
            "id": "test_id",
            "document": "内容",
            "metadata": {"memory_type": "fact", "importance": 3.0},
            "embedding": None
        }
        
        memory = MemoryUnit.from_chroma_document(doc)
        assert memory.embedding is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
