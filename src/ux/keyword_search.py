# -*- coding: utf-8 -*-
"""
关键词检索模块

基于JSON存储实现文本搜索，不依赖向量检索。
M6傻瓜层核心组件 - 提供快速、简单的记忆检索功能。

功能特性:
- 多关键词组合搜索（AND/OR模式）
- 支持内容、标签、类型字段搜索
- 支持模糊匹配
- 结果排序（相关性、时间）

Author: 安仔
Date: 2024
"""

import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher


@dataclass
class SearchResult:
    """搜索结果"""
    memory: Dict[str, Any]
    score: float  # 相关性分数 0-1
    matched_fields: List[str]  # 匹配的字段
    highlights: Dict[str, List[str]]  # 高亮片段


@dataclass
class SearchQuery:
    """搜索查询"""
    keywords: List[str]
    search_fields: List[str]  # 搜索字段: content, tags, type
    match_mode: str  # "AND" 或 "OR"
    fuzzy_match: bool  # 是否启用模糊匹配
    min_score: float  # 最小相关性分数


class KeywordSearch:
    """
    关键词检索器
    
    基于简单文本匹配实现记忆检索，无需向量数据库。
    适合MVP阶段和轻量级应用场景。
    
    Attributes:
        memories: 记忆存储列表
        case_sensitive: 是否区分大小写
        max_results: 最大返回结果数
    """
    
    def __init__(
        self,
        memories: Optional[List[Dict[str, Any]]] = None,
        case_sensitive: bool = False,
        max_results: int = 50
    ):
        """
        初始化关键词检索器
        
        Args:
            memories: 初始记忆列表
            case_sensitive: 是否区分大小写
            max_results: 最大返回结果数
        """
        self.memories = memories or []
        self.case_sensitive = case_sensitive
        self.max_results = max_results
        
        print(f"[KeywordSearch] 初始化完成")
        print(f"  - 记忆数量: {len(self.memories)}")
        print(f"  - 区分大小写: {case_sensitive}")
        print(f"  - 最大结果数: {max_results}")
    
    def add_memories(self, memories: List[Dict[str, Any]]) -> None:
        """添加记忆到索引"""
        self.memories.extend(memories)
        print(f"[KeywordSearch] 添加 {len(memories)} 条记忆，当前共 {len(self.memories)} 条")
    
    def search(
        self,
        query: str,
        search_fields: Optional[List[str]] = None,
        match_mode: str = "OR",
        fuzzy_match: bool = False,
        min_score: float = 0.0,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        date_range: Optional[Tuple[str, str]] = None
    ) -> List[SearchResult]:
        """
        主搜索方法
        
        Args:
            query: 搜索关键词（支持空格分隔多个词）
            search_fields: 搜索字段列表 ["content", "tags", "type"]
            match_mode: 匹配模式 "AND" 或 "OR"
            fuzzy_match: 是否启用模糊匹配
            min_score: 最小相关性分数
            memory_type: 按记忆类型过滤
            tags: 按标签过滤
            date_range: 按日期范围过滤 (start, end)
            
        Returns:
            List[SearchResult]: 搜索结果列表，按相关性排序
        """
        # 解析查询
        keywords = self._parse_query(query)
        if not keywords:
            return []
        
        # 默认搜索字段
        if search_fields is None:
            search_fields = ["content", "tags"]
        
        # 构建查询对象
        search_query = SearchQuery(
            keywords=keywords,
            search_fields=search_fields,
            match_mode=match_mode,
            fuzzy_match=fuzzy_match,
            min_score=min_score
        )
        
        # 执行搜索
        results = []
        for memory in self.memories:
            # 前置过滤
            if memory_type and memory.get("memory_type") != memory_type:
                continue
            if tags and not any(tag in memory.get("tags", []) for tag in tags):
                continue
            if date_range and not self._check_date_range(memory, date_range):
                continue
            
            # 计算匹配
            result = self._match_memory(memory, search_query)
            if result and result.score >= min_score:
                results.append(result)
        
        # 排序并限制结果数
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:self.max_results]
    
    def _parse_query(self, query: str) -> List[str]:
        """解析查询字符串"""
        if not query:
            return []
        
        # 分词（支持空格、逗号分隔）
        keywords = re.split(r'[\s,，]+', query.strip())
        
        # 清理并过滤
        keywords = [k.strip() for k in keywords if k.strip()]
        
        if not self.case_sensitive:
            keywords = [k.lower() for k in keywords]
        
        return keywords
    
    def _match_memory(
        self,
        memory: Dict[str, Any],
        query: SearchQuery
    ) -> Optional[SearchResult]:
        """匹配单个记忆"""
        matched_fields = []
        highlights = {}
        total_score = 0.0
        match_count = 0
        
        for keyword in query.keywords:
            keyword_matched = False
            keyword_score = 0.0
            
            for field in query.search_fields:
                field_value = self._get_field_value(memory, field)
                if not field_value:
                    continue
                
                # 执行匹配
                score, matched_texts = self._match_field(
                    keyword, field_value, query.fuzzy_match
                )
                
                if score > 0:
                    keyword_matched = True
                    keyword_score = max(keyword_score, score)
                    if field not in matched_fields:
                        matched_fields.append(field)
                    if field not in highlights:
                        highlights[field] = []
                    highlights[field].extend(matched_texts)
            
            if keyword_matched:
                match_count += 1
                total_score += keyword_score
        
        # 根据匹配模式判断是否命中
        if query.match_mode == "AND" and match_count < len(query.keywords):
            return None
        if query.match_mode == "OR" and match_count == 0:
            return None
        
        # 计算最终分数
        if query.match_mode == "AND":
            final_score = total_score / len(query.keywords) if query.keywords else 0
        else:
            final_score = total_score / match_count if match_count > 0 else 0
        
        return SearchResult(
            memory=memory,
            score=min(final_score, 1.0),
            matched_fields=matched_fields,
            highlights={k: list(set(v))[:3] for k, v in highlights.items()}  # 去重并限制数量
        )
    
    def _get_field_value(self, memory: Dict[str, Any], field: str) -> str:
        """获取字段值并转换为字符串"""
        value = memory.get(field)
        if value is None:
            return ""
        
        if isinstance(value, list):
            return " ".join(str(v) for v in value)
        
        return str(value)
    
    def _match_field(
        self,
        keyword: str,
        field_value: str,
        fuzzy_match: bool
    ) -> Tuple[float, List[str]]:
        """匹配字段值"""
        if not self.case_sensitive:
            field_value_lower = field_value.lower()
        else:
            field_value_lower = field_value
        
        matched_texts = []
        score = 0.0
        
        # 精确匹配
        if keyword in field_value_lower:
            count = field_value_lower.count(keyword)
            score = min(0.3 + count * 0.1, 1.0)  # 基础分 + 频率加分
            
            # 提取匹配片段
            for match in re.finditer(re.escape(keyword), field_value_lower):
                start = max(0, match.start() - 10)
                end = min(len(field_value), match.end() + 10)
                snippet = field_value[start:end]
                matched_texts.append(f"...{snippet}...")
        
        # 模糊匹配
        if fuzzy_match and score < 0.5:
            similarity = SequenceMatcher(None, keyword, field_value_lower).ratio()
            if similarity > 0.6:  # 相似度阈值
                fuzzy_score = similarity * 0.5  # 模糊匹配最高0.5分
                if fuzzy_score > score:
                    score = fuzzy_score
                    matched_texts.append(f"[模糊匹配] {field_value[:30]}...")
        
        return score, matched_texts
    
    def _check_date_range(
        self,
        memory: Dict[str, Any],
        date_range: Tuple[str, str]
    ) -> bool:
        """检查日期范围"""
        created_at = memory.get("created_at")
        if not created_at:
            return False
        
        try:
            start_date = datetime.fromisoformat(date_range[0])
            end_date = datetime.fromisoformat(date_range[1])
            memory_date = datetime.fromisoformat(created_at)
            return start_date <= memory_date <= end_date
        except (ValueError, TypeError):
            return True  # 解析失败时不过滤
    
    def search_by_content(
        self,
        keywords: List[str],
        match_mode: str = "OR"
    ) -> List[SearchResult]:
        """仅搜索内容字段"""
        query = " ".join(keywords)
        return self.search(query, search_fields=["content"], match_mode=match_mode)
    
    def search_by_tags(
        self,
        tags: List[str],
        match_mode: str = "OR"
    ) -> List[SearchResult]:
        """仅搜索标签字段"""
        query = " ".join(tags)
        return self.search(query, search_fields=["tags"], match_mode=match_mode)
    
    def search_by_type(self, memory_type: str) -> List[SearchResult]:
        """按类型搜索"""
        results = []
        for memory in self.memories:
            if memory.get("memory_type") == memory_type:
                results.append(SearchResult(
                    memory=memory,
                    score=1.0,
                    matched_fields=["type"],
                    highlights={}
                ))
        return results
    
    def get_all_tags(self) -> Dict[str, int]:
        """获取所有标签统计"""
        tag_count = {}
        for memory in self.memories:
            for tag in memory.get("tags", []):
                tag_count[tag] = tag_count.get(tag, 0) + 1
        return dict(sorted(tag_count.items(), key=lambda x: x[1], reverse=True))
    
    def get_timeline(self) -> List[Dict[str, Any]]:
        """获取时间线"""
        timeline = []
        for memory in sorted(
            self.memories,
            key=lambda x: x.get("created_at", ""),
            reverse=True
        ):
            timeline.append({
                "id": memory.get("memory_id"),
                "content": memory.get("content", "")[:100],
                "type": memory.get("memory_type"),
                "created_at": memory.get("created_at"),
                "tags": memory.get("tags", [])
            })
        return timeline


