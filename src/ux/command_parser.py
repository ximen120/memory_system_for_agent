# -*- coding: utf-8 -*-
"""
自然语言命令解析器

识别"记住/忘掉/查找..."等自然语言命令，提取命令类型和参数。
M6傻瓜层核心组件 - 让用户用自然语言与记忆系统交互。

功能特性:
- 识别多种命令类型（记住/忘掉/查找/显示）
- 提取命令参数（内容、标签、时间等）
- 支持模糊匹配和容错
- 支持复合命令

Author: 安仔
Date: 2024
"""

import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from difflib import SequenceMatcher


class CommandType(Enum):
    """命令类型枚举"""
    REMEMBER = "remember"      # 记住/保存
    FORGET = "forget"          # 忘掉/删除
    SEARCH = "search"          # 查找/搜索
    SHOW = "show"              # 显示/列出
    UPDATE = "update"          # 更新/修改
    TAG = "tag"                # 标签管理
    UNKNOWN = "unknown"        # 未知命令


@dataclass
class ParsedCommand:
    """解析后的命令"""
    raw_text: str                      # 原始文本
    command_type: CommandType          # 命令类型
    content: Optional[str] = None      # 内容参数
    tags: List[str] = field(default_factory=list)  # 标签参数
    memory_type: Optional[str] = None  # 记忆类型
    time_constraint: Optional[str] = None  # 时间约束
    confidence: float = 0.0            # 解析置信度
    suggestions: List[str] = field(default_factory=list)  # 建议


