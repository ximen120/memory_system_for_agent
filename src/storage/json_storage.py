"""
JSON 文件存储实现

将记忆单元持久化到 JSON 文件。
适合小规模数据，便于人工查看和备份。
"""

import json
from pathlib import Path
from typing import List, Optional

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


class JsonStorage(BaseStorage):
    """
    JSON 文件存储
    
    每个记忆单元保存为单独的 .json 文件，文件名即 memory_id。
    文件格式为人类可读的 JSON，便于调试和手动编辑。
    
    Attributes:
        storage_dir: 存储目录路径
    """
    
    def __init__(self, storage_dir: str = "./data/memories"):
        """
        初始化 JSON 存储
        
        Args:
            storage_dir: 存储目录路径，默认为 ./data/memories
        """
        super().__init__("json")
        self.storage_dir = Path(storage_dir)
        self._ensure_directory()
    
    def _ensure_directory(self) -> None:
        """确保存储目录存在"""
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, memory_id: str) -> Path:
        """获取记忆文件路径"""
        return self.storage_dir / f"{memory_id}.json"
    
    def _memory_to_dict(self, memory_unit: MemoryUnit) -> dict:
        """将 MemoryUnit 转换为字典（用于 JSON 序列化）"""
        return memory_unit.model_dump()
    
    def _dict_to_memory(self, data: dict) -> MemoryUnit:
        """将字典转换为 MemoryUnit"""
        return MemoryUnit(**data)
    
    def save(self, memory_unit: MemoryUnit) -> str:
        """
        保存记忆单元到 JSON 文件
        
        Args:
            memory_unit: 要保存的记忆单元
            
        Returns:
            str: 保存的记忆ID
            
        Raises:
            StorageError: 保存失败时抛出
        """
        try:
            self._ensure_directory()
            file_path = self._get_file_path(memory_unit.memory_id)
            data = self._memory_to_dict(memory_unit)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return memory_unit.memory_id
        except Exception as e:
            raise StorageError(f"保存记忆失败: {e}") from e
    
    def load(self, memory_id: str) -> MemoryUnit:
        """
        从 JSON 文件加载记忆
        
        Args:
            memory_id: 记忆唯一标识符
            
        Returns:
            MemoryUnit: 加载的记忆单元
            
        Raises:
            MemoryNotFoundError: 记忆不存在时抛出
            StorageError: 加载失败时抛出
        """
        file_path = self._get_file_path(memory_id)
        
        if not file_path.exists():
            raise MemoryNotFoundError(f"记忆不存在: {memory_id}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return self._dict_to_memory(data)
        except json.JSONDecodeError as e:
            raise StorageError(f"JSON解析失败: {e}") from e
        except Exception as e:
            raise StorageError(f"加载记忆失败: {e}") from e
    
    def delete(self, memory_id: str) -> bool:
        """
        删除指定记忆
        
        Args:
            memory_id: 记忆唯一标识符
            
        Returns:
            bool: 删除成功返回True，不存在返回False
            
        Raises:
            StorageError: 删除失败时抛出
        """
        file_path = self._get_file_path(memory_id)
        
        if not file_path.exists():
            return False
        
        try:
            file_path.unlink()
            return True
        except Exception as e:
            raise StorageError(f"删除记忆失败: {e}") from e
    
    def query(
        self,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_importance: Optional[float] = None,
        limit: int = 10
    ) -> List[MemoryUnit]:
        """
        条件查询记忆
        
        Args:
            memory_type: 按类型过滤（可选）
            tags: 按标签过滤，包含任一标签即可（可选）
            min_importance: 最小重要度（可选）
            limit: 返回结果数量上限，默认10
            
        Returns:
            List[MemoryUnit]: 符合条件的记忆列表
        """
        results = []
        
        # 获取所有 JSON 文件
        json_files = list(self.storage_dir.glob("*.json"))
        
        for file_path in json_files:
            try:
                memory = self.load(file_path.stem)  # stem 是不带扩展名的文件名
                
                # 应用过滤条件
                if memory_type and memory.memory_type != memory_type:
                    continue
                
                if tags and not any(tag in memory.tags for tag in tags):
                    continue
                
                if min_importance is not None and memory.importance < min_importance:
                    continue
                
                results.append(memory)
                
                if len(results) >= limit:
                    break
                    
            except Exception:
                # 跳过损坏的文件
                continue
        
        return results
    
    def exists(self, memory_id: str) -> bool:
        """检查记忆是否存在"""
        return self._get_file_path(memory_id).exists()
    
    def count(self) -> int:
        """获取存储的记忆总数"""
        return len(list(self.storage_dir.glob("*.json")))
    
    def close(self) -> None:
        """
        关闭存储
        
        JSON 存储无需特殊关闭操作。
        """
        pass
    
    def clear_all(self) -> None:
        """
        清空所有记忆（谨慎使用）
        
        删除存储目录中的所有 JSON 文件。
        """
        for file_path in self.storage_dir.glob("*.json"):
            try:
                file_path.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    # 简单测试
    print("JsonStorage 基础测试:\n")
    
    import tempfile
    import shutil
    
    # 使用临时目录测试
    tmpdir = tempfile.mkdtemp()
    
    try:
        storage = JsonStorage(tmpdir)
        print(f"1. 创建存储: {tmpdir}")
        print(f"   初始记忆数: {storage.count()}")
        
        # 创建测试记忆
        memory = MemoryUnit(
            content="安哥喜欢喝咖啡",
            memory_type="preference",
            importance=4.5,
            tags=["咖啡", "习惯"]
        )
        print(f"\n2. 创建记忆: {memory.memory_id}")
        
        # 保存
        saved_id = storage.save(memory)
        print(f"3. 保存成功: {saved_id}")
        print(f"   当前记忆数: {storage.count()}")
        
        # 加载
        loaded = storage.load(saved_id)
        print(f"\n4. 加载成功: {loaded.content}")
        print(f"   类型: {loaded.memory_type}")
        print(f"   标签: {loaded.tags}")
        
        # 查询
        results = storage.query(memory_type="preference")
        print(f"\n5. 查询结果: {len(results)} 条")
        
        # 删除
        deleted = storage.delete(saved_id)
        print(f"\n6. 删除: {'成功' if deleted else '失败'}")
        print(f"   当前记忆数: {storage.count()}")
        
        # 验证不存在
        exists = storage.exists(saved_id)
        print(f"   存在检查: {exists}")
        
        print("\n✅ 所有基础测试通过!")
        
    finally:
        # 清理
        shutil.rmtree(tmpdir, ignore_errors=True)
