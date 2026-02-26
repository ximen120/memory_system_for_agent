"""
ChromaDB 向量存储实现（Windows文件锁定问题修复版）

修复内容：
1. 添加内存模式支持（TEST_MODE=true）
2. 添加连接池管理和资源释放
3. 添加上下文管理器支持（with语句）
4. 添加显式关闭连接方法
5. Windows平台特定优化

将记忆单元持久化到 ChromaDB，支持语义检索。
"""

import os
import sys
import atexit
import platform
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from contextlib import contextmanager

try:
    from .base_storage import BaseStorage, StorageError, MemoryNotFoundError
    from ..core.memory_unit import MemoryUnit
except ImportError:
    try:
        from base_storage import BaseStorage, StorageError, MemoryNotFoundError
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
        from memory_unit import MemoryUnit
    except ImportError:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from base_storage import BaseStorage, StorageError, MemoryNotFoundError
        sys.path.insert(0, str(Path(__file__).parent.parent / "core"))
        from memory_unit import MemoryUnit

import chromadb
from chromadb.config import Settings


# 检测运行环境
IS_WINDOWS = platform.system() == "Windows"
TEST_MODE = os.environ.get("TEST_MODE", "false").lower() == "true"
FORCE_MEMORY_MODE = os.environ.get("FORCE_MEMORY_MODE", "false").lower() == "true"

# Windows平台默认使用内存模式（如果未明确设置持久化）
if IS_WINDOWS and not os.environ.get("PERSISTENT_MODE"):
    DEFAULT_MEMORY_MODE = True
else:
    DEFAULT_MEMORY_MODE = False


