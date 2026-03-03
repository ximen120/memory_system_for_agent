import sys
import os
import logging

logging.disable(logging.CRITICAL)
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'

sys.path.insert(0, r'D:\projects\memory_system_v3\src')
from api.memory_api import MemoryAPI

api = MemoryAPI(data_dir=r'D:\AnZai_JieYue\memory_v3')
count = len(api._memories)
print(f'加载: {count}条')

# 测试不同搜索方式
for st in ['keyword', 'vector', 'hybrid']:
    try:
        results = api.search('隆中对', top_k=3, search_type=st)
        print(f'搜索({st}): {len(results)}条')
        for r in results[:2]:
            c = r.content.replace('\n', ' ')[:60]
            print(f'  - {c}...')
    except Exception as e:
        print(f'搜索({st}): 失败 - {e}')

# 直接在_memories中搜
print(f'\n直接内存搜索"隆中对":')
for mid, mem in api._memories.items():
    content = mem.content if hasattr(mem, 'content') else str(mem)
    if '隆中对' in content:
        print(f'  找到: {mid} - {content[:60]}...')
        break
