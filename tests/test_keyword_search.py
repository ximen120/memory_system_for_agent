"""
关键词检索引擎单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "retrieval"))

import pytest
from keyword_search import KeywordSearch, KeywordSearchResult


class TestKeywordSearchCreation:
    """测试关键词检索引擎创建"""
    
    def test_create_default(self):
        """测试默认创建"""
        search = KeywordSearch()
        
        assert search.use_tfidf is True
        assert search._total_docs == 0
    
    def test_create_without_tfidf(self):
        """测试不使用TF-IDF创建"""
        search = KeywordSearch(use_tfidf=False)
        
        assert search.use_tfidf is False


class TestKeywordSearchTokenization:
    """测试分词功能"""
    
    @pytest.fixture
    def search(self):
        """提供搜索引擎实例"""
        return KeywordSearch()
    
    def test_tokenize_english(self, search):
        """测试英文分词"""
        tokens = search._tokenize("hello world python")
        
        assert "hello" in tokens
        assert "world" in tokens
        assert "python" in tokens
    
    def test_tokenize_chinese(self, search):
        """测试中文分词"""
        tokens = search._tokenize("我喜欢咖啡")
        
        # 应该提取双字词
        assert "喜欢" in tokens
        assert "欢咖" in tokens or "咖啡" in tokens
    
    def test_tokenize_mixed(self, search):
        """测试中英文混合"""
        tokens = search._tokenize("我喜欢Python编程")
        
        assert "python" in tokens
        assert "喜欢" in tokens


class TestKeywordSearchDocumentManagement:
    """测试文档管理"""
    
    @pytest.fixture
    def search(self):
        """提供搜索引擎实例"""
        return KeywordSearch()
    
    def test_add_document(self, search):
        """测试添加文档"""
        result = search.add_document("doc1", "我喜欢喝咖啡")
        
        assert result is True
        assert search._total_docs == 1
        assert "doc1" in search._documents
    
    def test_add_multiple_documents(self, search):
        """测试添加多个文档"""
        search.add_document("doc1", "咖啡很好喝")
        search.add_document("doc2", "茶也很好喝")
        
        assert search._total_docs == 2
    
    def test_remove_document(self, search):
        """测试移除文档"""
        search.add_document("doc1", "咖啡很好喝")
        
        result = search.remove_document("doc1")
        
        assert result is True
        assert search._total_docs == 0
        assert "doc1" not in search._documents
    
    def test_remove_nonexistent_document(self, search):
        """测试移除不存在的文档"""
        result = search.remove_document("nonexistent")
        
        assert result is False


class TestKeywordSearchSearch:
    """测试搜索功能"""
    
    @pytest.fixture
    def search_with_docs(self):
        """提供带文档的搜索引擎"""
        search = KeywordSearch(use_tfidf=False)
        search.add_document("doc1", "我喜欢喝咖啡，咖啡是我的最爱")
        search.add_document("doc2", "今天天气很好，适合喝茶")
        search.add_document("doc3", "咖啡和茶都是好饮品")
        return search
    
    def test_search_returns_results(self, search_with_docs):
        """测试搜索返回结果"""
        results = search_with_docs.search("咖啡")
        
        assert isinstance(results, list)
        assert len(results) > 0
    
    def test_search_result_structure(self, search_with_docs):
        """测试搜索结果结构"""
        results = search_with_docs.search("咖啡")
        
        if results:
            result = results[0]
            assert isinstance(result, KeywordSearchResult)
            assert hasattr(result, 'memory_id')
            assert hasattr(result, 'content')
            assert hasattr(result, 'score')
            assert hasattr(result, 'matched_keywords')
    
    def test_search_empty_query(self, search_with_docs):
        """测试空查询"""
        results = search_with_docs.search("")
        
        assert results == []
    
    def test_search_no_match(self, search_with_docs):
        """测试无匹配结果"""
        results = search_with_docs.search("不存在的词")
        
        assert results == []
    
    def test_search_with_top_k(self, search_with_docs):
        """测试限制返回数量"""
        results = search_with_docs.search("咖啡", top_k=1)
        
        assert len(results) <= 1


class TestKeywordSearchStats:
    """测试统计信息"""
    
    def test_get_stats_empty(self):
        """测试空索引统计"""
        search = KeywordSearch()
        
        stats = search.get_stats()
        
        assert stats['total_documents'] == 0
        assert stats['total_terms'] == 0
        assert stats['use_tfidf'] is True
    
    def test_get_stats_with_docs(self):
        """测试有文档的统计"""
        search = KeywordSearch()
        search.add_document("doc1", "咖啡茶咖啡")
        
        stats = search.get_stats()
        
        assert stats['total_documents'] == 1
        assert stats['total_terms'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
