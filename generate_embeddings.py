"""批量为迁移数据生成embedding向量"""
import sys
import os
import logging

logging.disable(logging.CRITICAL)
os.environ['TRANSFORMERS_VERBOSITY'] = 'error'

sys.path.insert(0, r'D:\projects\memory_system_v3\src')
from api.memory_api import MemoryAPI

print("初始化MemoryAPI（含模型加载）...")
api = MemoryAPI(data_dir=r'D:\AnZai_JieYue\memory_v3')
count = len(api._memories)
print(f"已加载 {count} 条记忆")

if not api.embedding_service.is_available():
    print("Embedding服务不可用，无法生成向量")
    sys.exit(1)

print(f"开始为 {count} 条记忆生成embedding...")
success = 0
fail = 0

for i, (mid, mem) in enumerate(api._memories.items()):
    try:
        content = mem.content if hasattr(mem, 'content') else str(mem)
        embedding = api.embedding_service.generate(content[:512])
        if embedding:
            api.vector_search.add_document(
                memory_id=mid,
                content=content,
                embedding=embedding,
                memory_type=getattr(mem, 'memory_type', 'fact'),
                metadata={"importance": getattr(mem, 'importance', 3.0)}
            )
            success += 1
    except Exception as e:
        fail += 1
    
    if (i + 1) % 50 == 0:
        print(f"  进度: {i+1}/{count} (成功:{success} 失败:{fail})")

print(f"\n完成! 成功:{success} 失败:{fail}")

# 验证搜索
results = api.search('隆中对', top_k=3)
print(f'搜索"隆中对": {len(results)}条结果')
for r in results[:3]:
    c = r.content.replace('\n', ' ')[:80]
    print(f'  - {c}...')
