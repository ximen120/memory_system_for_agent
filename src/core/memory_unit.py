"""
MemoryUnit 核心模型

记忆系统的基本数据单元，封装一条记忆的完整信息。
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

try:
    from .timestamp_utils import now
    from .id_generator import generate_memory_id
except ImportError:
    from timestamp_utils import now
    from id_generator import generate_memory_id


class MemoryUnit(BaseModel):
    """
    记忆单元模型
    
    代表系统中的一条记忆，包含内容、元数据、向量表示等。
    """
    
    # ========== 核心字段 ==========
    
    memory_id: str = Field(
        default_factory=generate_memory_id,
        description="唯一标识符，格式: mem_{timestamp}_{random}"
    )
    
    content: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="记忆内容文本"
    )
    
    memory_type: str = Field(
        ...,
        description="记忆类型: fact/preference/context/task/event"
    )
    
    importance: float = Field(
        ...,
        ge=1.0,
        le=5.0,
        description="重要度评分 1.0-5.0"
    )
    
    # ========== 时间戳字段 ==========
    
    created_at: str = Field(
        default_factory=now,
        description="创建时间，ISO 8601格式"
    )
    
    updated_at: Optional[str] = Field(
        default=None,
        description="最后更新时间"
    )
    
    # ========== 元数据字段 ==========
    
    source: Optional[str] = Field(
        default=None,
        description="记忆来源，如对话ID、文件路径等"
    )
    
    tags: List[str] = Field(
        default_factory=list,
        description="标签列表，用于分类"
    )
    
    # ========== 向量字段 ==========
    
    embedding: Optional[List[float]] = Field(
        default=None,
        description="向量表示，用于语义检索"
    )
    
    # ========== 统计字段 ==========
    
    access_count: int = Field(
        default=0,
        ge=0,
        description="被检索次数"
    )
    
    last_accessed_at: Optional[str] = Field(
        default=None,
        description="最后检索时间"
    )
    
    # ========== 验证器 ==========
    
    @field_validator('memory_type')
    @classmethod
    def validate_memory_type(cls, v: str) -> str:
        """验证记忆类型"""
        valid_types = {'fact', 'preference', 'context', 'task', 'event'}
        if v not in valid_types:
            raise ValueError(f"无效的记忆类型 '{v}'，必须是: {', '.join(valid_types)}")
        return v
    
    @field_validator('content')
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """验证内容不为空"""
        if not v or not v.strip():
            raise ValueError("内容不能为空")
        return v.strip()
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """清理标签（去重、去空）"""
        return list(set(tag.strip() for tag in v if tag and tag.strip()))
    
    # ========== 方法 ==========
    
    def update_access(self) -> None:
        """更新访问统计"""
        self.access_count += 1
        self.last_accessed_at = now()
    
    def update_content(self, new_content: str) -> None:
        """更新内容"""
        self.content = new_content.strip()
        self.updated_at = now()
        # 内容变了，embedding 需要重新生成
        self.embedding = None
    
    def to_chroma_document(self) -> Dict[str, Any]:
        """
        转换为 ChromaDB 文档格式
        
        Returns:
            Dict: 包含 id, document, metadata, embedding 的字典
        """
        return {
            "id": self.memory_id,
            "document": self.content,
            "metadata": {
                "memory_type": self.memory_type,
                "importance": self.importance,
                "created_at": self.created_at,
                "source": self.source,
                "tags": self.tags,
                "access_count": self.access_count,
            },
            "embedding": self.embedding
        }
    
    @classmethod
    def from_chroma_document(cls, doc: Dict[str, Any]) -> "MemoryUnit":
        """
        从 ChromaDB 文档格式创建 MemoryUnit
        
        Args:
            doc: ChromaDB 返回的文档字典
            
        Returns:
            MemoryUnit: 重建的记忆单元
        """
        metadata = doc.get("metadata", {})
        
        return cls(
            memory_id=doc.get("id", generate_memory_id()),
            content=doc.get("document", ""),
            memory_type=metadata.get("memory_type", "fact"),
            importance=metadata.get("importance", 3.0),
            created_at=metadata.get("created_at", now()),
            source=metadata.get("source"),
            tags=metadata.get("tags", []),
            embedding=doc.get("embedding"),
            access_count=metadata.get("access_count", 0),
        )
    
    def __str__(self) -> str:
        """简洁字符串表示"""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"MemoryUnit({self.memory_id}, {self.memory_type}, {content_preview})"
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return (
            f"MemoryUnit("
            f"id={self.memory_id}, "
            f"type={self.memory_type}, "
            f"importance={self.importance}, "
            f"content='{self.content[:30]}...'"
            f")"
        )


if __name__ == "__main__":
    # 简单测试
    print("MemoryUnit 基础测试:\n")
    
    # 1. 创建有效记忆
    memory = MemoryUnit(
        content="安哥喜欢喝咖啡，每天早上必须一杯美式",
        memory_type="preference",
        importance=4.5,
        tags=["咖啡", "习惯", "安哥"]
    )
    print(f"1. 创建记忆: {memory}")
    print(f"   ID: {memory.memory_id}")
    print(f"   创建时间: {memory.created_at}")
    
    # 2. 更新访问
    memory.update_access()
    print(f"\n2. 更新访问: 次数={memory.access_count}, 最后访问={memory.last_accessed_at}")
    
    # 3. 转换为 ChromaDB 格式
    chroma_doc = memory.to_chroma_document()
    print(f"\n3. ChromaDB格式:\n   {chroma_doc}")
    
    # 4. 从 ChromaDB 重建
    restored = MemoryUnit.from_chroma_document(chroma_doc)
    print(f"\n4. 重建记忆: {restored}")
    
    # 5. 验证错误处理
    print("\n5. 错误处理测试:")
    try:
        bad_memory = MemoryUnit(content="", memory_type="invalid", importance=10)
    except Exception as e:
        print(f"   ✅ 捕获错误: {type(e).__name__}")
