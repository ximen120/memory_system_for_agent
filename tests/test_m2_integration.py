"""
M2集成测试

测试M2向量检索模块的完整集成。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'libs'))

import tempfile
import shutil
import time
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


def test_m2_integration():
    """M2完整集成测试"""
    print_header("M2 Phase 集成测试")
    
    from api import UnifiedAPI
    
    tmpdir = tempfile.mkdtemp()
    
    try:
        api = UnifiedAPI(data_dir=tmpdir)
        
        print_section("1. 添加测试数据")
        test_data = [
            ("安哥喜欢喝咖啡", "preference", 4.0, ["咖啡", "喜好"]),
            ("安哥喜欢喝茶", "preference", 3.5, ["茶", "喜好"]),
            ("安哥是程序员", "fact", 3.5, ["职业", "编程"]),
            ("安哥计划学习Python", "goal", 4.5, ["Python", "学习", "计划"]),
            ("Python是一种编程语言", "fact", 3.0, ["Python", "编程"]),
            ("今天天气不错", "context", 2.0, ["天气"]),
        ]
        
        memory_ids = []
        for content, mtype, imp, tags in test_data:
            mid = api.remember(content, memory_type=mtype, importance=imp, tags=tags)
            memory_ids.append(mid)
            print(f"  [OK] 添加: {content[:20]}...")
        
        print(f"\n  共添加 {len(memory_ids)} 条记忆")
        
        print_section("2. 向量检索测试")
        start = time.time()
        results = api.search("咖啡", search_type="vector", top_k=5)
        elapsed = (time.time() - start) * 1000
        print(f"  查询: '咖啡'")
        print(f"  结果数: {len(results)}")
        print(f"  耗时: {elapsed:.2f}ms")
        
        if results:
            for r in results[:3]:
                print(f"    - {r.content[:30]}... (分数: {r.score:.4f})")
        
        print_section("3. 关键词检索测试")
        start = time.time()
        results = api.search("安哥 喜欢", search_type="keyword", top_k=5)
        elapsed = (time.time() - start) * 1000
        print(f"  查询: '安哥 喜欢'")
        print(f"  结果数: {len(results)}")
        print(f"  耗时: {elapsed:.2f}ms")
        
        print_section("4. 混合检索测试")
        start = time.time()
        results = api.search("Python", search_type="hybrid", top_k=5)
        elapsed = (time.time() - start) * 1000
        print(f"  查询: 'Python'")
        print(f"  结果数: {len(results)}")
        print(f"  耗时: {elapsed:.2f}ms")
        print(f"  搜索方法: {results[0].search_method if results else 'N/A'}")
        
        if results:
            for r in results[:3]:
                print(f"    - {r.content[:30]}... (分数: {r.score:.4f})")
        
        print_section("5. 自然语言查询测试")
        queries = [
            "查找关于咖啡的记忆",
            "安哥喜欢什么",
            "Python相关",
        ]
        
        for query in queries:
            results = api.query(query, top_k=3)
            print(f"  查询: '{query}'")
            print(f"  结果: {len(results)} 条")
        
        print_section("6. 记忆生命周期测试")
        # 更新
        mid = memory_ids[0]
        api.update(mid, content="安哥非常喜欢喝咖啡")
        memory = api.recall(mid)
        assert "非常" in memory["content"]
        print(f"  [OK] 更新记忆")
        
        # 查找相似
        similar = api.similar_to(mid, top_k=3)
        print(f"  [OK] 查找相似记忆: {len(similar)} 条")
        
        # 删除
        api.forget(memory_ids[1])
        memory = api.recall(memory_ids[1])
        assert memory is None
        print(f"  [OK] 删除记忆")
        
        print_section("7. 性能测试")
        # 批量搜索
        start = time.time()
        for _ in range(10):
            api.search("咖啡", top_k=5)
        elapsed = (time.time() - start) * 1000
        avg_time = elapsed / 10
        print(f"  10次搜索平均耗时: {avg_time:.2f}ms")
        
        print_section("8. 统计信息")
        stats = api.get_stats()
        print(f"  版本: {stats['version']}")
        print(f"  总记忆数: {stats['total_memories']}")
        print(f"  Embedding可用: {stats['embedding_available']}")
        print(f"  模型: {stats['embedding_model']}")
        
        print("\n" + "=" * 70)
        print("  [OK] M2集成测试全部通过！")
        print("=" * 70)
        
        return True
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_api_router():
    """测试API路由"""
    print_header("API路由集成测试")
    
    from api import APIRouter
    
    router = APIRouter()
    
    print_section("测试各API端点")
    
    # 添加记忆
    response = router.route("/api/v1/memory/add", {
        "content": "测试记忆",
        "memory_type": "test"
    })
    assert response["success"] is True
    print(f"  [OK] /api/v1/memory/add")
    
    # 搜索
    response = router.route("/api/v1/memory/search", {
        "query": "测试",
        "top_k": 5
    })
    assert "results" in response
    print(f"  [OK] /api/v1/memory/search")
    
    # 向量搜索
    response = router.route("/api/v1/search/vector", {
        "query": "测试",
        "top_k": 5
    })
    assert "results" in response
    print(f"  [OK] /api/v1/search/vector")
    
    # 混合搜索
    response = router.route("/api/v1/search/hybrid", {
        "query": "测试",
        "top_k": 5
    })
    assert "results" in response
    print(f"  [OK] /api/v1/search/hybrid")
    
    # 关键词搜索
    response = router.route("/api/v1/search/keyword", {
        "query": "测试",
        "top_k": 5
    })
    assert "results" in response
    print(f"  [OK] /api/v1/search/keyword")
    
    # 统计
    response = router.route("/api/v1/stats", {})
    assert response["success"] is True
    print(f"  [OK] /api/v1/stats")
    
    print("\n" + "=" * 70)
    print("  [OK] API路由测试通过！")
    print("=" * 70)
    
    return True


def test_performance():
    """性能测试"""
    print_header("M2性能测试")
    
    from api import UnifiedAPI
    
    tmpdir = tempfile.mkdtemp()
    
    try:
        api = UnifiedAPI(data_dir=tmpdir)
        
        # 添加测试数据
        print_section("准备测试数据")
        for i in range(50):
            api.remember(f"测试记忆内容 {i}", memory_type="test")
        print(f"  添加了 50 条测试数据")
        
        print_section("搜索性能测试")
        
        # 向量搜索
        times = []
        for _ in range(10):
            start = time.time()
            api.search("测试", search_type="vector", top_k=10)
            times.append((time.time() - start) * 1000)
        avg_time = sum(times) / len(times)
        print(f"  向量搜索平均耗时: {avg_time:.2f}ms")
        
        # 关键词搜索
        times = []
        for _ in range(10):
            start = time.time()
            api.search("测试", search_type="keyword", top_k=10)
            times.append((time.time() - start) * 1000)
        avg_time = sum(times) / len(times)
        print(f"  关键词搜索平均耗时: {avg_time:.2f}ms")
        
        # 混合搜索
        times = []
        for _ in range(10):
            start = time.time()
            api.search("测试", search_type="hybrid", top_k=10)
            times.append((time.time() - start) * 1000)
        avg_time = sum(times) / len(times)
        print(f"  混合搜索平均耗时: {avg_time:.2f}ms")
        
        print("\n" + "=" * 70)
        print("  [OK] 性能测试完成！")
        print("=" * 70)
        
        return True
        
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("  M2 Phase 集成测试套件")
    print("  向量检索模块完整测试")
    print("=" * 70)
    print(f"\n测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 运行测试
    try:
        results.append(("M2集成测试", test_m2_integration()))
    except Exception as e:
        print(f"\n  [FAIL] M2集成测试失败: {e}")
        results.append(("M2集成测试", False))
    
    try:
        results.append(("API路由测试", test_api_router()))
    except Exception as e:
        print(f"\n  [FAIL] API路由测试失败: {e}")
        results.append(("API路由测试", False))
    
    try:
        results.append(("性能测试", test_performance()))
    except Exception as e:
        print(f"\n  [FAIL] 性能测试失败: {e}")
        results.append(("性能测试", False))
    
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
        print("  [OK] 所有集成测试通过！M2 Phase 完成！")
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
