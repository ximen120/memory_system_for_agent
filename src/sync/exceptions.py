"""
同步相关异常定义
"""

class SyncError(Exception):
    """同步错误基类"""
    pass

class ConfigError(SyncError):
    """配置错误"""
    pass

class SourceNotFoundError(SyncError):
    """数据源不存在"""
    pass

class SourceReadError(SyncError):
    """数据源读取失败"""
    pass

class SyncConflictError(SyncError):
    """同步冲突"""
    pass
