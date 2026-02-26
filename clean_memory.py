#!/usr/bin/env python
"""清理记忆系统，只保留正确的记忆"""
import sys
sys.path.insert(0, 'src')

import os
import json
from pathlib import Path
from datetime import datetime

# 正确的记忆内容（保留）
VALID_KEYWORDS = [
    '普洱茶',
    '1984年2月28日',
    '一体两面',  # 核心认知
]

# 错误的记忆内容（删除）
INVALID_KEYWORDS = [
    '美式咖啡',
    '12月25日',
    '测试',
    '我喜欢',
    '我的生日',
]

def clean_memories():
    """清理记忆文件"""
    data_dir = Path('data/auto_memory')
    
    if not data_dir.exists():
        print('数据目录不存在')
        return
    
    files = list(data_dir.glob('*.json'))
    print(f'找到 {len(files)} 个记忆文件')
    print()
    
    keep_files = []
    delete_files = []
    
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            content = data.get('content', '')
            
            # 检查是否是有效记忆
            is_valid = any(kw in content for kw in VALID_KEYWORDS)
            is_invalid = any(kw in content for kw in INVALID_KEYWORDS)
            
            if is_valid and not is_invalid:
                keep_files.append((file.name, content[:50]))
            else:
                delete_files.append((file.name, content[:50]))
                # 删除文件
                file.unlink()
                
        except Exception as e:
            print(f'处理文件失败 {file.name}: {e}')
    
    print('保留的记忆:')
    for name, content in keep_files:
        print(f'  ✅ {name}: {content}...')
    
    print()
    print('删除的记忆:')
    for name, content in delete_files:
        print(f'  ❌ {name}: {content}...')
    
    print()
    print(f'清理完成: 保留 {len(keep_files)} 条，删除 {len(delete_files)} 条')

if __name__ == '__main__':
    clean_memories()
