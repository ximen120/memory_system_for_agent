"""
相似度计算服务单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "retrieval"))

import pytest
from similarity import (
    SimilarityService,
    SimilarityMetric,
    SimilarityResult,
    cosine_similarity,
    euclidean_distance,
    manhattan_distance,
    dot_product,
    quick_similarity,
    rank_by_similarity
)


class TestCosineSimilarity:
    """测试余弦相似度"""
    
    def test_identical_vectors(self):
        """测试相同向量相似度为1"""
        vec = [1.0, 0.0, 0.0]
        result = cosine_similarity(vec, vec)
        assert result == pytest.approx(1.0, abs=1e-6)
    
    def test_orthogonal_vectors(self):
        """测试正交向量相似度为0"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        result = cosine_similarity(vec1, vec2)
        assert result == pytest.approx(0.0, abs=1e-6)
    
    def test_opposite_vectors(self):
        """测试相反向量相似度为-1"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [-1.0, 0.0, 0.0]
        result = cosine_similarity(vec1, vec2)
        assert result == pytest.approx(-1.0, abs=1e-6)
    
    def test_dimension_mismatch_raises_error(self):
        """测试维度不匹配抛出错误"""
        vec1 = [1.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        
        with pytest.raises(ValueError):
            cosine_similarity(vec1, vec2)
    
    def test_empty_vector_raises_error(self):
        """测试空向量抛出错误"""
        with pytest.raises(ValueError):
            cosine_similarity([], [])


class TestEuclideanDistance:
    """测试欧几里得距离"""
    
    def test_identical_vectors(self):
        """测试相同向量距离为0"""
        vec = [1.0, 2.0, 3.0]
        result = euclidean_distance(vec, vec)
        assert result == pytest.approx(0.0, abs=1e-6)
    
    def test_simple_distance(self):
        """测试简单距离计算"""
        vec1 = [0.0, 0.0]
        vec2 = [3.0, 4.0]
        result = euclidean_distance(vec1, vec2)
        assert result == pytest.approx(5.0, abs=1e-6)


class TestManhattanDistance:
    """测试曼哈顿距离"""
    
    def test_identical_vectors(self):
        """测试相同向量距离为0"""
        vec = [1.0, 2.0, 3.0]
        result = manhattan_distance(vec, vec)
        assert result == pytest.approx(0.0, abs=1e-6)
    
    def test_simple_distance(self):
        """测试简单距离计算"""
        vec1 = [0.0, 0.0]
        vec2 = [3.0, 4.0]
        result = manhattan_distance(vec1, vec2)
        assert result == pytest.approx(7.0, abs=1e-6)


class TestDotProduct:
    """测试点积"""
    
    def test_orthogonal_vectors(self):
        """测试正交向量点积为0"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        result = dot_product(vec1, vec2)
        assert result == pytest.approx(0.0, abs=1e-6)
    
    def test_simple_dot_product(self):
        """测试简单点积计算"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [4.0, 5.0, 6.0]
        result = dot_product(vec1, vec2)
        expected = 1*4 + 2*5 + 3*6  # 32
        assert result == pytest.approx(expected, abs=1e-6)


class TestSimilarityService:
    """测试相似度服务"""
    
    @pytest.fixture
    def service(self):
        """提供相似度服务实例"""
        return SimilarityService()
    
    def test_compute_cosine(self, service):
        """测试计算余弦相似度"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        
        result = service.compute(vec1, vec2, SimilarityMetric.COSINE)
        
        assert isinstance(result, SimilarityResult)
        assert result.metric == SimilarityMetric.COSINE
        assert result.score == pytest.approx(0.0, abs=1e-6)
        assert result.normalized_score == pytest.approx(0.5, abs=1e-6)
    
    def test_compute_euclidean(self, service):
        """测试计算欧几里得距离"""
        vec1 = [0.0, 0.0]
        vec2 = [3.0, 4.0]
        
        result = service.compute(vec1, vec2, SimilarityMetric.EUCLIDEAN)
        
        assert result.metric == SimilarityMetric.EUCLIDEAN
        assert result.score == pytest.approx(5.0, abs=1e-6)
        assert result.normalized_score == pytest.approx(1/6, abs=1e-6)
    
    def test_compute_uses_default_metric(self, service):
        """测试使用默认度量"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        
        result = service.compute(vec1, vec2)  # 不指定metric
        
        assert result.metric == SimilarityMetric.COSINE  # 默认是COSINE
        assert result.score == pytest.approx(1.0, abs=1e-6)
    
    def test_compute_batch(self, service):
        """测试批量计算"""
        query = [1.0, 0.0, 0.0]
        candidates = [
            [0.0, 1.0, 0.0],  # 正交
            [1.0, 0.0, 0.0],  # 相同
            [0.0, 0.0, 1.0],  # 正交
        ]
        
        results = service.compute_batch(query, candidates, top_k=2)
        
        assert len(results) == 2
        # 第一个应该是相同向量（索引1）
        assert results[0][0] == 1
        assert results[0][1].normalized_score == pytest.approx(1.0, abs=1e-6)
    
    def test_compute_matrix(self, service):
        """测试相似度矩阵"""
        vectors = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],
        ]
        
        matrix = service.compute_matrix(vectors)
        
        assert len(matrix) == 3
        assert len(matrix[0]) == 3
        # 对角线应该是1
        assert matrix[0][0] == pytest.approx(1.0, abs=1e-6)
        # 相同向量应该是1
        assert matrix[0][2] == pytest.approx(1.0, abs=1e-6)


class TestQuickSimilarity:
    """测试快速相似度函数"""
    
    def test_quick_similarity(self):
        """测试快速相似度计算"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        
        result = quick_similarity(vec1, vec2)
        
        assert result == pytest.approx(0.0, abs=1e-6)


class TestRankBySimilarity:
    """测试相似度排序"""
    
    def test_rank_by_similarity(self):
        """测试按相似度排序"""
        query = [1.0, 0.0, 0.0]
        candidates = [
            [0.0, 1.0, 0.0],  # 正交，相似度0
            [1.0, 0.0, 0.0],  # 相同，相似度1
            [-1.0, 0.0, 0.0], # 相反，相似度-1
        ]
        
        results = rank_by_similarity(query, candidates, top_k=2)
        
        assert len(results) == 2
        # 第一个应该是相同向量
        assert results[0][0] == 1
        assert results[0][1] == pytest.approx(1.0, abs=1e-6)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
