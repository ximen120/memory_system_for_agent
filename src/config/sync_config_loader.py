"""
同步配置加载器
"""
import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any

try:
    from sync.exceptions import ConfigError
except ImportError:
    from src.sync.exceptions import ConfigError

logger = logging.getLogger(__name__)

class SyncConfigLoader:
    """同步配置加载器"""
    
    VALID_SOURCE_TYPES = ['file', 'directory', 'api', 'database']
    VALID_INTERVALS = ['realtime', 'hourly', 'daily', 'weekly', 'manual']
    VALID_CONFLICT_RESOLUTIONS = ['replace', 'append', 'skip']
    VALID_VALIDITY_TYPES = ['static', 'long_term', 'medium_term', 'short_term', 'volatile']
    
    def __init__(self, config_path: str = "config/sync_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载并验证配置"""
        if not self.config_path.exists():
            raise ConfigError(f"配置文件不存在: {self.config_path}")
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML格式错误: {e}")
        except Exception as e:
            raise ConfigError(f"读取配置文件失败: {e}")
        
        self._validate_config(config)
        logger.info(f"成功加载配置: {self.config_path}")
        return config
    
    def _validate_config(self, config: Dict) -> None:
        """验证配置格式（使用raise而非assert）"""
        if 'global' not in config:
            raise ConfigError("配置缺少 'global' 字段")
        
        if 'sync_sources' not in config:
            raise ConfigError("配置缺少 'sync_sources' 字段")
        
        if not isinstance(config['sync_sources'], list):
            raise ConfigError("'sync_sources' 必须是列表")
        
        source_names = set()
        for idx, source in enumerate(config['sync_sources']):
            self._validate_source(source, idx, source_names)
    
    def _validate_source(self, source: Dict, idx: int, source_names: set) -> None:
        """验证单个数据源配置"""
        if 'name' not in source:
            raise ConfigError(f"数据源[{idx}]缺少必填字段 'name'")
        
        name = source['name']
        
        if name in source_names:
            raise ConfigError(f"数据源名称重复: {name}")
        source_names.add(name)
        
        if 'type' not in source:
            raise ConfigError(f"数据源'{name}'缺少必填字段 'type'")
        
        if source['type'] not in self.VALID_SOURCE_TYPES:
            raise ConfigError(
                f"数据源'{name}'的type无效: {source['type']}, "
                f"有效值: {self.VALID_SOURCE_TYPES}"
            )
        
        if 'source_config' not in source:
            raise ConfigError(f"数据源'{name}'缺少必填字段 'source_config'")
        
        if 'sync_strategy' not in source:
            raise ConfigError(f"数据源'{name}'缺少必填字段 'sync_strategy'")
        
        if 'memory_mapping' not in source:
            raise ConfigError(f"数据源'{name}'缺少必填字段 'memory_mapping'")
        
        strategy = source['sync_strategy']
        if 'interval' in strategy:
            if strategy['interval'] not in self.VALID_INTERVALS:
                raise ConfigError(
                    f"数据源'{name}'的interval无效: {strategy['interval']}, "
                    f"有效值: {self.VALID_INTERVALS}"
                )
        
        if 'conflict_resolution' in strategy:
            if strategy['conflict_resolution'] not in self.VALID_CONFLICT_RESOLUTIONS:
                raise ConfigError(
                    f"数据源'{name}'的conflict_resolution无效: {strategy['conflict_resolution']}, "
                    f"有效值: {self.VALID_CONFLICT_RESOLUTIONS}"
                )
        
        mapping = source['memory_mapping']
        if 'validity_type' in mapping:
            if mapping['validity_type'] not in self.VALID_VALIDITY_TYPES:
                raise ConfigError(
                    f"数据源'{name}'的validity_type无效: {mapping['validity_type']}, "
                    f"有效值: {self.VALID_VALIDITY_TYPES}"
                )
    
    def get_enabled_sources(self) -> List[Dict]:
        """获取启用的数据源"""
        if not self.config['global'].get('enabled', True):
            logger.info("全局同步已禁用")
            return []
        
        enabled = [s for s in self.config['sync_sources'] if s.get('enabled', True)]
        logger.info(f"找到 {len(enabled)} 个启用的数据源")
        return enabled
    
    def get_source(self, name: str) -> Dict[str, Any]:
        """根据名称获取数据源配置"""
        for source in self.config['sync_sources']:
            if source['name'] == name:
                return source
        raise ConfigError(f"数据源不存在: {name}")
