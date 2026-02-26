# -*- coding: utf-8 -*-
"""
标签管理器

实现标签系统的核心功能：
1. 自动提取关键词作为标签
2. 手动添加/删除标签
3. 按标签筛选记忆
4. 标签统计和推荐

M6傻瓜层 - 用户无需手动管理标签
"""

import re
from typing import List, Dict, Any, Optional, Set
from collections import Counter
from dataclasses import dataclass


@dataclass
class TagInfo:
    """标签信息"""
    name: str
    count: int
    category: Optional[str] = None
    description: Optional[str] = None


class TagManager:
    """
    标签管理器
    
    自动为记忆生成标签，支持手动管理，提供筛选功能。
    
    Attributes:
        predefined_tags: 预定义标签库
        auto_extract_enabled: 是否启用自动提取
        min_tag_length: 标签最小长度
        max_tags_per_memory: 每条记忆最大标签数
    """
    
    # 预定义标签分类
    PREDEFINED_TAGS = {
        "工作": {"category": "领域", "keywords": ["工作", "项目", "会议", "报告", "客户", "同事"]},
        "生活": {"category": "领域", "keywords": ["生活", "家庭", "朋友", "日常", "购物"]},
        "学习": {"category": "领域", "keywords": ["学习", "课程", "读书", "知识", "技能"]},
        "重要": {"category": "优先级", "keywords": ["重要", "关键", "紧急", "必须", "一定"]},
        "待办": {"category": "状态", "keywords": ["待办", "待处理", "计划", "安排", "准备"]},
        "喜好": {"category": "偏好", "keywords": ["喜欢", "爱好", "偏好", "习惯", "想要"]},
        "目标": {"category": "规划", "keywords": ["目标", "计划", "梦想", "愿望", "期望"]},
        "人": {"category": "实体", "keywords": ["人", "朋友", "同事", "家人", "客户"]},
        "地点": {"category": "实体", "keywords": ["地点", "地方", "城市", "公司", "家"]},
        "时间": {"category": "实体", "keywords": ["时间", "日期", "明天", "下周", "下个月"]},
    }
    
    # 停用词
    STOP_WORDS = {
        "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也",
        "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这", "那",
        "啊", "呢", "吧", "吗", "哦", "嗯", "这个", "那个", "什么", "怎么", "为什么", "如何",
    }
    
    def __init__(
        self,
        auto_extract_enabled: bool = True,
        min_tag_length: int = 2,
        max_tags_per_memory: int = 5,
        use_predefined: bool = True
    ):
        """
        初始化标签管理器
        
        Args:
            auto_extract_enabled: 是否启用自动提取
            min_tag_length: 标签最小长度
            max_tags_per_memory: 每条记忆最大标签数
            use_predefined: 是否使用预定义标签
        """
        self.auto_extract_enabled = auto_extract_enabled
        self.min_tag_length = min_tag_length
        self.max_tags_per_memory = max_tags_per_memory
        self.use_predefined = use_predefined
        
        # 标签统计
        self.tag_stats: Dict[str, int] = {}
        
        print(f"[TagManager] 初始化完成")
        print(f"  - 自动提取: {'开启' if auto_extract_enabled else '关闭'}")
        print(f"  - 预定义标签: {len(self.PREDEFINED_TAGS)} 个")
    
    def extract_tags(self, content: str, existing_tags: Optional[List[str]] = None) -> List[str]:
        """
        从内容中提取标签
        
        Args:
            content: 记忆内容
            existing_tags: 已有标签（会保留）
            
        Returns:
            List[str]: 标签列表
        """
        tags = set(existing_tags or [])
        
        if not self.auto_extract_enabled:
            return list(tags)[:self.max_tags_per_memory]
        
        # 1. 匹配预定义标签
        if self.use_predefined:
            predefined = self._match_predefined_tags(content)
            tags.update(predefined)
        
        # 2. 提取关键词
        keywords = self._extract_keywords(content)
        tags.update(keywords)
        
        # 3. 按优先级排序并限制数量
        sorted_tags = self._sort_tags_by_priority(list(tags), content)
        
        return sorted_tags[:self.max_tags_per_memory]
    
    def _match_predefined_tags(self, content: str) -> Set[str]:
        """匹配预定义标签"""
        matched = set()
        content_lower = content.lower()
        
        for tag, info in self.PREDEFINED_TAGS.items():
            for keyword in info["keywords"]:
                if keyword in content_lower:
                    matched.add(tag)
                    break
        
        return matched
    
    def _extract_keywords(self, content: str) -> Set[str]:
        """提取关键词"""
        keywords = set()
        
        # 简单分词（基于规则）
        # 提取2-4字词组
        for length in range(4, self.min_tag_length - 1, -1):
            for i in range(len(content) - length + 1):
                word = content[i:i + length]
                
                # 过滤条件
                if self._is_valid_keyword(word):
                    keywords.add(word)
        
        # 提取命名实体（简单规则）
        # 时间模式
        time_patterns = [
            r'(\d{4}年\d{1,2}月\d{1,2}日)',
            r'(明天|后天|下周|下个月|明年)',
            r'(周一|周二|周三|周四|周五|周六|周日)',
        ]
        for pattern in time_patterns:
            matches = re.findall(pattern, content)
            keywords.update(matches)
        
        return keywords
    
    def _is_valid_keyword(self, word: str) -> bool:
        """判断是否为有效关键词"""
        # 长度检查
        if len(word) < self.min_tag_length:
            return False
        
        # 停用词检查
        if word in self.STOP_WORDS:
            return False
        
        # 纯数字检查
        if word.isdigit():
            return False
        
        # 纯英文检查（允许中英文混合）
        if word.isalpha() and word.isascii():
            return False
        
        return True
    
    def _sort_tags_by_priority(self, tags: List[str], content: str) -> List[str]:
        """按优先级排序标签"""
        def get_priority(tag):
            # 预定义标签优先级最高
            if tag in self.PREDEFINED_TAGS:
                return (0, -self.PREDEFINED_TAGS[tag]["keywords"].index(next(
                    (k for k in self.PREDEFINED_TAGS[tag]["keywords"] if k in content.lower()),
                    ""
                )) if any(k in content.lower() for k in self.PREDEFINED_TAGS[tag]["keywords"]) else 0)
            
            # 统计频率作为次要排序依据
            count = content.count(tag)
            return (1, -count)
        
        return sorted(tags, key=get_priority)
    
    def add_tag(self, memory_id: str, tag: str, memories: Dict[str, Any]) -> bool:
        """
        手动添加标签
        
        Args:
            memory_id: 记忆ID
            tag: 标签名称
            memories: 记忆存储字典
            
        Returns:
            bool: 是否成功
        """
        if memory_id not in memories:
            return False
        
        memory = memories[memory_id]
        if "tags" not in memory:
            memory["tags"] = []
        
        tag = tag.strip()
        if tag and tag not in memory["tags"]:
            memory["tags"].append(tag)
            
            # 更新统计
            self.tag_stats[tag] = self.tag_stats.get(tag, 0) + 1
            
            return True
        
        return False
    
    def remove_tag(self, memory_id: str, tag: str, memories: Dict[str, Any]) -> bool:
        """
        移除标签
        
        Args:
            memory_id: 记忆ID
            tag: 标签名称
            memories: 记忆存储字典
            
        Returns:
            bool: 是否成功
        """
        if memory_id not in memories:
            return False
        
        memory = memories[memory_id]
        if "tags" in memory and tag in memory["tags"]:
            memory["tags"].remove(tag)
            
            # 更新统计
            if tag in self.tag_stats:
                self.tag_stats[tag] = max(0, self.tag_stats[tag] - 1)
            
            return True
        
        return False
    
    def filter_by_tags(
        self,
        memories: List[Dict[str, Any]],
        tags: List[str],
        match_all: bool = False
    ) -> List[Dict[str, Any]]:
        """
        按标签筛选记忆
        
        Args:
            memories: 记忆列表
            tags: 要筛选的标签
            match_all: 是否要求匹配所有标签（True=AND，False=OR）
            
        Returns:
            List[Dict]: 筛选后的记忆列表
        """
        if not tags:
            return memories
        
        tags_set = set(t.strip() for t in tags if t.strip())
        filtered = []
        
        for memory in memories:
            memory_tags = set(memory.get("tags", []))
            
            if match_all:
                # AND 模式：包含所有标签
                if tags_set.issubset(memory_tags):
                    filtered.append(memory)
            else:
                # OR 模式：包含任一标签
                if tags_set & memory_tags:
                    filtered.append(memory)
        
        return filtered
    
    def get_all_tags(self, memories: List[Dict[str, Any]]) -> List[TagInfo]:
        """
        获取所有标签统计
        
        Args:
            memories: 记忆列表
            
        Returns:
            List[TagInfo]: 标签信息列表
        """
        tag_counter = Counter()
        
        for memory in memories:
            for tag in memory.get("tags", []):
                tag_counter[tag] += 1
        
        tag_infos = []
        for tag, count in tag_counter.most_common():
            category = None
            if tag in self.PREDEFINED_TAGS:
                category = self.PREDEFINED_TAGS[tag]["category"]
            
            tag_infos.append(TagInfo(
                name=tag,
                count=count,
                category=category
            ))
        
        return tag_infos
    
    def suggest_tags(self, content: str, top_k: int = 3) -> List[str]:
        """
        为内容推荐标签
        
        Args:
            content: 内容
            top_k: 推荐数量
            
        Returns:
            List[str]: 推荐标签列表
        """
        tags = self.extract_tags(content)
        return tags[:top_k]


