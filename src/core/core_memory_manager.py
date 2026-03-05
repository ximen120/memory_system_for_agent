"""
核心记忆管理器 - 专门处理 CORE-*.md 文件

用于自动加载最近更新的核心记忆文件。
"""

import os
import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CoreMemory:
    """核心记忆数据结构"""
    file_path: str
    file_name: str
    memory_id: str
    title: str
    modified_time: datetime
    formatted_date: str
    content: Optional[str] = None


class CoreMemoryManager:
    """
    核心记忆管理器
    
    专门用于读取和管理 CORE-*.md 格式的核心记忆文件。
    """
    
    # tier到目录的映射
    TIER_DIRS = {
        "core": "core",
        "principles": "principles",
        "quotes": "quotes"
    }
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化核心记忆管理器
        
        Args:
            base_path: 基础路径，默认从环境变量 MEMORY_CORE_PATH 读取，
                      或者使用默认路径 "D:/AnZai_JieYue/memory"
        """
        self.base_path = self._resolve_base_path(base_path)
        logger.info(f"CoreMemoryManager 初始化: base_path={self.base_path}")
    
    def _resolve_base_path(self, base_path: Optional[str]) -> Path:
        """
        解析基础路径
        
        Args:
            base_path: 用户指定的基础路径
            
        Returns:
            解析后的 Path 对象
        """
        if base_path:
            return Path(base_path)
        
        # 优先从环境变量读取
        env_path = os.getenv("MEMORY_CORE_PATH")
        if env_path:
            return Path(env_path)
        
        # 默认路径
        default_path = Path("D:/AnZai_JieYue/memory")
        return default_path
    
    def _get_dir_for_tier(self, tier: Optional[str]) -> List[Path]:
        """
        获取指定tier对应的目录列表
        
        Args:
            tier: 记忆层级，None表示全部层级
            
        Returns:
            目录列表
        """
        if tier is None:
            # 返回所有层级的目录
            return [
                self.base_path / dir_name 
                for dir_name in self.TIER_DIRS.values()
            ]
        
        # 返回指定层级的目录
        dir_name = self.TIER_DIRS.get(tier, "core")
        return [self.base_path / dir_name]
    
    def _extract_title_from_file(self, file_path: Path) -> str:
        """
        从文件中提取标题
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取的标题
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('# '):
                        return line[2:].strip()
        except Exception as e:
            logger.warning(f"读取文件 {file_path} 提取标题失败: {e}")
        
        # 如果无法从文件中提取，使用文件名（去掉扩展名）
        return file_path.stem
    
    def _format_date(self, dt: datetime) -> str:
        """
        格式化日期为 "3月2日" 格式
        
        Args:
            dt: datetime对象
            
        Returns:
            格式化的日期字符串
        """
        return f"{dt.month}月{dt.day}日"
    
    def _parse_core_file(self, file_path: Path) -> Optional[CoreMemory]:
        """
        解析单个CORE-*.md文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            CoreMemory对象，解析失败返回None
        """
        try:
            stat = file_path.stat()
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            
            title = self._extract_title_from_file(file_path)
            memory_id = file_path.stem
            
            return CoreMemory(
                file_path=str(file_path),
                file_name=file_path.name,
                memory_id=memory_id,
                title=title,
                modified_time=modified_time,
                formatted_date=self._format_date(modified_time)
            )
        except Exception as e:
            logger.warning(f"解析文件 {file_path} 失败: {e}")
            return None
    
    def get_recent_memories(
        self,
        limit: int = 5,
        tier: Optional[str] = None
    ) -> List[CoreMemory]:
        """
        获取最近更新的核心记忆
        
        Args:
            limit: 返回数量，默认5条
            tier: 记忆层级，None表示全部层级
            
        Returns:
            按修改时间倒序的CoreMemory列表
        """
        all_memories: List[CoreMemory] = []
        
        # 获取要扫描的目录列表
        dirs_to_scan = self._get_dir_for_tier(tier)
        
        for dir_path in dirs_to_scan:
            if not dir_path.exists():
                logger.warning(f"目录不存在: {dir_path}")
                continue
            
            # 扫描目录中的所有.md文件
            for file_path in dir_path.glob("*.md"):
                # 只处理CORE-开头的文件（如果是core层级）
                if tier == "core" and not file_path.name.startswith("CORE-"):
                    continue
                
                # 解析文件
                memory = self._parse_core_file(file_path)
                if memory:
                    all_memories.append(memory)
        
        # 按修改时间倒序排序
        all_memories.sort(
            key=lambda m: m.modified_time,
            reverse=True
        )
        
        # 取前limit条
        return all_memories[:limit]
    
    def format_markdown(self, memories: List[CoreMemory]) -> str:
        """
        格式化为markdown输出
        
        Args:
            memories: CoreMemory列表
            
        Returns:
            markdown格式的字符串
        """
        if not memories:
            return "已自动加载上下文：\n\n暂无核心记忆\n\n---\n安哥，已准备好继续。"
        
        lines = []
        lines.append("已自动加载上下文：")
        lines.append("")
        lines.append("【核心记忆】（最近更新）")
        
        for i, memory in enumerate(memories, 1):
            lines.append(f"{i}. [{memory.memory_id}] {memory.title}（{memory.formatted_date}）")
        
        lines.append("")
        lines.append("---")
        lines.append("安哥，已准备好继续。")
        
        return "\n".join(lines)
    
    def format_json(self, memories: List[CoreMemory]) -> str:
        """
        格式化为json输出
        
        Args:
            memories: CoreMemory列表
            
        Returns:
            json格式的字符串
        """
        data = {
            "memories": [
                {
                    "memory_id": m.memory_id,
                    "title": m.title,
                    "file_name": m.file_name,
                    "file_path": m.file_path,
                    "modified_time": m.modified_time.isoformat(),
                    "formatted_date": m.formatted_date
                }
                for m in memories
            ],
            "count": len(memories)
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
