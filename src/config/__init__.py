"""
配置模块
"""
try:
    from config.sync_config_loader import SyncConfigLoader
except ImportError:
    from src.config.sync_config_loader import SyncConfigLoader

__all__ = ['SyncConfigLoader']
