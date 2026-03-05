"""
同步配置加载器单元测试
"""
import sys
import pytest
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config.sync_config_loader import SyncConfigLoader
from sync.exceptions import ConfigError


def test_load_valid_config():
    """测试加载有效配置"""
    loader = SyncConfigLoader("tests/fixtures/valid_sync_config.yaml")
    assert loader.config is not None
    assert 'sync_sources' in loader.config
    assert len(loader.config['sync_sources']) > 0


def test_load_nonexistent_config():
    """测试加载不存在的配置"""
    with pytest.raises(ConfigError) as exc_info:
        SyncConfigLoader("tests/fixtures/nonexistent.yaml")
    assert "配置文件不存在" in str(exc_info.value)


def test_invalid_config_missing_name():
    """测试无效配置：缺少name"""
    with pytest.raises(ConfigError) as exc_info:
        SyncConfigLoader("tests/fixtures/invalid_config.yaml")
    assert "缺少必填字段 'name'" in str(exc_info.value)


def test_get_enabled_sources():
    """测试获取启用的数据源"""
    loader = SyncConfigLoader("tests/fixtures/valid_sync_config.yaml")
    sources = loader.get_enabled_sources()
    assert len(sources) > 0
    assert all(s.get('enabled', True) for s in sources)


def test_get_source_by_name():
    """测试根据名称获取数据源"""
    loader = SyncConfigLoader("tests/fixtures/valid_sync_config.yaml")
    source = loader.get_source("test_todo")
    assert source is not None
    assert source['name'] == "test_todo"


def test_get_source_not_found():
    """测试获取不存在的数据源"""
    loader = SyncConfigLoader("tests/fixtures/valid_sync_config.yaml")
    with pytest.raises(ConfigError) as exc_info:
        loader.get_source("nonexistent")
    assert "数据源不存在" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
