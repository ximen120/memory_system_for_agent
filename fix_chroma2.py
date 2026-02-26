#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复ChromaDB API调用"""

with open('src/storage/chroma_storage.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复内存模式API
old_text = '''                self.client = chromadb.Client(
                    settings=Settings(
                        chroma_db_impl="duckdb+parquet",
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )'''

new_text = '''                self.client = chromadb.EphemeralClient(
                    settings=Settings(
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )'''

if old_text in content:
    content = content.replace(old_text, new_text)
    with open('src/storage/chroma_storage.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ ChromaDB API修复成功')
else:
    print('❌ 未找到目标文本')
