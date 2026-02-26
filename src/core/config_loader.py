"""
配置加载器模块

读取.env文件配置，提供统一的配置访问接口。
"""

import os
from pathlib import Path
from typing import Optional, Union
from dotenv import load_dotenv


class Config:
    """配置类，封装所有配置项"""
    
    def __init__(self, env_file: Optional[Union[str, Path]] = None):
        """
        初始化配置
        
        Args:
            env_file: .env文件路径，默认为项目根目录下的.env
        """
        if env_file is None:
            # 默认在项目根目录查找.env
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            env_file = project_root / ".env"
        
        # 加载.env文件
        if Path(env_file).exists():
            load_dotenv(env_file)
        
        # 读取配置项
        self.python_path = self._get_str("PYTHON_PATH", "python")
        self.data_dir = self._get_str("DATA_DIR", "./data")
        self.embedding_model = self._get_str("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.vector_db_path = self._get_str("VECTOR_DB_PATH", "./data/vector_db")
        self.log_level = self._get_str("LOG_LEVEL", "INFO")
        
        # 记忆分层配置（带类型转换）
        self.work_memory_hours = self._get_int("WORK_MEMORY_HOURS", 24)
        self.short_term_days = self._get_int("SHORT_TERM_DAYS", 7)
        self.mid_term_days = self._get_int("MID_TERM_DAYS", 30)
        self.long_term_days = self._get_int("LONG_TERM_DAYS", 365)
    
    def _get_str(self, key: str, default: str) -> str:
        """获取字符串配置"""
        value = os.getenv(key)
        if value is None or value.strip() == "":
            return default
        return value.strip()
    
    def _get_int(self, key: str, default: int) -> int:
        """获取整数配置"""
        value = os.getenv(key)
        if value is None or value.strip() == "":
            return default
        try:
            return int(value.strip())
        except ValueError:
            print(f"警告: 配置项 {key} 的值 '{value}' 不是有效整数，使用默认值 {default}")
            return default
    
    def validate(self) -> list[str]:
        """
        验证配置是否完整
        
        Returns:
            list[str]: 缺失或错误的配置项列表，空列表表示验证通过
        """
        errors = []
        
        # 检查必要路径
        if not Path(self.data_dir).exists():
            errors.append(f"数据目录不存在: {self.data_dir}")
        
        # 检查Python路径
        if not Path(self.python_path).exists():
            errors.append(f"Python路径不存在: {self.python_path}")
        
        return errors


# 全局配置实例（懒加载）
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    获取全局配置实例
    
    Returns:
        Config: 配置对象
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reset_config() -> None:
    """
    重置全局配置实例（主要用于测试）
    """
    global _config_instance
    _config_instance = None


if __name__ == "__main__":
    # 简单测试
    config = Config()
    print("配置加载测试:")
    print(f"  Python路径: {config.python_path}")
    print(f"  数据目录: {config.data_dir}")
    print(f"  Embedding模型: {config.embedding_model}")
    print(f"  工作记忆: {config.work_memory_hours}小时")
    print(f"  短期记忆: {config.short_term_days}天")
    print(f"  中期记忆: {config.mid_term_days}天")
    print(f"  长期记忆: {config.long_term_days}天")
    
    errors = config.validate()
    if errors:
        print(f"\n⚠️ 配置问题: {errors}")
    else:
        print("\n✅ 配置验证通过")
