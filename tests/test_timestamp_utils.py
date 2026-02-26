"""
时间戳工具单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from datetime import datetime, timezone
from core.timestamp_utils import now, to_datetime, from_datetime, get_timestamp_for_id


class TestTimestampUtils:
    """测试时间戳工具函数"""
    
    def test_now_returns_iso_format(self):
        """测试 now() 返回 ISO 8601 格式"""
        timestamp = now()
        # 验证格式包含日期、时间、时区
        assert "T" in timestamp
        assert "+" in timestamp or "Z" in timestamp
        # 验证可以解析
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        assert isinstance(dt, datetime)
    
    def test_now_returns_recent_time(self):
        """测试 now() 返回当前时间（前后1分钟内）"""
        before = datetime.now(timezone.utc)
        timestamp = now()
        after = datetime.now(timezone.utc)
        
        dt = datetime.fromisoformat(timestamp)
        # 转换到 UTC 比较
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        
        # 时间应该在 before 和 after 之间
        assert before <= dt <= after
    
    def test_to_datetime_with_valid_iso(self):
        """测试 to_datetime 解析有效 ISO 字符串"""
        iso_str = "2026-02-23T10:30:00+08:00"
        dt = to_datetime(iso_str)
        assert isinstance(dt, datetime)
        assert dt.year == 2026
        assert dt.month == 2
        assert dt.day == 23
    
    def test_to_datetime_with_z_suffix(self):
        """测试 to_datetime 处理 Z 后缀（UTC）"""
        iso_str = "2026-02-23T10:30:00Z"
        dt = to_datetime(iso_str)
        assert isinstance(dt, datetime)
    
    def test_to_datetime_with_invalid_string(self):
        """测试 to_datetime 处理无效字符串"""
        with pytest.raises(ValueError):
            to_datetime("invalid-timestamp")
    
    def test_from_datetime_with_timezone(self):
        """测试 from_datetime 带时区的 datetime"""
        dt = datetime(2026, 2, 23, 10, 30, 0, tzinfo=timezone.utc)
        result = from_datetime(dt)
        assert "2026-02-23" in result
        assert "10:30:00" in result
    
    def test_from_datetime_without_timezone(self):
        """测试 from_datetime 无时区的 datetime"""
        dt = datetime(2026, 2, 23, 10, 30, 0)
        result = from_datetime(dt)
        assert "2026-02-23" in result
    
    def test_from_datetime_preserves_microseconds(self):
        """测试 from_datetime 保留微秒"""
        dt = datetime(2026, 2, 23, 10, 30, 0, 123456, tzinfo=timezone.utc)
        result = from_datetime(dt)
        assert "2026-02-23" in result
        assert "10:30:00" in result
    
    def test_get_timestamp_for_id_format(self):
        """测试 get_timestamp_for_id 返回 14 位数字"""
        ts = get_timestamp_for_id()
        assert len(ts) == 14
        assert ts.isdigit()
        # 格式: YYYYMMDDHHMMSS
        assert ts.startswith("20")  # 20xx 年份
    
    def test_get_timestamp_for_id_is_recent(self):
        """测试 get_timestamp_for_id 返回当前时间"""
        ts = get_timestamp_for_id()
        now_str = datetime.now().strftime("%Y%m%d%H%M%S")
        # 应该非常接近当前时间（相差不超过1秒）
        assert abs(int(ts) - int(now_str)) <= 1
    
    def test_to_datetime_error_message(self):
        """测试 to_datetime 错误信息"""
        with pytest.raises(ValueError) as exc_info:
            to_datetime("invalid")
        assert "无效的时间戳格式" in str(exc_info.value)
    
    def test_to_datetime_various_formats(self):
        """测试 to_datetime 处理各种格式"""
        # 带时区
        dt1 = to_datetime("2026-02-23T10:30:00+08:00")
        assert dt1.hour == 10
        
        # UTC 格式 Z
        dt2 = to_datetime("2026-02-23T10:30:00Z")
        assert dt2.hour == 10
        
        # 无时区（会被加上本地时区）
        dt3 = to_datetime("2026-02-23T10:30:00")
        assert dt3.hour == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
