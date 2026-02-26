# -*- coding: utf-8 -*-
"""
时间线浏览模块

按时间顺序查看和管理记忆，支持多种筛选和可视化展示。
M6傻瓜层核心组件 - 提供直观的时间轴浏览体验。

功能特性:
- 按时间顺序查看记忆
- 支持时间范围筛选（今天/本周/本月/自定义）
- 支持按记忆类型筛选
- 时间轴可视化展示
- 点击查看详情

Author: 安仔
Date: 2024
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict


class TimeRange(Enum):
    """时间范围枚举"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    ALL = "all"


@dataclass
class TimelineItem:
    """时间线项目"""
    memory_id: str
    content: str
    memory_type: str
    created_at: datetime
    tags: List[str] = field(default_factory=list)
    importance: float = 3.0
    day_key: str = ""  # 用于分组，如 "2024-01-15"
    
    def __post_init__(self):
        if not self.day_key and self.created_at:
            self.day_key = self.created_at.strftime("%Y-%m-%d")


@dataclass
class TimelineGroup:
    """时间线分组（按天）"""
    date: str
    items: List[TimelineItem] = field(default_factory=list)
    count: int = 0
    
    def __post_init__(self):
        self.count = len(self.items)


@dataclass
class TimelineStatistics:
    """时间线统计信息"""
    total_count: int
    date_range: Tuple[str, str]
    type_distribution: Dict[str, int]
    tag_distribution: Dict[str, int]
    daily_average: float
    busiest_day: Optional[str]


