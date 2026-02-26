#!/usr/bin/env python
"""检查记忆"""
import sys
sys.path.insert(0, 'src')
from auto_memory_bridge import recall

results = recall('安哥', top_k=5)
print(f'找到 {len(results)} 条关于安哥的记忆:')
for r in results:
    content = r['content'][:60]
    print(f'  - {content}')
