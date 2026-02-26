#!/usr/bin/env python
"""保存重要信息"""
import sys
sys.path.insert(0, 'src')
from auto_memory_bridge import remember

# 保存重要信息
remember('安哥的儿子叫天天', 'fact', 5.0, ['家人', '儿子', '天天', '重要'])

print('✅ 已保存：安哥的儿子叫天天（重要性：5.0）')
