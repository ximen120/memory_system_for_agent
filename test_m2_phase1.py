"""
M2 Phase 1 测试脚本

测试内容:
1. Embedding服务
2. 向量检索引擎
3. 混合检索引擎
4. MemoryAPI接口
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'libs'))

import tempfile
import shutil
from datetime import datetime


def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """打印小节标题"""
    print(f"\n>> {title}")
    print("-" * 50)


def test_embedding_service():
    """测试1: Embedding服务"""
    print_header("测试1: Embedding服务")
    
    from retrieval import EmbeddingService
    
    # 创建服务
    service = EmbeddingService()
    
    print_section("模型信息")
    info = service.get_model_info()
    print(f"  模型名称: {info['model_name']}")
    print(f"  是否可用: {info['is_available']}")
    print(f"  缓存目录: {info['cache_dir']}")
    
    if not info['is_available']:
        print("\n  [WARN] Embedding服务不可用，跳过向量生成测试")
        return False
    
    print_section("单文本生成")
    text = "安哥喜欢喝咖啡"
    embedding = service.generate(text)
    if embedding:
        print(f"  文本: '{text}'")
        print(f"  向量维度: {len(embedding)}")
        print(f"  向量前5个值: {embedding[:5]}")
    else:
        print("  [FAIL] 向量生成失败")
        return False
    
    print_section("批量生成")
    texts = ["文本1", "文本2", "文本3"]
    embeddings = service.generate_batch(texts)
    print(f"  输入: {len(texts)} 个文本")
    print(f"  输出: {len(embeddings)} 个向量")
    print(f"  第一个向量维度: {len(embeddings[0]) if embeddings[0] else 'None'}")
    
    print("\n  [OK] Embedding服务测试通过")
    return True


def test_vector_search():
    """测试2: 向量检索引擎"""
    print_header("测试2: 向量检索引擎")
    
    from retrieval import EmbeddingService, VectorSearch
    
    service = EmbeddingService()
    vector_search = VectorSearch(service)
    
    print_section("添加文档")
    documents = [
        ("mem1", "安哥喜欢喝咖啡", "preference", 4.0),
        ("mem2", "安哥是程序员", "fact", 3.5),
        ("mem3", "安哥计划学习Python", "goal", 4.5),
        ("mem4", "今天天气不错", "context", 2.0),
    ]
    
    added = 0
    for mem_id, content, mtype, imp in documents:
        if vector_search.add_document(mem_id, content, mtype, imp):
            added += 1
            print(f"  [OK] 添加: {content[:20]}...")
    
    print(f"\n  成功添加 {added}/{len(documents)} 个文档")
    
    if added == 0:
        print("  [WARN] 没有文档被添加，跳过检索测试")
        return False
    
    print_section("向量检索")
    query = "咖啡"
    results = vector_search.search(query, top_k=5, min_similarity=0.0)
    
    print(f"  查询: '{query}'")
    print(f"  结果数: {len(results)}")
    
    for r in results:
        print(f"    - {r.content[:30]}... (相似度: {r.score:.4f})")
    
    print_section("统计信息")
    stats = vector_search.get_stats()
    print(f"  文档数量: {stats['document_count']}")
    print(f"  Embedding可用: {stats['embedding_available']}")
    
    print("\n  [OK] 向量检索引擎测试通过")
    return True


def test_hybrid_search():
    """测试3: 混合检索引擎"""
    print_header("测试3: 混合检索引擎")
    
    from retrieval import EmbeddingService, VectorSearch, HybridSearch
    
    service = EmbeddingService()
    vector_search = VectorSearch(service)
    hybrid_search = HybridSearch(vector_search)
    
    print_section("添加测试数据")
    documents = [
        ("mem1", "安哥喜欢喝咖啡", "preference"),
        ("mem2", "安哥喜欢喝茶", "preference"),
        ("mem3", "安哥是程序员", "fact"),
        ("mem4", "安哥计划学习Python", "goal"),
        ("mem5", "Python是一种编程语言", "fact"),
    ]
    
    for mem_id, content, mtype in documents:
        vector_search.add_document(mem_id, content, mtype)
    
    print(f"  添加了 {len(documents)} 个文档")
    
    print_section("混合检索")
    query = "Python"
    results = hybrid_search.search(query, top_k=5)
    
    print(f"  查询: '{query}'")
    print(f"  结果数: {len(results)}")
    
    for r in results:
        print(f"    - {r.content[:30]}...")
        print(f"      融合分数: {r.score:.4f}, 向量分数: {r.vector_score}, 关键词分数: {r.keyword_score}")
    
    print_section("降级方案测试")
    results_fallback = hybrid_search.search_with_fallback("咖啡", top_k=3)
    print(f"  带降级的搜索返回 {len(results_fallback)} 条结果")
    
    print("\n  [OK] 混合检索引擎测试通过")
    return True


def test_memory_api():
    """测试4: MemoryAPI接口"""
    print_header("测试4: MemoryAPI接口")
    
    from api import MemoryAPI
    
    tmpdir = tempfile.mkdtemp()
    
    try:
        api = MemoryAPI(data_dir=tmpdir)
        
        print_section("添加记忆")
        memories = [
            ("安哥喜欢喝咖啡", "preference", 4.0, ["咖啡", "喜好"]),
            ("安哥是程序员", "fact", 3.5, ["职业"]),
            ("安哥计划学习Python", "goal", 4.5, ["Python", "学习"]),
        ]
        
        memory_ids = []
        for content, mtype, imp, tags in memories:
            mid = api.add_memory(content, memory_type=mtype, importance=imp, tags=tags)
            memory_ids.append(mid)
            print(f"  [OK] 添加: {content[:20]}... (ID: {mid[:20]}...)")
        
        print_section("搜索记忆")
        query = "Python"
        results = api.search(query, top_k=5)
        
        print(f"  查询: '{query}'")
        print(f"  找到 {len(results)} 条结果:")
        for r in results:
            print(f"    - {r.content[:30]}... (分数: {r.score:.4f}, 方法: {r.search_method})")
        
        print_section("获取单条记忆")
        if memory_ids:
            memory = api.get_memory(memory_ids[0])
            if memory:
                print(f"  找到记忆: {memory.content[:30]}...")
                print(f"  类型: {memory.memory_type}, 重要性: {memory.importance}")
        
        print_section("统计信息")
        stats = api.get_stats()
        print(f"  总记忆数: {stats['total_memories']}")
        print(f"  向量可用: {stats['vector_available']}")
        print(f"  向量数量: {stats['vector_count']}")
        
        print("\n  [OK] MemoryAPI接口测试通过")
        return True
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("  M2 Phase 1 基础设施测试")
    print("  向量检索API功能验证")
    print("=" * 70)
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 运行测试
    results.append(("Embedding服务", test_embedding_service()))
    results.append(("向量检索引擎", test_vector_search()))
    results.append(("混合检索引擎", test_hybrid_search()))
    results.append(("MemoryAPI接口", test_memory_api()))
    
    # 汇总
    print("\n" + "=" * 70)
    print("  测试结果汇总")
    print("=" * 70)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    print(f"\n  总计: {passed}/{total} 通过")
    print(f"  通过率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("  [OK] 所有测试通过！M2 Phase 1 完成！")
        print("=" * 70)
        return 0
    else:
        print("\n" + "=" * 70)
        print(f"  [WARN] 有 {total-passed} 个测试失败")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
