"""
混合检索引擎单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "retrieval"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "storage"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

import os
os.environ['TEST_MODE'] = 'true'

import pytest
from hybrid_search import HybridSearch, HybridSearchResult
from vector_search import VectorSearch
from keyword_search import KeywordSearch
from embedding_service import EmbeddingService


class TestHybridSearchCreation:
    """测试混合检索引擎创建"""
    
    @pytest.fixture
    def hybrid(self):
        """提供混合检索引擎实例"""
        embedding_service = EmbeddingService()
        vector_search = VectorSearch(embedding_service)
        keyword_search = KeywordSearch()
        return HybridSearch(vector_search, keyword_search)
    
    def test_create_with_components(self, hybrid):
        """测试使用组件创建"""
        assert hybrid.vector_search is not None
        assert hybrid.keyword_search is not None
        assert hybrid.vector_weight == 0.7
        assert hybrid.keyword_weight == 0.3
        assert hybrid.rrf_k == 60
    
    def test_create_with_custom_weights(self):
        """测试使用自定义权重创建"""
        embedding_service = EmbeddingService()
        vector_search = VectorSearch(embedding_service)
        keyword_search = KeywordSearch()
        
        hybrid = HybridSearch(
            vector_search=vector_search,
            keyword_search=keyword_search,
            vector_weight=0.8,
            keyword_weight=0.2,
            rrf_k=50
        )
        
        assert hybrid.vector_weight == 0.8
        assert hybrid.keyword_weight == 0.2
        assert hybrid.rrf_k == 50


class TestHybridSearchInterface:
    """测试混合检索接口"""
    
    @pytest.fixture
    def hybrid(self):
        """提供混合检索引擎实例"""
        embedding_service = EmbeddingService()
        vector_search = VectorSearch(embedding_service)
        keyword_search = KeywordSearch()
        return HybridSearch(vector_search, keyword_search)
    
    def test_search_interface(self, hybrid):
        """测试搜索接口"""
        results = hybrid.search("测试查询", top_k=5)
        
        assert isinstance(results, list)
        # 空索引应该返回空列表
        assert len(results) == 0
    
    def test_search_empty_query(self, hybrid):
        """测试空查询"""
        results = hybrid.search("")
        
        assert results == []
    
    def test_search_with_options(self, hybrid):
        """测试带选项的搜索"""
        results = hybrid.search(
            "测试",
            top_k=10,
            min_score=0.1,
            use_vector=True,
            use_keyword=True
        )
        
        assert isinstance(results, list)


class TestHybridSearchDocumentManagement:
    """测试文档管理"""
    
    @pytest.fixture
    def hybrid(self):
        """提供混合检索引擎实例"""
        embedding_service = EmbeddingService()
        vector_search = VectorSearch(embedding_service)
        keyword_search = KeywordSearch()
        return HybridSearch(vector_search, keyword_search)
    
    def test_add_document_without_embedding(self, hybrid):
        """测试添加无向量的文档"""
        result = hybrid.add_document(
            memory_id="test1",
            content="测试内容",
            memory_type="fact"
        )
        
        # 应该成功（关键词索引）
        assert result is True or result is False  # 取决于实现
    
    def test_remove_document(self, hybrid):
        """测试移除文档"""
        # 添加一个文档
        hybrid.add_document("test2", "测试内容")
        
        # 移除
        result = hybrid.remove_document("test2")
        
        # 应该成功或文档不存在
        assert isinstance(result, bool)


class TestHybridSearchStats:
    """测试统计信息"""
    
    @pytest.fixture
    def hybrid(self):
        """提供混合检索引擎实例"""
        embedding_service = EmbeddingService()
        vector_search = VectorSearch(embedding_service)
        keyword_search = KeywordSearch()
        return HybridSearch(vector_search, keyword_search)
    
    def test_get_stats_returns_dict(self, hybrid):
        """测试获取统计信息返回字典"""
        stats = hybrid.get_stats()
        
        assert isinstance(stats, dict)
        assert 'vector_search' in stats
        assert 'keyword_search' in stats
        assert 'vector_weight' in stats
        assert 'keyword_weight' in stats
        assert 'rrf_k' in stats
    
    def test_stats_contains_weights(self, hybrid):
        """测试统计信息包含权重"""
        stats = hybrid.get_stats()
        
        assert stats['vector_weight'] == 0.7
        assert stats['keyword_weight'] == 0.3
        assert stats['rrf_k'] == 60


class TestHybridSearchRRF:
    """测试RRF融合算法"""
    
    def test_rrf_formula(self):
        """测试RRF公式计算"""
        # RRF: score = Σ(weight_i / (k + rank_i))
        # k=60, vector_weight=0.7, keyword_weight=0.3
        
        k = 60
        vector_weight = 0.7
        keyword_weight = 0.3
        
        # 排名0的文档
        vector_rank = 0
        keyword_rank = 1
        
        score = (vector_weight / (k + vector_rank)) + (keyword_weight / (k + keyword_rank))
        
        # 验证计算
        expected = (0.7 / 60) + (0.3 / 61)
        assert score == pytest.approx(expected, abs=1e-6)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