# ========== 测试代码 ==========

def test_keyword_search():
    """测试关键词检索模块"""
    print("\n" + "=" * 60)
    print("KeywordSearch 模块测试")
    print("=" * 60)
    
    # 准备测试数据
    test_memories = [
        {
            "memory_id": "mem_001",
            "content": "我喜欢喝美式咖啡，每天早上必须一杯",
            "memory_type": "preference",
            "tags": ["喜好", "咖啡", "生活"],
            "created_at": "2024-01-15T08:00:00",
            "importance": 3.5
        },
        {
            "memory_id": "mem_002",
            "content": "下周三要参加项目评审会议，需要准备PPT",
            "memory_type": "task",
            "tags": ["工作", "会议", "重要"],
            "created_at": "2024-01-16T09:30:00",
            "importance": 4.5
        },
        {
            "memory_id": "mem_003",
            "content": "我的目标是学习Python编程，计划每天练习",
            "memory_type": "goal",
            "tags": ["目标", "学习", "Python"],
            "created_at": "2024-01-17T10:00:00",
            "importance": 4.0
        },
        {
            "memory_id": "mem_004",
            "content": "今天和朋友去公园散步，天气很好",
            "memory_type": "event",
            "tags": ["生活", "朋友", "休闲"],
            "created_at": "2024-01-18T15:00:00",
            "importance": 2.5
        },
        {
            "memory_id": "mem_005",
            "content": "记住：客户要求下周交付产品原型",
            "memory_type": "task",
            "tags": ["工作", "客户", "紧急"],
            "created_at": "2024-01-19T11:00:00",
            "importance": 5.0
        },
    ]
    
    # 创建检索器
    searcher = KeywordSearch(memories=test_memories)
    
    # 测试1: 单关键词搜索
    print("\n1. 单关键词搜索")
    print("-" * 60)
    
    results = searcher.search("咖啡")
    print(f"搜索'咖啡': {len(results)} 条结果")
    for r in results:
        print(f"  [{r.score:.2f}] {r.memory['content'][:40]}...")
    
    # 测试2: 多关键词OR搜索
    print("\n2. 多关键词OR搜索")
    print("-" * 60)
    
    results = searcher.search("工作 学习", match_mode="OR")
    print(f"搜索'工作 OR 学习': {len(results)} 条结果")
    for r in results:
        print(f"  [{r.score:.2f}] {r.memory['content'][:40]}...")
    
    # 测试3: 多关键词AND搜索
    print("\n3. 多关键词AND搜索")
    print("-" * 60)
    
    results = searcher.search("项目 会议", match_mode="AND")
    print(f"搜索'项目 AND 会议': {len(results)} 条结果")
    for r in results:
        print(f"  [{r.score:.2f}] {r.memory['content'][:40]}...")
    
    # 测试4: 标签搜索
    print("\n4. 标签搜索")
    print("-" * 60)
    
    results = searcher.search("重要", search_fields=["tags"])
    print(f"标签搜索'重要': {len(results)} 条结果")
    for r in results:
        print(f"  [{r.score:.2f}] {r.memory['content'][:40]}...")
    
    # 测试5: 类型过滤
    print("\n5. 类型过滤")
    print("-" * 60)
    
    results = searcher.search("", memory_type="task")
    print(f"类型'task': {len(results)} 条结果")
    for r in results:
        print(f"  {r.memory['content'][:40]}...")
    
    # 测试6: 模糊匹配
    print("\n6. 模糊匹配")
    print("-" * 60)
    
    results = searcher.search("Pyton", fuzzy_match=True)  # 拼写错误
    print(f"模糊搜索'Pyton': {len(results)} 条结果")
    for r in results:
        print(f"  [{r.score:.2f}] {r.memory['content'][:40]}...")
    
    # 测试7: 获取所有标签
    print("\n7. 标签统计")
    print("-" * 60)
    
    tags = searcher.get_all_tags()
    print(f"共 {len(tags)} 个标签:")
    for tag, count in list(tags.items())[:5]:
        print(f"  {tag}: {count} 次")
    
    # 测试8: 时间线
    print("\n8. 时间线浏览")
    print("-" * 60)
    
    timeline = searcher.get_timeline()
    print(f"共 {len(timeline)} 条记忆:")
    for item in timeline[:3]:
        print(f"  [{item['created_at'][:10]}] {item['content'][:30]}...")
    
    # 最终报告
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_keyword_search()
