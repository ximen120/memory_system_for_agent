import sys
import os
import logging

# 静默所有日志
logging.disable(logging.CRITICAL)
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'

sys.path.insert(0, r'D:\projects\memory_system_v3\src')
from api.memory_api import MemoryAPI

api = MemoryAPI(data_dir=r'D:\AnZai_JieYue\memory_v3')
count = len(api._memories)
print(f'加载记忆数: {count}')

results = api.search('隆中对', top_k=3)
print(f'搜索"隆中对": {len(results)}条结果')
for r in results[:3]:
    c = r.content.replace('\n', ' ')[:80]
    print(f'  - {c}...')

results2 = api.search('安哥', top_k=3)
print(f'搜索"安哥": {len(results2)}条结果')
for r in results2[:3]:
    c = r.content.replace('\n', ' ')[:80]
    print(f'  - {c}...')

print(f'\n{"="*40}')
if count >= 440:
    print(f'回归测试通过! {count}条记忆已就绪')
else:
    print(f'回归测试失败! 只有{count}条')
