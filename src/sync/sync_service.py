"""
数据同步服务主类
"""
import logging
from threading import Lock
from datetime import datetime, timedelta
from typing import List, Dict, Optional

try:
    from config.sync_config_loader import SyncConfigLoader
    from sync.readers.file_reader import FileReader
    from sync.exceptions import SyncError, SourceNotFoundError
except ImportError:
    from src.config.sync_config_loader import SyncConfigLoader
    from src.sync.readers.file_reader import FileReader
    from src.sync.exceptions import SyncError, SourceNotFoundError

logger = logging.getLogger(__name__)

class DataSyncService:
    """
    数据同步服务
    
    负责从外部数据源同步数据到记忆系统。
    支持文件、目录、API等多种数据源类型。
    """
    
    def __init__(
        self, 
        config_path: str = "config/sync_config.yaml", 
        memory_api = None
    ):
        """
        初始化同步服务
        
        Args:
            config_path: 配置文件路径
            memory_api: 记忆系统API实例（可选）
        """
        self.config_loader = SyncConfigLoader(config_path)
        self.memory_api = memory_api
        
        self.readers = {
            'file': FileReader(),
        }
        
        self._locks: Dict[str, Lock] = {}
        self._sync_history: Dict[str, Dict] = {}
        
        logger.info("数据同步服务初始化完成")
    
    def sync_source(self, source_name: str) -> bool:
        """
        同步单个数据源
        
        Args:
            source_name: 数据源名称
        
        Returns:
            bool: True表示成功，False表示失败
        """
        if source_name not in self._locks:
            self._locks[source_name] = Lock()
        
        with self._locks[source_name]:
            try:
                logger.info(f"开始同步数据源: {source_name}")
                
                source = self.config_loader.get_source(source_name)
                
                if not source.get('enabled', True):
                    logger.info(f"数据源已禁用: {source_name}")
                    return False
                
                reader = self.readers.get(source['type'])
                if not reader:
                    raise SyncError(f"不支持的数据源类型: {source['type']}")
                
                if not reader.exists(source['source_config']):
                    raise SourceNotFoundError(
                        f"数据源不存在: {source['source_config'].get('path', 'unknown')}"
                    )
                
                current_hash = reader.get_hash(source['source_config'])
                last_hash = self._sync_history.get(source_name, {}).get('hash')
                
                if current_hash == last_hash:
                    logger.info(f"数据源无变化，跳过同步: {source_name}")
                    return True
                
                content = reader.read(source['source_config'])
                
                logger.info(f"同步成功: {source_name}, 内容长度: {len(content)}")
                
                self._sync_history[source_name] = {
                    'hash': current_hash,
                    'last_sync': datetime.now().isoformat(),
                }
                
                return True
                
            except SourceNotFoundError as e:
                logger.error(f"数据源不存在: {source_name}, 错误: {e}")
                raise
            except SyncError as e:
                logger.error(f"同步失败: {source_name}, 错误: {e}")
                raise
            except Exception as e:
                logger.error(f"同步异常: {source_name}, 错误: {e}", exc_info=True)
                raise SyncError(f"同步异常: {e}") from e
    
    def sync_all(self) -> Dict[str, bool]:
        """
        同步所有启用的数据源
        
        Returns:
            Dict[str, bool]: 每个数据源的同步结果
        """
        logger.info("开始同步所有数据源")
        results = {}
        
        for source in self.config_loader.get_enabled_sources():
            source_name = source['name']
            try:
                results[source_name] = self.sync_source(source_name)
            except Exception as e:
                logger.error(f"同步失败: {source_name}, 错误: {e}")
                results[source_name] = False
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"同步完成: 成功 {success_count}/{len(results)}")
        return results
    
    def get_sync_status(self, source_name: str) -> Optional[Dict]:
        """获取数据源同步状态"""
        return self._sync_history.get(source_name)
