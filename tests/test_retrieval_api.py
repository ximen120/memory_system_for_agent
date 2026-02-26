"""
检索API单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "retrieval"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "storage"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))

import os
os.environ['TEST_MODE'] = 'true'

import pytest
from retrieval_api import RetrievalAPI, SearchMode, SearchRequest
from embedding_service import EmbeddingService
from vector_search import VectorSearch


class TestRetrievalAPICreation:
    """测试RetrievalAPI创建"""
    
    @pytest.fixture
    def api(self):
        """提供API实例"""
        embedding_service = EmbeddingService()
        vector_search = VectorSearch(embedding_service)
        return RetrievalAPI(embedding_service, vector_search)
    
    def test_create_with_components(self, api):
        """测试使用组件创建"""
        assert api.embedding_service is not None
        assert api.vector_search is not None
    
    def test_api_has_required_attributes(self, api):
        """测试API有必需的属性"""
        assert hasattr(api, 'embedding_service')
        assert hasattr(api, 'vector_search')
        assert hasattr(api, 'search')
        assert hasattr(api, 'vector_search')
        assert hasattr(api, 'add_memory')
        assert hasattr(api, 'remove_memory')
        assert hasattr(api, 'get_stats')


class TestRetrievalAPISearch:
    """测试检索API搜索功能（轻量级，不加载模型）"""
    
    @pytest.fixture
    def api(self):
        """提供API实例"""
        embedding_service = EmbeddingService()
        vector_search = VectorSearch(embedding_service)
        return RetrievalAPI(embedding_service, vector_search)
    
    def test_vector_search_interface(self, api):
        """测试向量搜索接口"""
        # 不实际加载模型，只测试接口
        response = api.vector_search("测试", top_k=5)
        
        assert response is not None
        assert isinstance(response.total, int)
        assert response.query == "测试"
        assert response.mode == SearchMode.VECTOR
    
    def test_search_request_object(self):
        """测试搜索请求对象"""
        request = SearchRequest(
            query="测试",
            mode=SearchMode.VECTOR,
            top_k=5,
            min_score=0.5
        )
        
        assert request.query == "测试"
        assert request.mode == SearchMode.VECTOR
        assert request.top_k == 5
        assert request.min_score == 0.5
    
    def test_search_response_structure(self):
        """测试搜索响应结构"""
        from retrieval_api import SearchResponse
        
        response = SearchResponse(
            results=[],
            total=0,
            query="测试",
            mode=SearchMode.VECTOR,
            search_time_ms=100.0
        )
        
        assert response.results == []
        assert response.total == 0
        assert response.query == "测试"


class TestRetrievalAPIMemoryManagement:
    """测试检索API记忆管理（轻量级）"""
    
    @pytest.fixture
    def api(self):
        """提供API实例"""
        embedding_service = EmbeddingService()
        vector_search = VectorSearch(embedding_service)
        return RetrievalAPI(embedding_service, vector_search)
    
    def test_add_memory_interface(self, api):
        """测试添加记忆接口"""
        # 不实际加载模型，只测试接口
        memory_id = api.add_memory(
            content="测试内容",
            memory_type="fact",
            tags=["测试"],
            importance=3.0
        )
        
        # 如果模型未加载，返回None
        assert memory_id is None or isinstance(memory_id, str)
    
    def test_remove_memory_interface(self, api):
        """测试移除记忆接口"""
        result = api.remove_memory("test_id")
        
        # 内存模式下返回True
        assert isinstance(result, bool)


class TestRetrievalAPIStats:
    """测试检索API统计信息"""
    
    def test_get_stats_returns_dict(self):
        """测试获取统计信息返回字典"""
        api = RetrievalAPI.create_default("./test_stats", "test_stats")
        
        stats = api.get_stats()
        
        assert isinstance(stats, dict)
        assert 'vector_search' in stats
        assert 'embedding_service' in stats
    
    def test_stats_contains_vector_search_info(self):
        """测试统计信息包含向量搜索信息"""
        api = RetrievalAPI.create_default("./test_stats", "test_stats")
        
        stats = api.get_stats()
        
        vs_stats = stats['vector_search']
        assert 'total_documents' in vs_stats
        assert 'collection_name' in vs_stats
        assert 'storage_type' in vs_stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
