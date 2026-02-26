#!/usr/bin/env python
"""快速加载记忆系统"""
import sys
sys.path.insert(0, 'src')
from memory_initializer import load_memory

result = load_memory()
if result['ready']:
    print('✅ 记忆系统已启动')
    print(f"历史记忆: {result['stats'].get('recent_memories', 0)} 条")
else:
    print('❌ 启动失败')
