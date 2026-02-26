#!/usr/bin/env python
"""检查1984生日记忆"""
import sys
sys.path.insert(0, 'src')
from auto_memory_bridge import recall

results = recall('1984', top_k=5)
print('找到', len(results), '条1984相关记忆:')
for r in results:
    print('  -', r.get('content', ''))
