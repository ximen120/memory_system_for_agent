#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复ChromaStorage的抽象方法"""

with open('src/storage/chroma_storage.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到delete方法的位置
old_text = '''    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        self._check_closed()
        
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            raise StorageError(f"删除记忆失败: {e}") from e
    
    def list_all(self) -> List[MemoryUnit]:'''

new_text = '''    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        self._check_closed()
        
        try:
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
    
    def list_all(self) -> List[MemoryUnit]:'''

if old_text in content:
    content = content.replace(old_text, new_text)
    with open('src/storage/chroma_storage.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ 文件更新成功')
else:
    print('❌ 未找到目标文本')
    # 尝试查找近似文本
    if 'def delete' in content:
        print('  - 但找到了def delete')
    if 'def list_all' in content:
        print('  - 但找到了def list_all')
