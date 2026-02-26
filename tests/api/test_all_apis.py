"""
API测试套件

测试所有API端点，包括：
1. UnifiedAPI
2. VectorAPI
3. HybridAPI
4. KeywordAPI
5. MemoryAPI
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'libs'))

import pytest
import tempfile
import shutil
from datetime import datetime


class TestUnifiedAPI:
    """测试 UnifiedAPI """
    
    @pytest.fixture
    def api(self):
        """提供API实例"""
        tmpdir = tempfile.mkdtemp()
        from api import UnifiedAPI
        api = UnifiedAPI(data_dir=tmpdir)
        yield api
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_remember(self, api):
        """测试记住功能"""
        memory_id = api.remember("测试内容", importance=4.0)
        assert memory_id is not None
        assert memory_id.startswith("mem_")
    
    def test_search(self, api):
        """测试搜索功能"""
        # 添加测试数据
        api.remember("安哥喜欢喝咖啡", memory_type="preference")
        api.remember("安哥是程序员", memory_type="fact")
        
        # 搜索
        results = api.search("咖啡", top_k=5)
        assert isinstance(results, list)
    
    def test_query(self, api):
        """测试自然语言查询"""
        api.remember("测试内容")
        results = api.query("查找测试")
        assert isinstance(results, list)
    
    def test_recall(self, api):
        """测试回忆功能"""
        memory_id = api.remember("测试内容")
        memory = api.recall(memory_id)
        assert memory is not None
        assert memory["content"] == "测试内容"
    
    def test_forget(self, api):
        """测试忘记功能"""
        memory_id = api.remember("测试内容")
        success = api.forget(memory_id)
        assert success is True
        
        # 确认已删除
        memory = api.recall(memory_id)
        assert memory is None
    
    def test_list_all(self, api):
        """测试列出所有记忆"""
        api.remember("记忆1")
        api.remember("记忆2")
        
        memories = api.list_all(limit=10)
        assert len(memories) >= 2
    
    def test_update(self, api):
        """测试更新功能"""
        memory_id = api.remember("原内容")
        success = api.update(memory_id, content="新内容")
        assert success is True
        
        memory = api.recall(memory_id)
        assert memory["content"] == "新内容"
    
    def test_get_stats(self, api):
        """测试统计功能"""
        stats = api.get_stats()
        assert "version" in stats
        assert "total_memories" in stats


class TestVectorAPI:
    """测试 VectorAPI """
    
    @pytest.fixture
    def api(self):
        """提供API实例"""
        from api import VectorAPI
        return VectorAPI()
    
    def test_embed(self, api):
        """测试向量生成"""
        response = api.embed({"text": "测试文本"})
        assert "success" in response
        
        if response["success"]:
            assert "embedding" in response
            assert "dimension" in response
    
    def test_batch_embed(self, api):
        """测试批量向量生成"""
        response = api.batch_embed({
            "texts": ["文本1", "文本2"],
            "batch_size": 32
        })
        assert "success" in response
        
        if response["success"]:
            assert "embeddings" in response
            assert response["count"] == 2
    
    def test_search_validation(self, api):
        """测试搜索参数验证"""
        # 缺少query参数
        response = api.search({})
        assert response["success"] is False
        assert "error" in response
        
        # 空query
        response = api.search({"query": ""})
        assert response["success"] is False
        
        # 无效的top_k
        response = api.search({"query": "test", "top_k": -1})
        assert response["success"] is False


class TestHybridAPI:
    """测试 HybridAPI """
    
    @pytest.fixture
    def api(self):
        """提供API实例"""
        from api import HybridAPI
        return HybridAPI()
    
    def test_search(self, api):
        """测试混合搜索"""
        # 添加测试数据
        api.vector_search.add_document("mem1", "测试内容1", "fact")
        api.vector_search.add_document("mem2", "测试内容2", "fact")
        
        response = api.search({
            "query": "测试",
            "top_k": 5
        })
        
        assert "success" in response
        assert "results" in response
        assert "search_method" in response
    
    def test_weights(self, api):
        """测试权重配置"""
        # 获取权重
        weights = api.get_search_weights()
        assert "vector_weight" in weights
        assert "keyword_weight" in weights
        
        # 设置权重
        response = api.set_search_weights(vector_weight=0.8, keyword_weight=0.2)
        assert response["success"] is True
        
        # 验证设置
        weights = api.get_search_weights()
        assert weights["vector_weight"] == 0.8
        assert weights["keyword_weight"] == 0.2


class TestKeywordAPI:
    """测试 KeywordAPI """
    
    @pytest.fixture
    def api(self):
        """提供API实例"""
        from api import KeywordAPI
        api = KeywordAPI()
        # 添加测试数据
        api.add_document("mem1", "安哥喜欢喝咖啡", "preference")
        api.add_document("mem2", "安哥喜欢喝茶", "preference")
        api.add_document("mem3", "Python编程", "fact")
        return api
    
    def test_and_search(self, api):
        """测试AND模式搜索"""
        response = api.search({
            "query": "安哥 喜欢",
            "match_mode": "AND",
            "top_k": 10
        })
        
        assert response["success"] is True
        assert len(response["results"]) > 0
    
    def test_or_search(self, api):
        """测试OR模式搜索"""
        response = api.search({
            "query": "咖啡 Python",
            "match_mode": "OR",
            "top_k": 10
        })
        
        assert response["success"] is True
        assert len(response["results"]) >= 2
    
    def test_document_management(self, api):
        """测试文档管理"""
        # 添加文档
        success = api.add_document("mem_test", "测试文档", "test")
        assert success is True
        
        # 删除文档
        success = api.delete_document("mem_test")
        assert success is True
        
        # 确认删除
        assert api.get_document_count() == 3  # 原始3个


class TestMemoryAPI:
    """测试 MemoryAPI """
    
    @pytest.fixture
    def api(self):
        """提供API实例"""
        tmpdir = tempfile.mkdtemp()
        from api import MemoryAPI
        api = MemoryAPI(data_dir=tmpdir)
        yield api
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_add_memory(self, api):
        """测试添加记忆"""
        memory_id = api.add_memory(
            content="测试内容",
            memory_type="fact",
            importance=3.0,
            tags=["测试"]
        )
        assert memory_id is not None
    
    def test_search_memories(self, api):
        """测试搜索记忆"""
        api.add_memory("安哥喜欢喝咖啡", "preference")
        api.add_memory("安哥是程序员", "fact")
        
        results = api.search("咖啡", search_type="keyword", top_k=5)
        assert len(results) > 0
    
    def test_memory_lifecycle(self, api):
        """测试记忆完整生命周期"""
        # 添加
        memory_id = api.add_memory("原内容")
        
        # 获取
        memory = api.get_memory(memory_id)
        assert memory is not None
        
        # 更新
        api.update_memory(memory_id, content="新内容")
        memory = api.get_memory(memory_id)
        assert memory.content == "新内容"
        
        # 删除
        success = api.delete_memory(memory_id)
        assert success is True
        
        # 确认删除
        memory = api.get_memory(memory_id)
        assert memory is None


class TestAPIIntegration:
    """测试API集成"""
    
    @pytest.fixture
    def unified_api(self):
        """提供UnifiedAPI实例"""
        tmpdir = tempfile.mkdtemp()
        from api import UnifiedAPI
        api = UnifiedAPI(data_dir=tmpdir)
        yield api
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_end_to_end_workflow(self, unified_api):
        """测试端到端工作流"""
        # 1. 添加多条记忆
        mid1 = unified_api.remember("安哥喜欢喝咖啡", importance=4.0)
        mid2 = unified_api.remember("安哥喜欢喝茶", importance=3.5)
        mid3 = unified_api.remember("安哥是程序员", importance=3.0)
        
        # 2. 搜索
        results = unified_api.search("喜欢", top_k=10)
        assert len(results) >= 2
        
        # 3. 查询特定记忆
        memory = unified_api.recall(mid1)
        assert memory is not None
        assert "咖啡" in memory["content"]
        
        # 4. 查找相似记忆
        similar = unified_api.similar_to(mid1, top_k=3)
        assert isinstance(similar, list)
        
        # 5. 更新记忆
        unified_api.update(mid1, content="安哥非常喜欢喝咖啡")
        memory = unified_api.recall(mid1)
        assert "非常" in memory["content"]
        
        # 6. 删除记忆
        unified_api.forget(mid2)
        memory = unified_api.recall(mid2)
        assert memory is None
        
        # 7. 获取统计
        stats = unified_api.get_stats()
        assert stats["total_memories"] >= 2
    
    def test_search_types(self, unified_api):
        """测试不同搜索类型"""
        # 添加测试数据
        unified_api.remember("Python编程语言")
        unified_api.remember("Java编程语言")
        
        # 向量搜索
        results_vector = unified_api.search("编程", search_type="vector")
        
        # 关键词搜索
        results_keyword = unified_api.search("编程", search_type="keyword")
        
        # 混合搜索
        results_hybrid = unified_api.search("编程", search_type="hybrid")
        
        # 自动选择
        results_auto = unified_api.search("编程", search_type="auto")
        
        # 验证都是列表
        assert isinstance(results_vector, list)
        assert isinstance(results_keyword, list)
        assert isinstance(results_hybrid, list)
        assert isinstance(results_auto, list)
    
    def test_natural_language_queries(self, unified_api):
        """测试自然语言查询"""
        unified_api.remember("安哥喜欢喝咖啡")
        
        # 不同形式的查询
        queries = [
            "查找咖啡",
            "搜索关于咖啡的记忆",
            "安哥喜欢什么",
        ]
        
        for query in queries:
            results = unified_api.query(query)
            assert isinstance(results, list)


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("API测试套件")
    print("=" * 70)
    
    # 使用pytest运行测试
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode


if __name__ == "__main__":
    import sys
    sys.exit(run_all_tests())
