"""
日志工具模块

提供统一的日志记录功能。
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "memory_system",
    level: str = "INFO",
    log_dir: Optional[str] = None
) -> logging.Logger:
    """
    设置并获取日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别 (DEBUG/INFO/WARNING/ERROR)
        log_dir: 日志文件目录，默认为None（不写入文件）
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # 清除已有处理器并关闭文件
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            handler.close()
        logger.removeHandler(handler)
    
    # 格式: [时间] [级别] [模块] 消息
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志目录）
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 按日期分割日志文件
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = log_path / f"{name}_{today}.log"
        
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 默认日志记录器（懒加载）
_default_logger: Optional[logging.Logger] = None


def get_logger() -> logging.Logger:
    """
    获取默认日志记录器
    
    Returns:
        logging.Logger: 默认日志记录器
    """
    global _default_logger
    if _default_logger is None:
        _default_logger = setup_logger()
    return _default_logger


if __name__ == "__main__":
    # 简单测试
    logger = setup_logger("test", "DEBUG", "./logs")
    
    print("测试各级别日志:")
    logger.debug("这是一条DEBUG日志")
    logger.info("这是一条INFO日志")
    logger.warning("这是一条WARNING日志")
    logger.error("这是一条ERROR日志")
    
    print("\n✅ 日志测试完成，检查 ./logs/ 目录")
