"""
M2向量检索集成测试

测试向量检索、相似度计算、混合检索的协同工作。
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "retrieval"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "storage"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src" / "core"))

import os
os.environ['TEST_MODE'] = 'true'

import pytest

from retrieval_api import RetrievalAPI, SearchMode, SearchRequest
from vector_search import VectorSearch
from keyword_search import KeywordSearch
from similarity import SimilarityService, SimilarityMetric
from embedding_service import EmbeddingService
import pytest


class TestM2SimilarityIntegration:
    """M2相似度计算集成测试"""
    
    @pytest.fixture
    def service(self):
        """提供SimilarityService实例"""
        return SimilarityService()
    
    def test_similarity_with_vectors(self, service):
        """测试向量相似度计算"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        
        result = service.compute(vec1, vec2, SimilarityMetric.COSINE)
        
        assert result.score == pytest.approx(0.0, abs=1e-6)
        assert result.normalized_score == pytest.approx(0.5, abs=1e-6)
    
    def test_batch_similarity(self, service):
        """测试批量相似度计算"""
        query = [1.0, 0.0, 0.0]
        candidates = [
            [0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
        ]
        
        results = service.compute_batch(query, candidates, top_k=2)
        
        assert len(results) == 2
        assert results[0][0] == 1  # 最相似的应该是索引1
    
    def test_similarity_matrix(self, service):
        """测试相似度矩阵"""
        vectors = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],
        ]
        
        matrix = service.compute_matrix(vectors)
        
        assert len(matrix) == 3
        assert len(matrix[0]) == 3
        assert matrix[0][2] == pytest.approx(1.0, abs=1e-6)


class TestM2KeywordSearchIntegration:
    """M2关键词检索集成测试"""
    
    @pytest.fixture
    def keyword_search(self):
        """提供KeywordSearch实例"""
        return KeywordSearch(use_tfidf=True)
    
    def test_add_and_search(self, keyword_search):
        """测试添加和搜索"""
        keyword_search.add_document("doc1", "我喜欢喝咖啡")
        keyword_search.add_document("doc2", "我喜欢喝茶")
        keyword_search.add_document("doc3", "今天天气很好")
        
        results = keyword_search.search("咖啡", top_k=5)
        
        assert len(results) > 0
        assert "咖啡" in results[0].content
    
    def test_remove_and_search(self, keyword_search):
        """测试移除后搜索"""
        keyword_search.add_document("doc1", "咖啡很好喝")
        keyword_search.remove_document("doc1")
        
        results = keyword_search.search("咖啡", top_k=5)
        
        assert len(results) == 0


class TestM2RetrievalAPIIntegration:
    """M2检索API集成测试"""
    
    @pytest.fixture
    def api(self):
        """提供RetrievalAPI实例（轻量级）"""
        embedding_service = EmbeddingService()
        vector_search = VectorSearch(embedding_service)
        return RetrievalAPI(embedding_service, vector_search)
    
    def test_api_structure(self, api):
        """测试API结构"""
        assert hasattr(api, 'vector_search')
        assert hasattr(api, 'search')
        assert hasattr(api, 'add_memory')
        assert hasattr(api, 'remove_memory')
        assert hasattr(api, 'get_stats')
    
    def test_vector_search_interface(self, api):
        """测试向量搜索接口（不实际加载模型）"""
        # 只测试接口存在，不实际调用搜索（避免加载模型）
        assert hasattr(api, 'vector_search')
        assert callable(api.vector_search)
    
    def test_search_request_response(self):
        """测试搜索请求和响应"""
        request = SearchRequest(
            query="测试",
            mode=SearchMode.VECTOR,
            top_k=5,
            min_score=0.5
        )
        
        assert request.query == "测试"
        assert request.mode == SearchMode.VECTOR


class TestM2EndToEnd:
    """M2端到端测试"""
    
    def test_keyword_only_workflow(self):
        """测试纯关键词检索流程"""
        keyword_search = KeywordSearch(use_tfidf=True)
        
        documents = [
            ("doc1", "Python是一种编程语言"),
            ("doc2", "Java也是一种编程语言"),
            ("doc3", "咖啡很好喝"),
        ]
        
        for doc_id, content in documents:
            keyword_search.add_document(doc_id, content)
        
        results = keyword_search.search("编程", top_k=5)
        
        assert len(results) >= 2
        
        stats = keyword_search.get_stats()
        assert stats['total_documents'] == 3
    
    def test_similarity_workflow(self):
        """测试相似度计算流程"""
        service = SimilarityService()
        
        # 测试向量相似度
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        vec3 = [1.0, 0.0, 0.0]
        
        result1 = service.compute(vec1, vec2, SimilarityMetric.COSINE)
        result2 = service.compute(vec1, vec3, SimilarityMetric.COSINE)
        
        assert result1.score == pytest.approx(0.0, abs=1e-6)  # 正交
        assert result2.score == pytest.approx(1.0, abs=1e-6)  # 相同


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
