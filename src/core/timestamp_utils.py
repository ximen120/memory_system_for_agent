"""
时间戳工具模块

提供统一的时间戳生成和转换功能。
"""

from datetime import datetime, timezone
from typing import Union


def now() -> str:
    """
    获取当前时间的ISO格式时间戳
    
    Returns:
        str: ISO 8601格式时间戳，例如 "2026-02-23T10:30:00+08:00"
    """
    return datetime.now(timezone.utc).astimezone().isoformat()


def to_datetime(timestamp_str: str) -> datetime:
    """
    将ISO格式时间戳字符串转换为datetime对象
    
    Args:
        timestamp_str: ISO 8601格式时间戳字符串
        
    Returns:
        datetime: datetime对象
        
    Raises:
        ValueError: 如果时间戳格式不正确
    """
    try:
        # 处理带时区的ISO格式
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        return datetime.fromisoformat(timestamp_str)
    except ValueError as e:
        raise ValueError(f"无效的时间戳格式: {timestamp_str}") from e


def from_datetime(dt: datetime) -> str:
    """
    将datetime对象转换为ISO格式时间戳字符串
    
    Args:
        dt: datetime对象
        
    Returns:
        str: ISO 8601格式时间戳字符串
    """
    if dt.tzinfo is None:
        # 如果没有时区信息，假设为本地时间
        dt = dt.replace(tzinfo=datetime.now(timezone.utc).astimezone().tzinfo)
    return dt.isoformat()


def get_timestamp_for_id() -> str:
    """
    获取用于生成ID的紧凑时间戳格式
    
    Returns:
        str: 紧凑格式，例如 "20260223103000"
    """
    return datetime.now().strftime("%Y%m%d%H%M%S")


if __name__ == "__main__":
    # 简单测试
    print(f"当前时间: {now()}")
    print(f"ID时间戳: {get_timestamp_for_id()}")
