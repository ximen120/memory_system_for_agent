"""
相似度计算服务

提供多种向量相似度计算方法，支持批量计算和性能优化。
"""

import math
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# 配置日志
logger = logging.getLogger(__name__)


class SimilarityMetric(Enum):
    """相似度度量类型"""
    COSINE = "cosine"           # 余弦相似度
    EUCLIDEAN = "euclidean"    # 欧几里得距离
    DOT_PRODUCT = "dot_product" # 点积
    MANHATTAN = "manhattan"    # 曼哈顿距离


@dataclass
class SimilarityResult:
    """相似度计算结果"""
    score: float           # 相似度分数
    metric: SimilarityMetric  # 使用的度量
    normalized_score: float  # 归一化分数 (0-1)


class SimilarityService:
    """
    相似度计算服务
    
    提供多种相似度计算方法，支持批量计算和缓存优化。
    
    使用示例：
        >>> from retrieval import SimilarityService
        >>> service = SimilarityService()
        >>> 
        >>> vec1 = [1.0, 0.0, 0.0]
        >>> vec2 = [0.0, 1.0, 0.0]
        >>> 
        >>> result = service.compute(vec1, vec2, metric=SimilarityMetric.COSINE)
        >>> print(f"相似度: {result.score:.3f}")
    """
    
    def __init__(self, default_metric: SimilarityMetric = SimilarityMetric.COSINE):
        """
        初始化相似度服务
        
        Args:
            default_metric: 默认相似度度量
        """
        self.default_metric = default_metric
        logger.info(f"相似度服务初始化: default_metric={default_metric.value}")
    
    def compute(
        self,
        vec1: List[float],
        vec2: List[float],
        metric: Optional[SimilarityMetric] = None
    ) -> SimilarityResult:
        """
        计算两个向量的相似度
        
        Args:
            vec1: 第一个向量
            vec2: 第二个向量
            metric: 相似度度量类型，默认使用COSINE
            
        Returns:
            SimilarityResult: 相似度结果
        """
        metric = metric or self.default_metric
        
        try:
            if metric == SimilarityMetric.COSINE:
                score = cosine_similarity(vec1, vec2)
                normalized = (score + 1) / 2  # 映射到 [0, 1]
            elif metric == SimilarityMetric.EUCLIDEAN:
                score = euclidean_distance(vec1, vec2)
                normalized = 1 / (1 + score)  # 距离越小越相似
            elif metric == SimilarityMetric.DOT_PRODUCT:
                score = dot_product(vec1, vec2)
                normalized = normalize_dot_product(vec1, vec2, score)
            elif metric == SimilarityMetric.MANHATTAN:
                score = manhattan_distance(vec1, vec2)
                normalized = 1 / (1 + score)
            else:
                raise ValueError(f"未知的相似度度量: {metric}")
            
            return SimilarityResult(
                score=score,
                metric=metric,
                normalized_score=normalized
            )
            
        except Exception as e:
            logger.error(f"相似度计算失败: {e}")
            raise
    
    def compute_batch(
        self,
        query_vec: List[float],
        candidate_vecs: List[List[float]],
        metric: Optional[SimilarityMetric] = None,
        top_k: Optional[int] = None
    ) -> List[Tuple[int, SimilarityResult]]:
        """
        批量计算相似度
        
        Args:
            query_vec: 查询向量
            candidate_vecs: 候选向量列表
            metric: 相似度度量类型
            top_k: 返回前k个结果，None返回全部
            
        Returns:
            List[Tuple[int, SimilarityResult]]: (索引, 结果)列表
        """
        metric = metric or self.default_metric
        
        results = []
        for i, candidate in enumerate(candidate_vecs):
            try:
                result = self.compute(query_vec, candidate, metric)
                results.append((i, result))
            except Exception as e:
                logger.warning(f"计算第{i}个候选向量相似度失败: {e}")
                continue
        
        # 按归一化分数排序
        results.sort(key=lambda x: x[1].normalized_score, reverse=True)
        
        # 截断
        if top_k:
            results = results[:top_k]
        
        return results
    
    def compute_matrix(
        self,
        vectors: List[List[float]],
        metric: Optional[SimilarityMetric] = None
    ) -> List[List[float]]:
        """
        计算相似度矩阵
        
        Args:
            vectors: 向量列表
            metric: 相似度度量类型
            
        Returns:
            List[List[float]]: 相似度矩阵
        """
        metric = metric or self.default_metric
        n = len(vectors)
        
        matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i, n):
                if i == j:
                    matrix[i][j] = 1.0 if metric == SimilarityMetric.COSINE else 0.0
                else:
                    try:
                        result = self.compute(vectors[i], vectors[j], metric)
                        matrix[i][j] = result.normalized_score
                        matrix[j][i] = result.normalized_score
                    except Exception as e:
                        logger.warning(f"计算({i},{j})相似度失败: {e}")
                        matrix[i][j] = 0.0
                        matrix[j][i] = 0.0
        
        return matrix


