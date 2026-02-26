"""
日志工具单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import logging
import tempfile
import shutil
from core.logger import setup_logger, get_logger


class TestLogger:
    """测试日志工具"""
    
    def test_setup_logger_returns_logger(self):
        """测试 setup_logger 返回 Logger 对象"""
        logger = setup_logger("test1", "INFO")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test1"
    
    def test_setup_logger_sets_level(self):
        """测试设置日志级别"""
        logger = setup_logger("test2", "DEBUG")
        assert logger.level == logging.DEBUG
        
        logger = setup_logger("test3", "ERROR")
        assert logger.level == logging.ERROR
    
    def test_setup_logger_creates_file(self):
        """测试创建日志文件"""
        import logging
        tmpdir = tempfile.mkdtemp()
        try:
            logger = setup_logger("test4", "INFO", tmpdir)
            logger.info("测试消息")
            
            # 关闭所有文件处理器，释放文件锁
            for handler in logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
            
            # 检查日志文件是否存在
            log_files = list(Path(tmpdir).glob("test4_*.log"))
            assert len(log_files) == 1
        finally:
            # 清理
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_log_format(self, capsys):
        """测试日志格式"""
        logger = setup_logger("test5", "INFO")
        logger.info("测试消息")
        
        captured = capsys.readouterr()
        # 格式: [时间] [级别] [模块] 消息
        assert "[INFO]" in captured.out
        assert "[test5]" in captured.out
        assert "测试消息" in captured.out
    
    def test_get_logger_singleton(self):
        """测试 get_logger 返回单例"""
        logger1 = get_logger()
        logger2 = get_logger()
        assert logger1 is logger2
    
    def test_logger_handlers_cleared(self):
        """测试重复设置时清除旧处理器"""
        logger = setup_logger("test6", "INFO")
        handler_count_1 = len(logger.handlers)
        
        # 再次设置同名logger
        logger2 = setup_logger("test6", "DEBUG")
        handler_count_2 = len(logger2.handlers)
        
        # 处理器应该被清除并重新添加
        assert handler_count_1 == handler_count_2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