# ========== 测试代码 ==========

def test_tag_manager():
    """测试标签管理器"""
    print("\n" + "=" * 60)
    print("TagManager 测试")
    print("=" * 60)
    
    manager = TagManager()
    
    # 测试1: 自动提取标签
    print("\n1. 自动提取标签测试")
    test_contents = [
        "我喜欢喝咖啡，每天早上必须一杯美式咖啡",
        "记住，我下周要参加一个重要会议，需要准备PPT",
        "我的目标是学习Python编程，计划每天练习",
        "今天和朋友去公园散步，天气很好",
    ]
    
    for content in test_contents:
        tags = manager.extract_tags(content)
        print(f"\n内容: {content}")
        print(f"标签: {tags}")
    
    # 测试2: 手动添加标签
    print("\n2. 手动添加标签测试")
    memories = {
        "mem_001": {"content": "测试内容", "tags": []},
        "mem_002": {"content": "另一个测试", "tags": ["工作"]},
    }
    
    manager.add_tag("mem_001", "重要", memories)
    manager.add_tag("mem_001", "待办", memories)
    manager.add_tag("mem_002", "紧急", memories)
    
    print(f"mem_001 标签: {memories['mem_001']['tags']}")
    print(f"mem_002 标签: {memories['mem_002']['tags']}")
    
    # 测试3: 按标签筛选
    print("\n3. 按标签筛选测试")
    memory_list = list(memories.values())
    
    filtered = manager.filter_by_tags(memory_list, ["重要"])
    print(f"筛选'重要': {len(filtered)} 条")
    
    filtered = manager.filter_by_tags(memory_list, ["工作"])
    print(f"筛选'工作': {len(filtered)} 条")
    
    # 测试4: 标签统计
    print("\n4. 标签统计")
    tag_infos = manager.get_all_tags(memory_list)
    for info in tag_infos:
        print(f"  {info.name}: {info.count} 次")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_tag_manager()