# 基础相似度函数
def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    计算两个向量的余弦相似度
    
    余弦相似度 = (A·B) / (||A|| * ||B||)
    结果范围: [-1, 1]，其中 1 表示完全相同，-1 表示完全相反
    
    Args:
        vec1: 第一个向量
        vec2: 第二个向量
        
    Returns:
        float: 余弦相似度，范围 [-1, 1]
        
    Raises:
        ValueError: 向量维度不匹配或为零向量时抛出
    """
    # 验证输入
    if len(vec1) != len(vec2):
        raise ValueError(f"向量维度不匹配: {len(vec1)} vs {len(vec2)}")
    
    if len(vec1) == 0:
        raise ValueError("向量不能为空")
    
    # 计算点积
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    
    # 计算模长
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    # 检查零向量
    if norm1 == 0 or norm2 == 0:
        raise ValueError("不能计算零向量的相似度")
    
    # 计算余弦相似度
    similarity = dot_product / (norm1 * norm2)
    
    # 处理浮点误差，确保结果在 [-1, 1] 范围内
    similarity = max(-1.0, min(1.0, similarity))
    
    return similarity


def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """
    计算两个向量的欧几里得距离
    
    Args:
        vec1: 第一个向量
        vec2: 第二个向量
        
    Returns:
        float: 欧几里得距离
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"向量维度不匹配: {len(vec1)} vs {len(vec2)}")
    
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(vec1, vec2)))


def manhattan_distance(vec1: List[float], vec2: List[float]) -> float:
    """
    计算两个向量的曼哈顿距离
    
    Args:
        vec1: 第一个向量
        vec2: 第二个向量
        
    Returns:
        float: 曼哈顿距离
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"向量维度不匹配: {len(vec1)} vs {len(vec2)}")
    
    return sum(abs(a - b) for a, b in zip(vec1, vec2))


def dot_product(vec1: List[float], vec2: List[float]) -> float:
    """
    计算两个向量的点积
    
    Args:
        vec1: 第一个向量
        vec2: 第二个向量
        
    Returns:
        float: 点积结果
    """
    if len(vec1) != len(vec2):
        raise ValueError(f"向量维度不匹配: {len(vec1)} vs {len(vec2)}")
    
    return sum(a * b for a, b in zip(vec1, vec2))


def normalize_dot_product(vec1: List[float], vec2: List[float], dot: float) -> float:
    """
    将点积归一化到 [0, 1] 范围
    
    Args:
        vec1: 第一个向量
        vec2: 第二个向量
        dot: 点积值
        
    Returns:
        float: 归一化分数
    """
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # 归一化到 [-1, 1] 然后映射到 [0, 1]
    normalized = dot / (norm1 * norm2)
    return (normalized + 1) / 2


# 便捷函数
def quick_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    快速计算余弦相似度（便捷函数）
    
    Args:
        vec1: 第一个向量
        vec2: 第二个向量
        
    Returns:
        float: 余弦相似度
    """
    return cosine_similarity(vec1, vec2)


def rank_by_similarity(
    query_vec: List[float],
    candidate_vecs: List[List[float]],
    top_k: int = 10
) -> List[Tuple[int, float]]:
    """
    按相似度排序候选向量
    
    Args:
        query_vec: 查询向量
        candidate_vecs: 候选向量列表
        top_k: 返回前k个
        
    Returns:
        List[Tuple[int, float]]: (索引, 相似度)列表
    """
    service = SimilarityService()
    results = service.compute_batch(query_vec, candidate_vecs, top_k=top_k)
    
    return [(idx, result.normalized_score) for idx, result in results]


if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("相似度计算服务测试")
    print("=" * 50)
    
    # 创建服务
    service = SimilarityService()
    
    # 测试向量
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [0.0, 1.0, 0.0]
    vec3 = [1.0, 0.0, 0.0]
    
    print("\n1. 余弦相似度测试:")
    result = service.compute(vec1, vec2, SimilarityMetric.COSINE)
    print(f"   {vec1} vs {vec2}: {result.score:.3f} (归一化: {result.normalized_score:.3f})")
    
    result = service.compute(vec1, vec3, SimilarityMetric.COSINE)
    print(f"   {vec1} vs {vec3}: {result.score:.3f} (归一化: {result.normalized_score:.3f})")
    
    print("\n2. 欧几里得距离测试:")
    result = service.compute(vec1, vec2, SimilarityMetric.EUCLIDEAN)
    print(f"   {vec1} vs {vec2}: {result.score:.3f} (归一化: {result.normalized_score:.3f})")
    
    print("\n3. 批量计算测试:")
    candidates = [vec2, vec3, [0.5, 0.5, 0.0]]
    results = service.compute_batch(vec1, candidates, top_k=2)
    for idx, res in results:
        print(f"   候选{idx}: 归一化分数={res.normalized_score:.3f}")
    
    print("\n4. 相似度矩阵测试:")
    vectors = [vec1, vec2, vec3]
    matrix = service.compute_matrix(vectors)
    for row in matrix:
        print(f"   {[f'{x:.2f}' for x in row]}")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
