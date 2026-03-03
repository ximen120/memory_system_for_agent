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
    
    @field_validator('memory_type', mode='before')
    @classmethod
    def validate_memory_type(cls, v) -> str:
        """验证记忆类型（宽容模式）"""
        valid_types = {'fact', 'preference', 'context', 'task', 'event'}
        if not v or v not in valid_types:
            return "fact"
        return v
    
    @field_validator('content', mode='before')
    @classmethod
    def validate_content_not_empty(cls, v) -> str:
        """验证内容不为空（宽容模式）"""
        if not v or not str(v).strip():
            return "[空记忆]"
        return str(v).strip()
    
    @field_validator('importance', mode='before')
    @classmethod
    def validate_importance(cls, v) -> float:
        """验证重要性（宽容模式）"""
        if v is None:
            return 3.0
        try:
            importance = float(v)
            if importance < 1.0:
                return 1.0
            if importance > 5.0:
                return 5.0
            return importance
        except (ValueError, TypeError):
            return 3.0
    
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
            ChromaDB 兼容的文档字典
        """
        metadata = {
            "memory_type": self.memory_type,
            "importance": self.importance,
            "created_at": self.created_at,
            "source": self.source or "",
            "tags": ",".join(self.tags),
            "access_count": self.access_count,
        }
        
        if self.updated_at:
            metadata["updated_at"] = self.updated_at
        if self.last_accessed_at:
            metadata["last_accessed_at"] = self.last_accessed_at
        
        return {
            "id": self.memory_id,
            "document": self.content,
            "metadata": metadata,
            "embedding": self.embedding
        }
    
    @classmethod
    def from_chroma_result(cls, result: Dict[str, Any]) -> "MemoryUnit":
        """
        从 ChromaDB 查询结果创建 MemoryUnit
        
        Args:
            result: ChromaDB 返回的结果字典
        """
        metadata = result.get("metadata", {})
        tags_str = metadata.get("tags", "")
        tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
        
        return cls(
            memory_id=result.get("id", ""),
            content=result.get("document", ""),
            memory_type=metadata.get("memory_type", "fact"),
            importance=metadata.get("importance", 3.0),
            created_at=metadata.get("created_at", now()),
            updated_at=metadata.get("updated_at"),
            source=metadata.get("source") or None,
            tags=tags,
            access_count=metadata.get("access_count", 0),
            last_accessed_at=metadata.get("last_accessed_at"),
        )
    
    @classmethod
    def from_legacy_dict(cls, data: dict) -> "MemoryUnit":
        """从旧格式数据创建MemoryUnit，自动修正不合规字段"""
        # 过滤掉MemoryUnit不认识的字段
        valid_fields = cls.model_fields.keys()
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        
        return cls(**filtered)
    
    def __repr__(self) -> str:
        return (
            f"MemoryUnit(id={self.memory_id!r}, "
            f"type={self.memory_type!r}, "
            f"importance={self.importance}, "
            f"content={self.content[:50]!r}...)"
        )