class CommandParser:
    """
    自然语言命令解析器
    
    将用户的自然语言输入解析为结构化命令，支持模糊匹配和容错。
    
    Attributes:
        command_patterns: 命令模式字典
        fuzzy_threshold: 模糊匹配阈值
    """
    
    # 命令关键词映射
    COMMAND_KEYWORDS = {
        CommandType.REMEMBER: [
            "记住", "记得", "记录", "保存", "记下", "别忘了",
            "remember", "save", "record", "note"
        ],
        CommandType.FORGET: [
            "忘掉", "忘记", "删除", "移除", "去掉", "清空",
            "forget", "delete", "remove", "clear"
        ],
        CommandType.SEARCH: [
            "查找", "搜索", "查询", "找一下", "找找", "搜一下",
            "search", "find", "lookup", "query"
        ],
        CommandType.SHOW: [
            "显示", "列出", "查看", "展示", "看看", "浏览",
            "show", "list", "display", "view", "browse"
        ],
        CommandType.UPDATE: [
            "更新", "修改", "编辑", "改动", "调整",
            "update", "edit", "modify", "change"
        ],
        CommandType.TAG: [
            "标签", "分类", "标记", "打标签",
            "tag", "label", "categorize"
        ],
    }
    
    # 记忆类型关键词
    MEMORY_TYPE_KEYWORDS = {
        "fact": ["事实", "信息", "知识"],
        "preference": ["喜好", "偏好", "喜欢", "讨厌"],
        "task": ["任务", "待办", "计划", "安排"],
        "event": ["事件", "经历", "活动"],
        "goal": ["目标", "愿望", "梦想", "计划"],
        "context": ["上下文", "背景", "环境"],
    }
    
    # 时间约束关键词
    TIME_KEYWORDS = {
        "today": ["今天", "今日"],
        "yesterday": ["昨天", "昨日"],
        "this_week": ["本周", "这周", "最近一周"],
        "this_month": ["本月", "这个月"],
        "recent": ["最近", "近期", "前不久"],
    }
    
    def __init__(self, fuzzy_threshold: float = 0.6):
        """
        初始化命令解析器
        
        Args:
            fuzzy_threshold: 模糊匹配阈值（0-1）
        """
        self.fuzzy_threshold = fuzzy_threshold
        print(f"[CommandParser] 初始化完成")
        print(f"  - 模糊匹配阈值: {fuzzy_threshold}")
        print(f"  - 支持命令数: {len(self.COMMAND_KEYWORDS)}")
    
    def parse(self, text: str) -> ParsedCommand:
        """
        解析自然语言命令
        
        Args:
            text: 用户输入文本
            
        Returns:
            ParsedCommand: 解析后的命令对象
        """
        if not text or not text.strip():
            return ParsedCommand(
                raw_text=text,
                command_type=CommandType.UNKNOWN,
                confidence=0.0
            )
        
        text = text.strip()
        
        # 1. 识别命令类型
        cmd_type, confidence = self._extract_command_type(text)
        
        # 2. 提取参数
        content = self._extract_content(text, cmd_type)
        tags = self._extract_tags(text)
        memory_type = self._extract_memory_type(text)
        time_constraint = self._extract_time_constraint(text)
        
        # 3. 生成建议
        suggestions = self._generate_suggestions(text, cmd_type, confidence)
        
        return ParsedCommand(
            raw_text=text,
            command_type=cmd_type,
            content=content,
            tags=tags,
            memory_type=memory_type,
            time_constraint=time_constraint,
            confidence=confidence,
            suggestions=suggestions
        )
    
    def _extract_command_type(self, text: str) -> Tuple[CommandType, float]:
        """提取命令类型"""
        text_lower = text.lower()
        best_match = CommandType.UNKNOWN
        best_score = 0.0
        
        for cmd_type, keywords in self.COMMAND_KEYWORDS.items():
            for keyword in keywords:
                # 精确匹配
                if keyword in text_lower:
                    score = 1.0
                    if score > best_score:
                        best_score = score
                        best_match = cmd_type
                
                # 模糊匹配
                if best_score < 1.0:
                    similarity = SequenceMatcher(None, keyword, text_lower[:len(keyword) + 5]).ratio()
                    if similarity > self.fuzzy_threshold and similarity > best_score:
                        best_score = similarity * 0.8  # 模糊匹配降低置信度
                        best_match = cmd_type
        
        return best_match, best_score
    
    def _extract_content(self, text: str, cmd_type: CommandType) -> Optional[str]:
        """提取内容参数"""
        # 移除命令词
        content = text
        
        # 获取该命令类型的所有关键词
        cmd_keywords = self.COMMAND_KEYWORDS.get(cmd_type, [])
        
        for keyword in cmd_keywords:
            if keyword in content.lower():
                # 找到命令词位置，移除它
                idx = content.lower().find(keyword)
                if idx >= 0:
                    content = content[:idx] + content[idx + len(keyword):]
        
        # 清理
        content = content.strip()
        
        # 移除常见连接词
        content = re.sub(r'^[，,\s]*', '', content)
        content = re.sub(r'^[是\s]*', '', content)
        
        return content if content else None
    
    def _extract_tags(self, text: str) -> List[str]:
        """提取标签参数"""
        tags = []
        
        # 匹配"标签: xxx"或"#xxx"格式
        tag_patterns = [
            r'标签[：:]\s*([^，,。]+)',
            r'#([^\s#，,。]+)',
            r'\[([^\]]+)\]',
        ]
        
        for pattern in tag_patterns:
            matches = re.findall(pattern, text)
            tags.extend(matches)
        
        # 清理
        tags = [t.strip() for t in tags if t.strip()]
        
        return list(set(tags))  # 去重
    
    def _extract_memory_type(self, text: str) -> Optional[str]:
        """提取记忆类型"""
        text_lower = text.lower()
        
        for mem_type, keywords in self.MEMORY_TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return mem_type
        
        return None
    
    def _extract_time_constraint(self, text: str) -> Optional[str]:
        """提取时间约束"""
        text_lower = text.lower()
        
        for time_key, keywords in self.TIME_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return time_key
        
        return None
    
    def _generate_suggestions(
        self,
        text: str,
        cmd_type: CommandType,
        confidence: float
    ) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if confidence < 0.5:
            suggestions.append("命令识别置信度较低，请使用更明确的命令词")
        
        if cmd_type == CommandType.UNKNOWN:
            suggestions.append("支持的命令：记住/忘掉/查找/显示/更新/标签")
        
        if cmd_type == CommandType.REMEMBER and not self._extract_content(text, cmd_type):
            suggestions.append("请提供要记住的内容，例如：'记住我喜欢喝咖啡'")
        
        if cmd_type == CommandType.SEARCH and not self._extract_content(text, cmd_type):
            suggestions.append("请提供搜索关键词，例如：'查找关于工作的记忆'")
        
        return suggestions
    
    def is_command(self, text: str, min_confidence: float = 0.5) -> bool:
        """
        判断文本是否为命令
        
        Args:
            text: 输入文本
            min_confidence: 最小置信度
            
        Returns:
            bool: 是否为命令
        """
        parsed = self.parse(text)
        return parsed.command_type != CommandType.UNKNOWN and parsed.confidence >= min_confidence
    
    def batch_parse(self, texts: List[str]) -> List[ParsedCommand]:
        """批量解析"""
        return [self.parse(text) for text in texts]
    
    def get_command_help(self) -> str:
        """获取命令帮助信息"""
        help_text = """
支持的命令：

【记住/保存】
  - "记住我喜欢喝咖啡"
  - "保存：下周要开会"
  - "记录 标签:工作 明天交报告"

【忘掉/删除】
  - "忘掉关于咖啡的记忆"
  - "删除标签:临时的所有记忆"
  - "清空今天的记录"

【查找/搜索】
  - "查找关于工作的记忆"
  - "搜索标签:重要"
  - "查询类型:任务"

【显示/列出】
  - "显示所有记忆"
  - "列出最近一周的记忆"
  - "查看标签:生活"

【更新/修改】
  - "更新mem_001的内容"
  - "修改关于咖啡的记忆"

【标签管理】
  - "给mem_001打标签:重要"
  - "标签 工作 添加到昨天的记忆"

提示：
- 可以使用标签筛选：标签:工作
- 可以使用时间筛选：今天/昨天/本周
- 可以使用类型筛选：类型:任务
"""
        return help_text.strip()