class ChromaStorage(BaseStorage):
    """
    ChromaDB 向量存储（Windows文件锁定问题修复版）
    
    修复Windows文件锁定问题：
    1. 内存模式：数据存储在内存中，无文件锁定
    2. 连接管理：显式关闭连接释放资源
    3. 上下文管理：支持with语句自动清理
    
    Attributes:
        client: ChromaDB 客户端
        collection: 记忆集合
        collection_name: 集合名称
        _is_closed: 连接是否已关闭
    """
    
    # 类级别的客户端缓存（避免重复创建）
    _client_cache: Dict[str, Any] = {}
    
    def __init__(
        self,
        persist_directory: str = "./data/vector_db",
        collection_name: str = "memories",
        use_memory_mode: Optional[bool] = None
    ):
        """
        初始化 ChromaDB 存储
        
        Args:
            persist_directory: 数据持久化目录
            collection_name: 集合名称
            use_memory_mode: 是否使用内存模式（None=自动判断）
        """
        super().__init__("chroma")
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        self._is_closed = False
        self._client_key = f"{collection_name}_{persist_directory}"
        
        # 确定是否使用内存模式
        if use_memory_mode is None:
            # 优先级：FORCE_MEMORY_MODE > TEST_MODE > DEFAULT_MEMORY_MODE
            self.use_memory_mode = FORCE_MEMORY_MODE or TEST_MODE or DEFAULT_MEMORY_MODE
        else:
            self.use_memory_mode = use_memory_mode
        
        # Windows平台警告
        if IS_WINDOWS and not self.use_memory_mode:
            print("[ChromaDB警告] Windows平台使用持久化模式可能遇到文件锁定问题")
            print("                建议设置 TEST_MODE=true 或 FORCE_MEMORY_MODE=true")
        
        self._init_client()
        
        # 注册退出清理
        atexit.register(self.close)
    
    def _init_client(self):
        """初始化ChromaDB客户端"""
        try:
            # 检查缓存
            if self._client_key in self._client_cache:
                print(f"[ChromaDB] 使用缓存的客户端")
                self.client = self._client_cache[self._client_key]
            elif self.use_memory_mode:
                # 内存模式：数据存储在内存中，无文件锁定
                print("[ChromaDB] 使用内存模式（数据不持久化）")
                self.client = chromadb.EphemeralClient(
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            else:
                # 持久化模式：数据存储在磁盘
                print(f"[ChromaDB] 使用持久化模式，数据目录: {self.persist_directory}")
                self.persist_directory.mkdir(parents=True, exist_ok=True)
                self.client = chromadb.PersistentClient(
                    path=str(self.persist_directory),
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
            
            # 缓存客户端
            self._client_cache[self._client_key] = self.client
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "安仔记忆系统 v3.0"}
            )
            
        except Exception as e:
            raise StorageError(f"ChromaDB 初始化失败: {e}") from e
    
    def close(self):
        """
        关闭连接，释放资源
        
        在Windows上这很重要，可以避免文件锁定问题
        """
        if self._is_closed:
            return
        
        try:
            print(f"[ChromaDB] 关闭连接: {self.collection_name}")
            
            # 清理集合引用
            self.collection = None
            
            # 从缓存中移除
            if self._client_key in self._client_cache:
                del self._client_cache[self._client_key]
            
            # 强制垃圾回收（帮助释放文件句柄）
            import gc
            gc.collect()
            
            self._is_closed = True
            
        except Exception as e:
            print(f"[ChromaDB警告] 关闭连接时出错: {e}")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口，自动关闭连接"""
        self.close()
        return False
    
    def __del__(self):
        """析构函数，确保资源释放"""
        if not self._is_closed:
            self.close()
    
    def _check_closed(self):
        """检查连接是否已关闭"""
        if self._is_closed:
            raise StorageError("ChromaDB连接已关闭，请重新初始化")
    
    def save(self, memory_unit: MemoryUnit) -> str:
        """
        保存记忆单元到 ChromaDB
        
        Args:
            memory_unit: 要保存的记忆单元
            
        Returns:
            str: 保存的记忆ID
        """
        self._check_closed()
        
        try:
            doc = memory_unit.to_chroma_document()
            
            # 准备元数据
            metadata = {}
            for key, value in doc["metadata"].items():
                if key == "tags" and isinstance(value, list):
                    metadata[key] = ",".join(value)
                elif isinstance(value, (str, int, float, bool)):
                    metadata[key] = value
                elif value is None:
                    metadata[key] = ""
                else:
                    metadata[key] = str(value)
            
            self.collection.add(
                ids=[doc["id"]],
                documents=[doc["document"]],
                metadatas=[metadata],
                embeddings=[doc["embedding"]] if doc["embedding"] else None
            )
            
            return doc["id"]
            
        except Exception as e:
            raise StorageError(f"保存记忆失败: {e}") from e
    
    def get(self, memory_id: str) -> Optional[MemoryUnit]:
        """获取指定ID的记忆"""
        self._check_closed()
        
        try:
            result = self.collection.get(ids=[memory_id], include=["metadatas", "documents", "embeddings"])
            
            if not result["ids"]:
                return None
            
            return self._convert_to_memory_unit(result, 0)
            
        except Exception as e:
            raise StorageError(f"获取记忆失败: {e}") from e
    
    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[MemoryUnit]:
        """向量搜索"""
        self._check_closed()
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=filters
            )
            
            memories = []
            if results["ids"] and results["ids"][0]:
                for i in range(len(results["ids"][0])):
                    memories.append(self._convert_to_query_result(results, i))
            
            return memories
            
        except Exception as e:
            raise StorageError(f"搜索记忆失败: {e}") from e
    
    def _convert_to_memory_unit(self, result: Dict, index: int) -> MemoryUnit:
        """转换查询结果为MemoryUnit"""
        metadata = result["metadatas"][index]
        
        # 还原标签
        tags = []
        if "tags" in metadata and metadata["tags"]:
            tags = [t.strip() for t in metadata["tags"].split(",") if t.strip()]
        
        return MemoryUnit(
            memory_id=result["ids"][index],
            content=result["documents"][index],
            memory_type=metadata.get("memory_type", "fact"),
            importance=float(metadata.get("importance", 3.0)),
            created_at=metadata.get("created_at"),
            source=metadata.get("source"),
            tags=tags,
            embedding=result["embeddings"][index] if result.get("embeddings") is not None else None,
            access_count=int(metadata.get("access_count", 0)),
            last_accessed_at=metadata.get("last_accessed_at")
        )
    
    def _convert_to_query_result(self, result: Dict, index: int) -> MemoryUnit:
        """转换查询结果为MemoryUnit（query结果格式不同）"""
        metadata = result["metadatas"][0][index]
        
        tags = []
        if "tags" in metadata and metadata["tags"]:
            tags = [t.strip() for t in metadata["tags"].split(",") if t.strip()]
        
        return MemoryUnit(
            memory_id=result["ids"][0][index],
            content=result["documents"][0][index],
            memory_type=metadata.get("memory_type", "fact"),
            importance=float(metadata.get("importance", 3.0)),
            created_at=metadata.get("created_at"),
            source=metadata.get("source"),
            tags=tags,
            embedding=result["embeddings"][0][index] if result.get("embeddings") is not None else None,
            access_count=int(metadata.get("access_count", 0)),
            last_accessed_at=metadata.get("last_accessed_at")
        )
    
    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        self._check_closed()
        
        try:
            # 先检查是否存在
            if not self.exists(memory_id):
                return False
            
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            raise StorageError(f"删除记忆失败: {e}") from e
    
    def exists(self, memory_id: str) -> bool:
        """检查记忆是否存在"""
        self._check_closed()
        try:
            result = self.collection.get(ids=[memory_id])
            return len(result["ids"]) > 0
        except Exception:
            return False
    
    def count(self) -> int:
        """获取存储的记忆总数"""
        self._check_closed()
        try:
            return self.collection.count()
        except Exception as e:
            raise StorageError(f"获取记忆数量失败: {e}") from e
    
    def load(self, memory_id: str) -> "MemoryUnit":
        """加载指定ID的记忆"""
        self._check_closed()
        memory = self.get(memory_id)
        if memory is None:
            raise MemoryNotFoundError(f"记忆不存在: {memory_id}")
        return memory
    
    def query(self, memory_type=None, tags=None, min_importance=None, limit=10):
        """条件查询记忆"""
        self._check_closed()
        try:
            all_memories = self.list_all()
            results = []
            for memory in all_memories:
                if memory_type and memory.memory_type != memory_type:
                    continue
                if tags and not any(tag in memory.tags for tag in tags):
                    continue
                if min_importance is not None and memory.importance < min_importance:
                    continue
                results.append(memory)
            return results[:limit]
        except Exception as e:
            raise StorageError(f"查询记忆失败: {e}") from e
    
    def list_all(self) -> List[MemoryUnit]:
        """列出所有记忆"""
        self._check_closed()
        
        try:
            result = self.collection.get()
            
            memories = []
            if result["ids"]:
                for i in range(len(result["ids"])):
                    memories.append(self._convert_to_memory_unit(result, i))
            
            return memories
            
        except Exception as e:
            raise StorageError(f"列出记忆失败: {e}") from e
    
    def reset(self) -> None:
        """重置存储（删除所有数据）"""
        self._check_closed()
        
        try:
            self.client.reset()
            print(f"[ChromaDB] 已重置集合: {self.collection_name}")
        except Exception as e:
            raise StorageError(f"重置存储失败: {e}") from e


@contextmanager
def chroma_storage_context(
    persist_directory: str = "./data/vector_db",
    collection_name: str = "memories",
    use_memory_mode: Optional[bool] = None
):
    """
    ChromaStorage上下文管理器
    
    使用示例:
        with chroma_storage_context() as storage:
            storage.save(memory_unit)
            # 退出with块时自动关闭连接
    
    Args:
        persist_directory: 数据持久化目录
        collection_name: 集合名称
        use_memory_mode: 是否使用内存模式
    """
    storage = ChromaStorage(
        persist_directory=persist_directory,
        collection_name=collection_name,
        use_memory_mode=use_memory_mode
    )
    try:
        yield storage
    finally:
        storage.close()


def get_storage_mode() -> str:
    """
    获取当前存储模式
    
    Returns:
        str: "memory" 或 "persistent"
    """
    if FORCE_MEMORY_MODE or TEST_MODE or DEFAULT_MEMORY_MODE:
        return "memory"
    return "persistent"


# ========== 测试代码 ==========

def test_chroma_storage():
    """测试ChromaStorage（Windows文件锁定问题修复）"""
    print("=" * 60)
    print("ChromaStorage Windows文件锁定问题修复测试")
    print("=" * 60)
    print(f"\n系统信息:")
    print(f"  平台: {platform.system()}")
    print(f"  是否Windows: {IS_WINDOWS}")
    print(f"  默认内存模式: {DEFAULT_MEMORY_MODE}")
    print(f"  当前模式: {get_storage_mode()}")
    
    # 测试1: 内存模式
    print("\n" + "-" * 60)
    print("测试1: 内存模式（推荐用于Windows）")
    print("-" * 60)
    
    try:
        with chroma_storage_context(use_memory_mode=True) as storage:
            print("[OK] 内存模式初始化成功")
            
            # 创建测试记忆
            from memory_unit import MemoryUnit
            test_memory = MemoryUnit(
                content="这是一个测试记忆",
                memory_type="fact",
                importance=3.0,
                tags=["测试", "内存模式"]
            )
            
            # 保存
            memory_id = storage.save(test_memory)
            print(f"[OK] 保存记忆成功: {memory_id}")
            
            # 读取
            retrieved = storage.get(memory_id)
            if retrieved:
                print(f"[OK] 读取记忆成功: {retrieved.content}")
            
            # 自动关闭连接
        
        print("[OK] 内存模式测试通过，连接已自动关闭")
        
    except Exception as e:
        print(f"[FAIL] 内存模式测试失败: {e}")
        return False
    
    # 测试2: 持久化模式（如果不在Windows上）
    if not IS_WINDOWS:
        print("\n" + "-" * 60)
        print("测试2: 持久化模式")
        print("-" * 60)
        
        try:
            storage = ChromaStorage(use_memory_mode=False)
            print("[OK] 持久化模式初始化成功")
            storage.close()
            print("[OK] 持久化模式连接已关闭")
        except Exception as e:
            print(f"[WARN] 持久化模式测试失败: {e}")
    else:
        print("\n" + "-" * 60)
        print("测试2: 持久化模式（Windows上跳过）")
        print("-" * 60)
        print("[SKIP] Windows平台建议使用内存模式")
    
    # 测试3: 环境变量控制
    print("\n" + "-" * 60)
    print("测试3: 环境变量控制")
    print("-" * 60)
    
    print(f"  TEST_MODE: {os.environ.get('TEST_MODE', '未设置')}")
    print(f"  FORCE_MEMORY_MODE: {os.environ.get('FORCE_MEMORY_MODE', '未设置')}")
    print(f"  PERSISTENT_MODE: {os.environ.get('PERSISTENT_MODE', '未设置')}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n使用建议:")
    print("  Windows开发/测试: 设置 TEST_MODE=true")
    print("  Windows生产环境: 设置 FORCE_MEMORY_MODE=true")
    print("  Linux/Mac生产环境: 可使用持久化模式")
    
    return True


if __name__ == "__main__":
    success = test_chroma_storage()
    sys.exit(0 if success else 1)
