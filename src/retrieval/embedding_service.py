"""
Embedding服务

提供文本向量化功能，支持：
- 延迟加载模型
- 本地缓存管理
- 批量生成
- 降级方案
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Union
from dataclasses import dataclass

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Embedding配置"""
    model_name: str = "all-MiniLM-L6-v2"
    cache_dir: str = "./models"
    device: str = "cpu"
    offline: bool = True
    max_seq_length: int = 512


class EmbeddingService:
    """
    Embedding生成服务
    
    特性：
    - 延迟加载模型（避免启动阻塞）
    - 本地缓存管理
    - 批量生成支持
    - 降级方案（模型不可用时返回None）
    
    使用示例：
        >>> service = EmbeddingService()
        >>> embedding = service.generate("测试文本")
        >>> print(len(embedding))  # 384维
    """
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        cache_dir: Optional[str] = None,
        device: Optional[str] = None,
        config: Optional[EmbeddingConfig] = None
    ):
        """
        初始化Embedding服务
        
        Args:
            model_name: 模型名称，默认all-MiniLM-L6-v2
            cache_dir: 缓存目录，默认./models
            device: 运行设备，默认cpu
            config: 完整配置对象（优先使用）
        """
        if config:
            self.config = config
        else:
            self.config = EmbeddingConfig(
                model_name=model_name or os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
                cache_dir=cache_dir or os.getenv("EMBEDDING_CACHE_DIR", "./models"),
                device=device or os.getenv("EMBEDDING_DEVICE", "cpu"),
                offline=os.getenv("EMBEDDING_OFFLINE", "true").lower() == "true"
            )
        
        self._model = None
        self._is_loaded = False
        self._load_error = None
        
        logger.info(f"Embedding服务初始化: model={self.config.model_name}")
    
    def _load_model(self) -> bool:
        """
        延迟加载模型
        
        Returns:
            是否加载成功
        """
        if self._is_loaded:
            return True
        
        if self._load_error:
            logger.warning(f"模型之前加载失败: {self._load_error}")
            return False
        
        try:
            
            if self.config.offline:
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                logger.info("已启用HuggingFace离线模式")
            
            from sentence_transformers import SentenceTransformer
            
            cache_path = Path(self.config.cache_dir) / self.config.model_name
            
            if cache_path.exists():
                # 使用本地缓存
                logger.info(f"从本地缓存加载模型: {cache_path}")
                self._model = SentenceTransformer(
                    str(cache_path),
                    device=self.config.device
                )
            else:
                # 下载模型
                logger.info(f"下载模型: {self.config.model_name}")
                self._model = SentenceTransformer(
                    self.config.model_name,
                    device=self.config.device
                )
                # 保存到本地缓存
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                self._model.save(str(cache_path))
                logger.info(f"模型已缓存到: {cache_path}")
            
            self._is_loaded = True
            logger.info("模型加载成功")
            return True
            
        except ImportError as e:
            self._load_error = f"sentence-transformers未安装: {e}"
            logger.error(self._load_error)
            return False
            
        except Exception as e:
            self._load_error = f"模型加载失败: {e}"
            logger.error(self._load_error)
            return False
    
    def generate(
        self,
        text: str,
        return_none_on_error: bool = True
    ) -> Optional[List[float]]:
        """
        生成文本的embedding向量
        
        Args:
            text: 输入文本
            return_none_on_error: 出错时返回None而非抛出异常
            
        Returns:
            向量列表(384维)或None
            
        示例：
            >>> service = EmbeddingService()
            >>> embedding = service.generate("测试文本")
            >>> print(len(embedding))
            384
        """
        if not text or not text.strip():
            if return_none_on_error:
                return None
            raise ValueError("文本不能为空")
        
        if not self._load_model():
            if return_none_on_error:
                return None
            raise RuntimeError("模型未加载")
        
        try:
            # 截断超长文本
            if len(text) > self.config.max_seq_length * 3:  # 中文字符约占3字节
                text = text[:self.config.max_seq_length * 3]
            
            embedding = self._model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"生成embedding失败: {e}")
            if return_none_on_error:
                return None
            raise
    
    def generate_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[Optional[List[float]]]:
        """
        批量生成embedding
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
            
        Returns:
            向量列表，与输入一一对应
            
        示例：
            >>> service = EmbeddingService()
            >>> embeddings = service.generate_batch(["文本1", "文本2"])
            >>> print(len(embeddings))
            2
        """
        if not texts:
            return []
        
        if not self._load_model():
            return [None] * len(texts)
        
        try:
            # 过滤空文本
            valid_texts = []
            valid_indices = []
            for i, text in enumerate(texts):
                if text and text.strip():
                    valid_texts.append(text)
                    valid_indices.append(i)
            
            if not valid_texts:
                return [None] * len(texts)
            
            # 批量生成
            embeddings = self._model.encode(
                valid_texts,
                batch_size=batch_size,
                convert_to_numpy=True
            )
            
            # 构建结果列表
            results = [None] * len(texts)
            for idx, emb in zip(valid_indices, embeddings):
                results[idx] = emb.tolist()
            
            return results
            
        except Exception as e:
            logger.error(f"批量生成失败: {e}")
            return [None] * len(texts)
    
    def is_available(self) -> bool:
        """
        检查服务是否可用
        
        Returns:
            模型是否已加载成功
        """
        return self._load_model()
    
    def get_model_info(self) -> dict:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        info = {
            "model_name": self.config.model_name,
            "is_loaded": self._is_loaded,
            "is_available": self.is_available(),
            "cache_dir": self.config.cache_dir,
            "device": self.config.device
        }
        
        if self._load_error:
            info["error"] = self._load_error
        
        return info
    
    def clear_cache(self) -> bool:
        """
        清除模型缓存
        
        Returns:
            是否成功
        """
        try:
            import shutil
            cache_path = Path(self.config.cache_dir) / self.config.model_name
            if cache_path.exists():
                shutil.rmtree(cache_path)
                logger.info(f"缓存已清除: {cache_path}")
            self._model = None
            self._is_loaded = False
            self._load_error = None
            return True
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")
            return False


# 全局单例
_embedding_service_instance: Optional[EmbeddingService] = None


def get_embedding_service(
    model_name: Optional[str] = None,
    cache_dir: Optional[str] = None
) -> EmbeddingService:
    """
    获取全局Embedding服务实例（单例模式）
    
    Args:
        model_name: 模型名称
        cache_dir: 缓存目录
        
    Returns:
        EmbeddingService实例
    """
    global _embedding_service_instance
    
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService(
            model_name=model_name,
            cache_dir=cache_dir
        )
    
    return _embedding_service_instance


def reset_embedding_service() -> None:
    """重置全局实例（用于测试）"""
    global _embedding_service_instance
    _embedding_service_instance = None
