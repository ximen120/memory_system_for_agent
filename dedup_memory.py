#!/usr/bin/env python
"""去重：只保留最新的正确记忆"""
import sys
sys.path.insert(0, 'src')

import os
import json
from pathlib import Path

# 要保留的最新正确记忆
KEEP_CONTENTS = [
    '安哥喜欢喝普洱茶',
    '安哥出生于1984年2月28日',
    '安哥和安仔是一体两面',
]

def dedup():
    """去重"""
    data_dir = Path('data/auto_memory')
    files = sorted(data_dir.glob('*.json'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f'找到 {len(files)} 个文件，按时间排序')
    print()
    
    kept = {key: None for key in KEEP_CONTENTS}
    deleted = []
    
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            content = data.get('content', '')
            
            # 检查是否是需要保留的类型
            matched = False
            for key in KEEP_CONTENTS:
                if key in content:
                    matched = True
                    if kept[key] is None:
                        # 第一个（最新的）保留
                        kept[key] = (file.name, content[:60])
                        print(f'✅ 保留: {key} -> {file.name}')
                    else:
                        # 重复的删除
                        file.unlink()
                        deleted.append((file.name, content[:60]))
                        print(f'❌ 删除重复: {file.name}')
                    break
            
            if not matched:
                # 不属于保留类型的删除
                file.unlink()
                deleted.append((file.name, content[:40]))
                
        except Exception as e:
            print(f'处理失败: {file.name}, {e}')
    
    print()
    print('=' * 60)
    print('最终保留:')
    for key, info in kept.items():
        if info:
            print(f'  ✅ {key}: {info[0]}')
    print(f'\n共删除 {len(deleted)} 个重复/无效文件')

if __name__ == '__main__':
    dedup()
