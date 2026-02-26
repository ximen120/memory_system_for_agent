#!/usr/bin/env python
"""检查生日记忆"""
import sys
sys.path.insert(0, 'src')
from auto_memory_bridge import recall

results = recall('生日', top_k=5)
print('找到', len(results), '条生日相关记忆:')
for r in results:
    print('  -', r.get('content', ''))
