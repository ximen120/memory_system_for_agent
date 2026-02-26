#!/usr/bin/env python
"""验证最新记忆"""
import sys
sys.path.insert(0, 'src')
from auto_memory_bridge import recall

print('🔍 检索最新记忆...')
print()

# 查普洱茶
results = recall('普洱', top_k=3)
print('普洱茶:', len(results), '条')
for r in results:
    print('  -', r.get('content', ''))

print()

# 查生日
results = recall('1984', top_k=3)
print('1984生日:', len(results), '条')
for r in results:
    print('  -', r.get('content', ''))
