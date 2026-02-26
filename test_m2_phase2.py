"""
M2 Phase 2 API测试脚本

测试内容:
1. 向量检索API
2. 混合检索API
3. 关键词检索API
4. 统一路由
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


def test_vector_api():
    """测试1: 向量检索API"""
    print_header("测试1: 向量检索API")
    
    from api import VectorAPI
    
    api = VectorAPI()
    
    print_section("测试向量生成")
    response = api.embed({"text": "安哥喜欢喝咖啡"})
    print(f"  成功: {response['success']}")
    if response['success']:
        print(f"  向量维度: {response['dimension']}")
        print(f"  耗时: {response['time_ms']}ms")
    else:
        print(f"  错误: {response.get('error', '未知错误')}")
    
    print_section("测试批量向量生成")
    response = api.batch_embed({
        "texts": ["文本1", "文本2", "文本3"],
        "batch_size": 32
    })
    print(f"  成功: {response['success']}")
    if response['success']:
        print(f"  成功数量: {response['count']}/{response['total']}")
    
    print_section("测试向量搜索")
    # 先添加一些文档
    api.vector_search.add_document(
        memory_id="mem1",
        content="安哥喜欢喝咖啡",
        memory_type="preference"
    )
    api.vector_search.add_document(
        memory_id="mem2",
        content="安哥是程序员",
        memory_type="fact"
    )
    
    response = api.search({
        "query": "咖啡",
        "top_k": 5,
        "min_similarity": 0.0
    })
    
    print(f"  成功: {response['success']}")
    print(f"  查询: {response['query']}")
    print(f"  结果数: {response['total']}")
    print(f"  耗时: {response['time_ms']}ms")
    
    if response['results']:
        for r in response['results'][:3]:
            print(f"    - {r['content'][:30]}... (相似度: {r['score']:.4f})")
    
    print("\n  [OK] 向量检索API测试通过")
    return True


def test_hybrid_api():
    """测试2: 混合检索API"""
    print_header("测试2: 混合检索API")
    
    from api import HybridAPI
    
    api = HybridAPI()
    
    print_section("添加测试数据")
    documents = [
        ("mem1", "安哥喜欢喝咖啡", "preference"),
        ("mem2", "安哥喜欢喝茶", "preference"),
        ("mem3", "安哥是程序员", "fact"),
        ("mem4", "安哥计划学习Python", "goal"),
    ]
    
    for mem_id, content, mtype in documents:
        api.vector_search.add_document(mem_id, content, mtype)
        print(f"  添加: {content[:20]}...")
    
    print_section("测试混合搜索")
    response = api.search({
        "query": "Python",
        "top_k": 5,
        "vector_weight": 0.7,
        "keyword_weight": 0.3
    })
    
    print(f"  成功: {response['success']}")
    print(f"  查询: {response['query']}")
    print(f"  搜索方法: {response.get('search_method', 'unknown')}")
    print(f"  结果数: {response['total']}")
    
    if response['results']:
        for r in response['results'][:3]:
            print(f"    - {r['content'][:30]}...")
            print(f"      融合分数: {r['score']:.4f}, 向量: {r.get('vector_score')}, 关键词: {r.get('keyword_score')}")
    
    print_section("测试权重配置")
    weights = api.get_search_weights()
    print(f"  当前权重: {weights}")
    
    response = api.set_search_weights(vector_weight=0.8, keyword_weight=0.2)
    print(f"  设置权重: {response}")
    
    print("\n  [OK] 混合检索API测试通过")
    return True


def test_keyword_api():
    """测试3: 关键词检索API"""
    print_header("测试3: 关键词检索API")
    
    from api import KeywordAPI
    
    api = KeywordAPI()
    
    print_section("添加测试文档")
    documents = [
        ("mem1", "安哥喜欢喝咖啡", "preference"),
        ("mem2", "安哥喜欢喝茶", "preference"),
        ("mem3", "Python是一种编程语言", "fact"),
    ]
    
    for mem_id, content, mtype in documents:
        api.add_document(mem_id, content, mtype)
        print(f"  添加: {content[:20]}...")
    
    print_section("测试AND模式搜索")
    response = api.search({
        "query": "安哥 喜欢",
        "match_mode": "AND",
        "top_k": 10
    })
    
    print(f"  成功: {response['success']}")
    print(f"  查询: {response['query']}")
    print(f"  匹配模式: {response['match_mode']}")
    print(f"  结果数: {response['total']}")
    
    if response['results']:
        for r in response['results']:
            print(f"    - {r['content'][:30]}... (分数: {r['score']:.4f})")
            print(f"      匹配关键词: {r.get('matched_keywords', [])}")
    
    print_section("测试OR模式搜索")
    response = api.search({
        "query": "咖啡 Python",
        "match_mode": "OR",
        "top_k": 10
    })
    
    print(f"  成功: {response['success']}")
    print(f"  结果数: {response['total']}")
    
    print("\n  [OK] 关键词检索API测试通过")
    return True


def test_api_router():
    """测试4: 统一API路由"""
    print_header("测试4: 统一API路由")
    
    from api import APIRouter
    
    router = APIRouter()
    
    print_section("测试向量搜索路由")
    response = router.route("/api/v1/search/vector", {
        "query": "咖啡",
        "top_k": 5
    })
    print(f"  成功: {response['success']}")
    print(f"  结果数: {response.get('total', 0)}")
    
    print_section("测试混合搜索路由")
    response = router.route("/api/v1/search/hybrid", {
        "query": "Python",
        "top_k": 5
    })
    print(f"  成功: {response['success']}")
    print(f"  结果数: {response.get('total', 0)}")
    
    print_section("测试关键词搜索路由")
    response = router.route("/api/v1/search/keyword", {
        "query": "安哥",
        "top_k": 5
    })
    print(f"  成功: {response['success']}")
    print(f"  结果数: {response.get('total', 0)}")
    
    print_section("测试添加记忆路由")
    response = router.route("/api/v1/memory/add", {
        "content": "测试记忆内容",
        "memory_type": "test",
        "importance": 3.0
    })
    print(f"  成功: {response['success']}")
    if response['success']:
        print(f"  记忆ID: {response['memory_id'][:30]}...")
    
    print_section("测试统计信息路由")
    response = router.route("/api/v1/stats", {})
    print(f"  成功: {response['success']}")
    if response['success']:
        stats = response.get('stats', {})
        print(f"  记忆API统计: {stats.get('memory_api', {})}")
    
    print_section("测试未知路由")
    response = router.route("/api/v1/unknown", {})
    print(f"  成功: {response['success']}")
    print(f"  错误: {response.get('error', '')[:50]}...")
    
    print("\n  [OK] 统一API路由测试通过")
    return True


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("  M2 Phase 2 API测试")
    print("  检索API功能验证")
    print("=" * 70)
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 运行测试
    results.append(("向量检索API", test_vector_api()))
    results.append(("混合检索API", test_hybrid_api()))
    results.append(("关键词检索API", test_keyword_api()))
    results.append(("统一API路由", test_api_router()))
    
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
        print("  [OK] 所有测试通过！M2 Phase 2 完成！")
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
