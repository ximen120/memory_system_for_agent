"""
配置加载器单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import os
from core.config_loader import Config, get_config, reset_config


class TestConfigLoader:
    """测试配置加载器"""
    
    def setup_method(self):
        """每个测试前重置配置"""
        reset_config()
    
    def test_config_loads_default_values(self):
        """测试加载默认值"""
        config = Config(env_file="nonexistent.env")  # 使用不存在的文件，触发默认值
        
        assert config.python_path == "python"
        assert config.data_dir == "./data"
        assert config.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
        assert config.log_level == "INFO"
        assert config.work_memory_hours == 24
        assert config.short_term_days == 7
        assert config.mid_term_days == 30
        assert config.long_term_days == 365
    
    def test_config_loads_from_env_file(self, tmp_path):
        """测试从.env文件加载配置"""
        env_file = tmp_path / ".env"
        env_file.write_text("""
PYTHON_PATH=/custom/python
DATA_DIR=/custom/data
WORK_MEMORY_HOURS=48
SHORT_TERM_DAYS=14
""")
        
        config = Config(env_file=env_file)
        
        assert config.python_path == "/custom/python"
        assert config.data_dir == "/custom/data"
        assert config.work_memory_hours == 48
        assert config.short_term_days == 14
        # 其他值保持默认
        assert config.mid_term_days == 30
    
    def test_config_integer_conversion(self, tmp_path):
        """测试整数类型转换"""
        env_file = tmp_path / ".env"
        env_file.write_text("WORK_MEMORY_HOURS=48")
        
        config = Config(env_file=env_file)
        assert isinstance(config.work_memory_hours, int)
        assert config.work_memory_hours == 48
    
    def test_config_invalid_integer_uses_default(self, tmp_path, capsys, monkeypatch):
        """测试无效整数使用默认值"""
        # 清除环境变量，确保不受其他测试影响
        monkeypatch.delenv("WORK_MEMORY_HOURS", raising=False)
        
        env_file = tmp_path / ".env"
        env_file.write_text("WORK_MEMORY_HOURS=invalid")
        
        config = Config(env_file=env_file)
        assert config.work_memory_hours == 24  # 默认值
        
        captured = capsys.readouterr()
        assert "警告" in captured.out or "警告" in captured.err
    
    def test_get_config_singleton(self):
        """测试 get_config 返回单例"""
        reset_config()  # 确保从头开始
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2
    
    def test_config_strips_whitespace(self, tmp_path, monkeypatch):
        """测试配置值去除首尾空格"""
        # 清除环境变量，确保不受其他测试影响
        monkeypatch.delenv("PYTHON_PATH", raising=False)
        
        env_file = tmp_path / ".env"
        env_file.write_text('PYTHON_PATH=  /path/with/spaces  ')
        
        config = Config(env_file=env_file)
        assert config.python_path == "/path/with/spaces"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