# ========== 测试代码 ==========

def test_command_parser():
    """测试命令解析器"""
    print("\n" + "=" * 60)
    print("CommandParser 模块测试")
    print("=" * 60)
    
    parser = CommandParser()
    
    # 测试用例
    test_cases = [
        # 记住命令
        "记住我喜欢喝美式咖啡",
        "保存：下周三要参加项目评审会议",
        "记录 标签:工作 明天交报告",
        
        # 忘掉命令
        "忘掉关于咖啡的记忆",
        "删除标签:临时的所有记忆",
        
        # 查找命令
        "查找关于工作的记忆",
        "搜索标签:重要",
        "查询类型:任务",
        
        # 显示命令
        "显示所有记忆",
        "列出最近一周的记忆",
        
        # 更新命令
        "更新mem_001的内容",
        
        # 标签命令
        "给mem_001打标签:重要",
        
        # 模糊匹配
        "记主我喜欢喝咖啡",  # 错别字
        "查找关于工作的",     # 不完整
        
        # 非命令
        "今天天气不错",
        "你好",
    ]
    
    print("\n1. 单条命令解析测试")
    print("-" * 60)
    
    for text in test_cases:
        result = parser.parse(text)
        
        print(f"\n输入: {text}")
        print(f"  命令类型: {result.command_type.value}")
        print(f"  置信度: {result.confidence:.2f}")
        print(f"  内容: {result.content}")
        print(f"  标签: {result.tags}")
        print(f"  记忆类型: {result.memory_type}")
        print(f"  时间约束: {result.time_constraint}")
        
        if result.suggestions:
            print(f"  建议: {result.suggestions}")
    
    # 测试2: 批量解析
    print("\n2. 批量解析测试")
    print("-" * 60)
    
    batch_results = parser.batch_parse(test_cases[:5])
    print(f"批量解析 {len(batch_results)} 条命令")
    
    for result in batch_results:
        print(f"  [{result.command_type.value}] {result.raw_text[:20]}...")
    
    # 测试3: 命令判断
    print("\n3. 命令判断测试")
    print("-" * 60)
    
    for text in ["记住xxx", "今天天气", "查找yyy", "你好"]:
        is_cmd = parser.is_command(text)
        print(f"  '{text}' -> {'是命令' if is_cmd else '不是命令'}")
    
    # 测试4: 帮助信息
    print("\n4. 帮助信息")
    print("-" * 60)
    print(parser.get_command_help())
    
    # 最终报告
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_command_parser()
