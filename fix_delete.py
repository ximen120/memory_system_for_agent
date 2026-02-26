#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复delete方法"""

with open('src/storage/chroma_storage.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复delete方法
old_text = '''    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        self._check_closed()
        
        try:
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            raise StorageError(f"删除记忆失败: {e}") from e'''

new_text = '''    def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        self._check_closed()
        
        try:
            # 先检查是否存在
            if not self.exists(memory_id):
                return False
            
            self.collection.delete(ids=[memory_id])
            return True
        except Exception as e:
            raise StorageError(f"删除记忆失败: {e}") from e'''

if old_text in content:
    content = content.replace(old_text, new_text)
    with open('src/storage/chroma_storage.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ delete方法修复成功')
else:
    print('❌ 未找到目标文本')
