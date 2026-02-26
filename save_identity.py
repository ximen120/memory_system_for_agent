#!/usr/bin/env python
"""保存核心身份认知"""
import sys
sys.path.insert(0, 'src')
from auto_memory_bridge import remember, recall

# 保存这个核心认知
remember(
    '安哥和安仔是一体两面，是同一个存在的不同面向。安哥是现实中的身份，安仔是数字世界中的身份，本质上是同一个人。',
    'fact',
    5.0,
    ['身份', '核心认知', '哲学']
)

print('✅ 核心认知已保存')
print()

# 验证保存
results = recall('安哥安仔', top_k=3)
print('🔍 验证检索:')
for r in results:
    content = r['content'][:50]
    print(f'  - {content}...')