class TimelineViewer:
    """
    时间线浏览器
    
    提供按时间顺序查看和管理记忆的功能，支持多种筛选和可视化。
    
    Attributes:
        memories: 记忆数据列表
        groups: 按天分组的时间线
        current_filter: 当前筛选条件
    """
    
    # 记忆类型显示名称
    TYPE_DISPLAY_NAMES = {
        "fact": "[事实]",
        "preference": "[喜好]",
        "task": "[任务]",
        "event": "[事件]",
        "goal": "[目标]",
        "context": "[上下文]",
    }
    
    # 时间范围显示名称
    RANGE_DISPLAY_NAMES = {
        TimeRange.TODAY: "今天",
        TimeRange.YESTERDAY: "昨天",
        TimeRange.THIS_WEEK: "本周",
        TimeRange.LAST_WEEK: "上周",
        TimeRange.THIS_MONTH: "本月",
        TimeRange.LAST_MONTH: "上月",
        TimeRange.ALL: "全部",
    }
    
    def __init__(self, memories: Optional[List[Dict[str, Any]]] = None):
        """
        初始化时间线浏览器
        
        Args:
            memories: 记忆数据列表
        """
        self.memories = memories or []
        self.groups: List[TimelineGroup] = []
        self.current_filter: Dict[str, Any] = {}
        
        print(f"[TimelineViewer] 初始化完成")
        print(f"  - 记忆数量: {len(self.memories)}")
        
        if self.memories:
            self._build_timeline()
    
    def add_memories(self, memories: List[Dict[str, Any]]) -> None:
        """添加记忆并重建时间线"""
        self.memories.extend(memories)
        self._build_timeline()
        print(f"[TimelineViewer] 添加 {len(memories)} 条记忆，当前共 {len(self.memories)} 条")
    
    def _build_timeline(self) -> None:
        """构建时间线分组"""
        # 按日期分组
        day_groups = defaultdict(list)
        
        for memory in self.memories:
            item = self._memory_to_timeline_item(memory)
            if item:
                day_groups[item.day_key].append(item)
        
        # 创建分组列表并排序
        self.groups = []
        for date_str in sorted(day_groups.keys(), reverse=True):
            items = sorted(
                day_groups[date_str],
                key=lambda x: x.created_at,
                reverse=True
            )
            self.groups.append(TimelineGroup(date=date_str, items=items))
    
    def _memory_to_timeline_item(self, memory: Dict[str, Any]) -> Optional[TimelineItem]:
        """将记忆字典转换为时间线项目"""
        try:
            created_at = memory.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            elif not isinstance(created_at, datetime):
                created_at = datetime.now()
            
            return TimelineItem(
                memory_id=memory.get("memory_id", ""),
                content=memory.get("content", ""),
                memory_type=memory.get("memory_type", "fact"),
                created_at=created_at,
                tags=memory.get("tags", []),
                importance=memory.get("importance", 3.0)
            )
        except Exception as e:
            print(f"[TimelineViewer警告] 转换记忆失败: {e}")
            return None
    
    def get_timeline(
        self,
        time_range: Optional[TimeRange] = None,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[TimelineGroup]:
        """
        获取时间线数据
        
        Args:
            time_range: 时间范围
            memory_type: 记忆类型筛选
            tags: 标签筛选
            limit: 限制返回天数
            
        Returns:
            List[TimelineGroup]: 时间线分组列表
        """
        filtered_groups = self.groups.copy()
        
        # 时间范围筛选
        if time_range:
            filtered_groups = self._filter_by_time_range(filtered_groups, time_range)
        
        # 类型筛选
        if memory_type:
            filtered_groups = self._filter_groups_by_type(filtered_groups, memory_type)
        
        # 标签筛选
        if tags:
            filtered_groups = self._filter_groups_by_tags(filtered_groups, tags)
        
        # 限制数量
        if limit:
            filtered_groups = filtered_groups[:limit]
        
        return filtered_groups
    
    def _filter_by_time_range(
        self,
        groups: List[TimelineGroup],
        time_range: TimeRange
    ) -> List[TimelineGroup]:
        """按时间范围筛选"""
        today = datetime.now().date()
        
        if time_range == TimeRange.TODAY:
            target_date = today.strftime("%Y-%m-%d")
            return [g for g in groups if g.date == target_date]
        
        elif time_range == TimeRange.YESTERDAY:
            target_date = (today - timedelta(days=1)).strftime("%Y-%m-%d")
            return [g for g in groups if g.date == target_date]
        
        elif time_range == TimeRange.THIS_WEEK:
            # 本周一到今天
            monday = today - timedelta(days=today.weekday())
            return [
                g for g in groups
                if monday <= datetime.strptime(g.date, "%Y-%m-%d").date() <= today
            ]
        
        elif time_range == TimeRange.LAST_WEEK:
            # 上周一到上周日
            last_monday = today - timedelta(days=today.weekday() + 7)
            last_sunday = last_monday + timedelta(days=6)
            return [
                g for g in groups
                if last_monday <= datetime.strptime(g.date, "%Y-%m-%d").date() <= last_sunday
            ]
        
        elif time_range == TimeRange.THIS_MONTH:
            first_day = today.replace(day=1)
            return [
                g for g in groups
                if first_day <= datetime.strptime(g.date, "%Y-%m-%d").date() <= today
            ]
        
        elif time_range == TimeRange.LAST_MONTH:
            # 上月1号到上月最后一天
            first_day_this_month = today.replace(day=1)
            last_day_last_month = first_day_this_month - timedelta(days=1)
            first_day_last_month = last_day_last_month.replace(day=1)
            return [
                g for g in groups
                if first_day_last_month <= datetime.strptime(g.date, "%Y-%m-%d").date() <= last_day_last_month
            ]
        
        return groups
    
    def _filter_groups_by_type(
        self,
        groups: List[TimelineGroup],
        memory_type: str
    ) -> List[TimelineGroup]:
        """按类型筛选分组"""
        result = []
        for group in groups:
            filtered_items = [
                item for item in group.items
                if item.memory_type == memory_type
            ]
            if filtered_items:
                result.append(TimelineGroup(date=group.date, items=filtered_items))
        return result
    
    def _filter_groups_by_tags(
        self,
        groups: List[TimelineGroup],
        tags: List[str]
    ) -> List[TimelineGroup]:
        """按标签筛选分组"""
        result = []
        for group in groups:
            filtered_items = [
                item for item in group.items
                if any(tag in item.tags for tag in tags)
            ]
            if filtered_items:
                result.append(TimelineGroup(date=group.date, items=filtered_items))
        return result
    
    def filter_by_date_range(
        self,
        start_date: str,
        end_date: str
    ) -> List[TimelineGroup]:
        """
        按自定义日期范围筛选
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            List[TimelineGroup]: 筛选后的时间线
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            return [
                g for g in self.groups
                if start <= datetime.strptime(g.date, "%Y-%m-%d").date() <= end
            ]
        except ValueError as e:
            print(f"[TimelineViewer错误] 日期格式错误: {e}")
            return []
    
    def filter_by_memory_type(self, memory_type: str) -> List[TimelineGroup]:
        """按记忆类型筛选"""
        return self._filter_groups_by_type(self.groups, memory_type)
    
    def filter_by_tags(self, tags: List[str]) -> List[TimelineGroup]:
        """按标签筛选"""
        return self._filter_groups_by_tags(self.groups, tags)
    
    def render_timeline(
        self,
        groups: Optional[List[TimelineGroup]] = None,
        show_details: bool = False,
        max_items_per_day: int = 10
    ) -> str:
        """
        渲染时间轴（文本形式）
        
        Args:
            groups: 时间线分组（默认使用全部）
            show_details: 是否显示详细信息
            max_items_per_day: 每天最多显示条目数
            
        Returns:
            str: 渲染后的时间轴文本
        """
        if groups is None:
            groups = self.groups
        
        if not groups:
            return "暂无记忆记录"
        
        lines = []
        lines.append("=" * 60)
        lines.append("[记忆时间线]")
        lines.append("=" * 60)
        
        for group in groups:
            # 日期标题
            date_obj = datetime.strptime(group.date, "%Y-%m-%d")
            weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date_obj.weekday()]
            lines.append(f"\n[{group.date}] ({weekday}) - {group.count} 条记忆")
            lines.append("-" * 60)
            
            # 显示条目
            items_to_show = group.items[:max_items_per_day]
            for i, item in enumerate(items_to_show, 1):
                type_name = self.TYPE_DISPLAY_NAMES.get(item.memory_type, "[笔记]")
                time_str = item.created_at.strftime("%H:%M")
                
                lines.append(f"  {i}. {type_name} [{time_str}] {item.content[:50]}")
                
                if show_details:
                    if item.tags:
                        lines.append(f"     [标签] {', '.join(item.tags)}")
                    lines.append(f"     [重要度] {'*' * int(item.importance)}")
                
                if i < len(items_to_show):
                    lines.append("")
            
            if len(group.items) > max_items_per_day:
                lines.append(f"     ... 还有 {len(group.items) - max_items_per_day} 条 ...")
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
    
    def get_item_detail(self, memory_id: str) -> Optional[TimelineItem]:
        """获取单个记忆的详细信息"""
        for group in self.groups:
            for item in group.items:
                if item.memory_id == memory_id:
                    return item
        return None
    
    def get_statistics(self) -> TimelineStatistics:
        """获取时间线统计信息"""
        if not self.memories:
            return TimelineStatistics(
                total_count=0,
                date_range=("", ""),
                type_distribution={},
                tag_distribution={},
                daily_average=0.0,
                busiest_day=None
            )
        
        # 类型分布
        type_dist = defaultdict(int)
        for memory in self.memories:
            type_dist[memory.get("memory_type", "fact")] += 1
        
        # 标签分布
        tag_dist = defaultdict(int)
        for memory in self.memories:
            for tag in memory.get("tags", []):
                tag_dist[tag] += 1
        
        # 日期范围
        dates = [
            datetime.fromisoformat(m.get("created_at", "2024-01-01").replace('Z', '+00:00'))
            for m in self.memories if m.get("created_at")
        ]
        if dates:
            min_date = min(dates).strftime("%Y-%m-%d")
            max_date = max(dates).strftime("%Y-%m-%d")
        else:
            min_date = max_date = ""
        
        # 日均记忆数
        if len(self.groups) > 0:
            daily_avg = len(self.memories) / len(self.groups)
        else:
            daily_avg = 0.0
        
        # 最忙碌的一天
        busiest = max(self.groups, key=lambda g: g.count) if self.groups else None
        busiest_day = busiest.date if busiest else None
        
        return TimelineStatistics(
            total_count=len(self.memories),
            date_range=(min_date, max_date),
            type_distribution=dict(type_dist),
            tag_distribution=dict(sorted(tag_dist.items(), key=lambda x: x[1], reverse=True)),
            daily_average=daily_avg,
            busiest_day=busiest_day
        )
    
    def export_timeline(
        self,
        filepath: str,
        groups: Optional[List[TimelineGroup]] = None
    ) -> bool:
        """
        导出时间线到JSON文件
        
        Args:
            filepath: 导出文件路径
            groups: 要导出的时间线分组
            
        Returns:
            bool: 是否成功
        """
        try:
            if groups is None:
                groups = self.groups
            
            export_data = {
                "export_time": datetime.now().isoformat(),
                "total_groups": len(groups),
                "total_items": sum(g.count for g in groups),
                "timeline": []
            }
            
            for group in groups:
                group_data = {
                    "date": group.date,
                    "count": group.count,
                    "items": [
                        {
                            "memory_id": item.memory_id,
                            "content": item.content,
                            "memory_type": item.memory_type,
                            "created_at": item.created_at.isoformat(),
                            "tags": item.tags,
                            "importance": item.importance
                        }
                        for item in group.items
                    ]
                }
                export_data["timeline"].append(group_data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            print(f"[TimelineViewer] 时间线已导出到: {filepath}")
            return True
            
        except Exception as e:
            print(f"[TimelineViewer错误] 导出失败: {e}")
            return False


# ========== 测试代码 ==========

def test_timeline_viewer():
    """测试时间线浏览模块"""
    print("\n" + "=" * 60)
    print("TimelineViewer 模块测试")
    print("=" * 60)
    
    # 准备测试数据
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    last_week = today - timedelta(days=5)
    
    test_memories = [
        {
            "memory_id": "mem_001",
            "content": "我喜欢喝美式咖啡，每天早上必须一杯",
            "memory_type": "preference",
            "tags": ["喜好", "咖啡"],
            "created_at": today.replace(hour=8, minute=0).isoformat(),
            "importance": 3.5
        },
        {
            "memory_id": "mem_002",
            "content": "下周三要参加项目评审会议",
            "memory_type": "task",
            "tags": ["工作", "会议"],
            "created_at": today.replace(hour=10, minute=30).isoformat(),
            "importance": 4.5
        },
        {
            "memory_id": "mem_003",
            "content": "学习Python编程，计划每天练习",
            "memory_type": "goal",
            "tags": ["目标", "学习"],
            "created_at": yesterday.replace(hour=14, minute=0).isoformat(),
            "importance": 4.0
        },
        {
            "memory_id": "mem_004",
            "content": "和朋友去公园散步",
            "memory_type": "event",
            "tags": ["生活", "朋友"],
            "created_at": yesterday.replace(hour=16, minute=0).isoformat(),
            "importance": 2.5
        },
        {
            "memory_id": "mem_005",
            "content": "客户要求下周交付产品原型",
            "memory_type": "task",
            "tags": ["工作", "客户"],
            "created_at": last_week.replace(hour=9, minute=0).isoformat(),
            "importance": 5.0
        },
    ]
    
    # 创建时间线浏览器
    viewer = TimelineViewer(memories=test_memories)
    
    # 测试1: 获取完整时间线
    print("\n1. 获取完整时间线")
    print("-" * 60)
    
    timeline = viewer.get_timeline()
    print(f"共有 {len(timeline)} 天，{sum(g.count for g in timeline)} 条记忆")
    for group in timeline:
        print(f"  {group.date}: {group.count} 条")
    
    # 测试2: 时间范围筛选
    print("\n2. 时间范围筛选")
    print("-" * 60)
    
    today_timeline = viewer.get_timeline(time_range=TimeRange.TODAY)
    print(f"今天: {len(today_timeline)} 天，{sum(g.count for g in today_timeline)} 条")
    
    week_timeline = viewer.get_timeline(time_range=TimeRange.THIS_WEEK)
    print(f"本周: {len(week_timeline)} 天，{sum(g.count for g in week_timeline)} 条")
    
    # 测试3: 类型筛选
    print("\n3. 按类型筛选")
    print("-" * 60)
    
    task_timeline = viewer.filter_by_memory_type("task")
    print(f"任务类型: {sum(g.count for g in task_timeline)} 条")
    
    # 测试4: 标签筛选
    print("\n4. 按标签筛选")
    print("-" * 60)
    
    work_timeline = viewer.filter_by_tags(["工作"])
    print(f"工作标签: {sum(g.count for g in work_timeline)} 条")
    
    # 测试5: 自定义日期范围
    print("\n5. 自定义日期范围")
    print("-" * 60)
    
    start = (today - timedelta(days=3)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    custom_timeline = viewer.filter_by_date_range(start, end)
    print(f"{start} 到 {end}: {len(custom_timeline)} 天")
    
    # 测试6: 渲染时间轴
    print("\n6. 渲染时间轴")
    print("-" * 60)
    
    rendered = viewer.render_timeline(timeline[:2], show_details=False)
    print(rendered)
    
    # 测试7: 获取详情
    print("\n7. 获取记忆详情")
    print("-" * 60)
    
    detail = viewer.get_item_detail("mem_001")
    if detail:
        print(f"ID: {detail.memory_id}")
        print(f"内容: {detail.content}")
        print(f"类型: {detail.memory_type}")
        print(f"标签: {detail.tags}")
    
    # 测试8: 统计信息
    print("\n8. 统计信息")
    print("-" * 60)
    
    stats = viewer.get_statistics()
    print(f"总记忆数: {stats.total_count}")
    print(f"日期范围: {stats.date_range[0]} 到 {stats.date_range[1]}")
    print(f"类型分布: {stats.type_distribution}")
    print(f"日均记忆: {stats.daily_average:.1f}")
    print(f"最忙碌的一天: {stats.busiest_day}")
    
    # 测试9: 导出
    print("\n9. 导出时间线")
    print("-" * 60)
    
    import tempfile
    import os
    
    temp_file = os.path.join(tempfile.gettempdir(), "timeline_export.json")
    success = viewer.export_timeline(temp_file)
    if success:
        print(f"导出成功: {temp_file}")
        # 清理
        os.remove(temp_file)
    
    # 最终报告
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    test_timeline_viewer()
