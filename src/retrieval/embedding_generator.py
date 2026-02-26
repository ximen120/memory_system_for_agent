"""
Embedding 生成器

将文本转换为向量表示，用于语义检索。
"""

import os; os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
from typing import List, Optional, Union
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    raise ImportError("请安装 sentence-transformers: pip install sentence-transformers")


class EmbeddingError(Exception):
    """Embedding 生成错误"""
    pass


class EmbeddingGenerator:
    """
    Embedding 生成器
    
    使用预训练模型将文本转换为向量表示。
    
    Attributes:
        model: SentenceTransformer 模型实例
        model_name: 模型名称
        embedding_dim: 向量维度
        max_length: 最大处理长度
    """
    
    # 支持的模型配置
    SUPPORTED_MODELS = {
        "sentence-transformers/all-MiniLM-L6-v2": {
            "dim": 384,
            "max_length": 256,
            "description": "轻量级模型，适合本地部署"
        },
        "BAAI/bge-m3": {
            "dim": 1024,
            "max_length": 8192,
            "description": "高性能多语言模型"
        }
    }
    
    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        """
        初始化 Embedding 生成器
        
        Args:
            model_name: 模型名称，默认为 all-MiniLM-L6-v2
            device: 运行设备 (cpu/cuda)，默认自动选择
            cache_dir: 模型缓存目录
            
        Raises:
            EmbeddingError: 模型加载失败时抛出
        """
        self.model_name = model_name
        
        # 获取模型配置
        if model_name in self.SUPPORTED_MODELS:
            self.embedding_dim = self.SUPPORTED_MODELS[model_name]["dim"]
            self.max_length = self.SUPPORTED_MODELS[model_name]["max_length"]
        else:
            # 未知模型，使用默认值
            self.embedding_dim = 384
            self.max_length = 256
        
        try:
            # 加载模型
            load_kwargs = {}
            if cache_dir:
                load_kwargs["cache_folder"] = cache_dir
            
            self.model = SentenceTransformer(model_name, device=device, **load_kwargs)
            
            # 验证模型输出维度
            test_embedding = self.model.encode("test", show_progress_bar=False)
            actual_dim = len(test_embedding)
            
            if actual_dim != self.embedding_dim:
                print(f"警告: 模型实际维度 {actual_dim} 与配置 {self.embedding_dim} 不符，使用实际值")
                self.embedding_dim = actual_dim
                
        except Exception as e:
            raise EmbeddingError(f"模型加载失败 '{model_name}': {e}") from e
    
    def generate(self, text: str, normalize: bool = True) -> List[float]:
        """
        生成单条文本的 Embedding
        
        Args:
            text: 输入文本
            normalize: 是否归一化向量，默认 True
            
        Returns:
            List[float]: 向量表示
            
        Raises:
            EmbeddingError: 生成失败时抛出
        """
        # 验证输入
        if text is None:
            raise EmbeddingError("输入文本不能为 None")
        
        if not isinstance(text, str):
            text = str(text)
        
        # 处理空文本
        if not text.strip():
            # 返回零向量
            return [0.0] * self.embedding_dim
        
        # 截断超长文本（按字符数粗略估计）
        if len(text) > self.max_length * 4:  # 粗略估计：每个token约4个字符
            text = text[:self.max_length * 4]
        
        try:
            # 生成向量
            embedding = self.model.encode(
                text,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=normalize
            )
            
            # 转换为 Python 列表
            return embedding.tolist()
            
        except Exception as e:
            raise EmbeddingError(f"Embedding 生成失败: {e}") from e
    
    def batch_generate(
        self,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = 32,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        批量生成文本的 Embedding
        
        Args:
            texts: 输入文本列表
            normalize: 是否归一化向量，默认 True
            batch_size: 批处理大小，默认 32
            show_progress: 是否显示进度条，默认 False
            
        Returns:
            List[List[float]]: 向量列表，与输入顺序一致
            
        Raises:
            EmbeddingError: 生成失败时抛出
        """
        if not texts:
            return []
        
        # 处理 None 和非字符串
        processed_texts = []
        for text in texts:
            if text is None:
                processed_texts.append("")
            elif not isinstance(text, str):
                processed_texts.append(str(text))
            else:
                processed_texts.append(text)
        
        # 截断超长文本
        processed_texts = [
            text[:self.max_length * 4] if len(text) > self.max_length * 4 else text
            for text in processed_texts
        ]
        
        try:
            # 批量生成
            embeddings = self.model.encode(
                processed_texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=normalize
            )
            
            # 转换为 Python 列表
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            raise EmbeddingError(f"批量 Embedding 生成失败: {e}") from e
    
    def get_info(self) -> dict:
        """
        获取生成器信息
        
        Returns:
            dict: 包含模型名称、维度、最大长度等信息
        """
        return {
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "max_length": self.max_length,
            "device": str(self.model.device),
        }


if __name__ == "__main__":
    # 简单测试
    print("EmbeddingGenerator 基础测试:\n")
    
    # 1. 初始化
    print("1. 初始化模型...")
    try:
        generator = EmbeddingGenerator()
        info = generator.get_info()
        print(f"   模型: {info['model_name']}")
        print(f"   维度: {info['embedding_dim']}")
        print(f"   设备: {info['device']}")
        print(f"   最大长度: {info['max_length']}")
    except Exception as e:
        print(f"   ❌ 初始化失败: {e}")
        exit(1)
    
    # 2. 单文本生成
    print("\n2. 单文本生成测试:")
    texts = [
        "安哥喜欢喝咖啡",
        "Memory system v3.0",
        "这是一段很长的中文文本，" * 50,  # 长文本
        "",  # 空文本
    ]
    
    for text in texts:
        try:
            embedding = generator.generate(text)
            preview = text[:20] + "..." if len(text) > 20 else text
            print(f"   '{preview}' -> 维度: {len(embedding)}, 前3个值: {embedding[:3]}")
        except Exception as e:
            print(f"   ❌ 失败: {e}")
    
    # 3. 批量生成
    print("\n3. 批量生成测试:")
    batch_texts = [f"文本{i}" for i in range(10)]
    embeddings = generator.batch_generate(batch_texts)
    print(f"   输入: {len(batch_texts)} 条")
    print(f"   输出: {len(embeddings)} 个向量")
    print(f"   每个向量维度: {len(embeddings[0])}")
    
    print("\n✅ 所有基础测试通过!")
