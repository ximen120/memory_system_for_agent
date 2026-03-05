"""
同步服务单元测试
"""
import sys
import pytest
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from sync.sync_service import DataSyncService
from sync.exceptions import SourceNotFoundError


def test_sync_service_init():
    """测试同步服务初始化"""
    service = DataSyncService(config_path="tests/fixtures/valid_sync_config.yaml")
    assert service.config_loader is not None
    assert service.readers is not None


def test_sync_source():
    """测试同步单个数据源"""
    service = DataSyncService(config_path="tests/fixtures/valid_sync_config.yaml")
    
    result = service.sync_source("test_todo")
    assert result is True


def test_sync_source_not_found():
    """测试同步不存在的数据源"""
    service = DataSyncService(config_path="tests/fixtures/valid_sync_config.yaml")
    
    with pytest.raises(SourceNotFoundError):
        # 使用一个不存在的路径
        service.config_loader.config['sync_sources'][0]['source_config']['path'] = 'tests/fixtures/nonexistent.md'
        service.sync_source("test_todo")


def test_sync_all():
    """测试同步所有数据源"""
    service = DataSyncService(config_path="tests/fixtures/valid_sync_config.yaml")
    
    results = service.sync_all()
    assert isinstance(results, dict)
    assert "test_todo" in results


def test_get_sync_status():
    """测试获取同步状态"""
    service = DataSyncService(config_path="tests/fixtures/valid_sync_config.yaml")
    
    # 同步前状态为空
    status = service.get_sync_status("test_todo")
    assert status is None
    
    # 同步后状态存在
    service.sync_source("test_todo")
    status = service.get_sync_status("test_todo")
    assert status is not None
    assert 'hash' in status
    assert 'last_sync' in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
