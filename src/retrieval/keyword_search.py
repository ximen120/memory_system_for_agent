"""
关键词检索引擎

基于TF-IDF和简单关键词匹配实现文本检索。
"""

import re
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from collections import Counter
import math

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class KeywordSearchResult:
    """关键词搜索结果"""
    memory_id: str
    content: str
    score: float  # 匹配分数
    matched_keywords: List[str]  # 匹配的关键词
    memory_type: str
    created_at: str
    metadata: Dict[str, Any]


class KeywordSearch:
    """
    关键词检索引擎
    
    基于TF-IDF和关键词匹配实现文本检索。
    
    使用示例：
        >>> from retrieval import KeywordSearch
        >>> 
        >>> search = KeywordSearch()
        >>> search.add_document("doc1", "我喜欢喝咖啡")
        >>> results = search.search("咖啡")
    """
    
    def __init__(self, use_tfidf: bool = True):
        """
        初始化关键词检索引擎
        
        Args:
            use_tfidf: 是否使用TF-IDF加权
        """
        self.use_tfidf = use_tfidf
        self._documents: Dict[str, Dict[str, Any]] = {}
        self._inverted_index: Dict[str, List[str]] = {}  # 倒排索引
        self._doc_freq: Dict[str, int] = {}  # 文档频率
        self._total_docs = 0
        
        logger.info(f"关键词检索引擎初始化: use_tfidf={use_tfidf}")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        分词（简单实现）
        
        Args:
            text: 输入文本
            
        Returns:
            分词结果
        """
        # 简单的中文和英文分词
        # 中文：按字切分（简化版）
        # 英文：按空格和标点切分
        
        # 统一转小写
        text = text.lower()
        
        # 提取英文单词
        english_words = re.findall(r'[a-z]+', text)
        
        # 提取中文字符（长度>=2的词）
        chinese_chars = list(text)
        chinese_words = []
        for i in range(len(chinese_chars) - 1):
            word = chinese_chars[i] + chinese_chars[i + 1]
            if all('\u4e00' <= c <= '\u9fff' for c in word):
                chinese_words.append(word)
        
        return english_words + chinese_words
    
    def _calculate_tf(self, term: str, tokens: List[str]) -> float:
        """计算词频(TF)"""
        if not tokens:
            return 0.0
        return tokens.count(term) / len(tokens)
    
    def _calculate_idf(self, term: str) -> float:
        """计算逆文档频率(IDF)"""
        if term not in self._doc_freq or self._total_docs == 0:
            return 0.0
        
        # IDF = log(N / df)
        df = self._doc_freq[term]
        return math.log(self._total_docs / (df + 1)) + 1
    
    def add_document(
        self,
        memory_id: str,
        content: str,
        memory_type: str = "fact",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加文档到索引
        
        Args:
            memory_id: 记忆ID
            content: 文档内容
            memory_type: 记忆类型
            metadata: 元数据
            
        Returns:
            是否成功
        """
        try:
            # 分词
            tokens = self._tokenize(content)
            
            # 存储文档
            self._documents[memory_id] = {
                'content': content,
                'tokens': tokens,
                'memory_type': memory_type,
                'metadata': metadata or {},
                'token_set': set(tokens)
            }
            
            # 更新倒排索引
            for token in set(tokens):
                if token not in self._inverted_index:
                    self._inverted_index[token] = []
                self._inverted_index[token].append(memory_id)
                
                # 更新文档频率
                self._doc_freq[token] = self._doc_freq.get(token, 0) + 1
            
            self._total_docs += 1
            
            return True
        except Exception as e:
            logger.error(f"添加文档失败: {e}")
            return False
    
    def remove_document(self, memory_id: str) -> bool:
        """
        从索引中移除文档
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否成功
        """
        if memory_id not in self._documents:
            return False
        
        try:
            doc = self._documents[memory_id]
            
            # 更新倒排索引
            for token in doc['token_set']:
                if token in self._inverted_index:
                    self._inverted_index[token].remove(memory_id)
                    if not self._inverted_index[token]:
                        del self._inverted_index[token]
                
                # 更新文档频率
                if token in self._doc_freq:
                    self._doc_freq[token] -= 1
            
            # 移除文档
            del self._documents[memory_id]
            self._total_docs -= 1
            
            return True
        except Exception as e:
            logger.error(f"移除文档失败: {e}")
            return False
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.1
    ) -> List[KeywordSearchResult]:
        """
        关键词搜索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            min_score: 最小分数
            
        Returns:
            搜索结果列表
        """
        if not query or not self._documents:
            return []
        
        try:
            # 分词
            query_tokens = self._tokenize(query)
            
            if not query_tokens:
                return []
            
            # 查找候选文档
            candidates = set()
            for token in query_tokens:
                if token in self._inverted_index:
                    candidates.update(self._inverted_index[token])
            
            # 计算分数
            results = []
            for memory_id in candidates:
                doc = self._documents[memory_id]
                
                # 计算匹配分数
                score = 0.0
                matched_keywords = []
                
                for token in query_tokens:
                    if token in doc['token_set']:
                        matched_keywords.append(token)
                        
                        if self.use_tfidf:
                            # TF-IDF加权
                            tf = self._calculate_tf(token, doc['tokens'])
                            idf = self._calculate_idf(token)
                            score += tf * idf
                        else:
                            # 简单计数
                            score += 1.0
                
                # 归一化
                if self.use_tfidf:
                    # 除以查询词数归一化
                    score /= len(query_tokens)
                else:
                    score /= len(query_tokens)
                
                if score >= min_score:
                    results.append(KeywordSearchResult(
                        memory_id=memory_id,
                        content=doc['content'],
                        score=score,
                        matched_keywords=matched_keywords,
                        memory_type=doc['memory_type'],
                        created_at=doc['metadata'].get('created_at', ''),
                        metadata=doc['metadata']
                    ))
            
            # 排序并截断
            results.sort(key=lambda x: x.score, reverse=True)
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"关键词搜索失败: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'total_documents': self._total_docs,
            'total_terms': len(self._inverted_index),
            'use_tfidf': self.use_tfidf
        }


# 便捷函数
def simple_keyword_search(
    documents: List[Tuple[str, str]],
    query: str,
    top_k: int = 10
) -> List[KeywordSearchResult]:
    """
    简单关键词搜索（无需预先创建索引）
    
    Args:
        documents: (memory_id, content)列表
        query: 查询文本
        top_k: 返回数量
        
    Returns:
        搜索结果
    """
    search = KeywordSearch(use_tfidf=False)
    
    for memory_id, content in documents:
        search.add_document(memory_id, content)
    
    return search.search(query, top_k=top_k)


if __name__ == "__main__":
    # 测试代码
    print("=" * 50)
    print("关键词检索引擎测试")
    print("=" * 50)
    
    # 创建搜索引擎
    search = KeywordSearch(use_tfidf=True)
    
    # 添加文档
    documents = [
        ("doc1", "我喜欢喝咖啡，咖啡是我的最爱"),
        ("doc2", "今天天气很好，适合喝茶"),
        ("doc3", "咖啡和茶都是好饮品"),
        ("doc4", "我喜欢编程，Python是我的最爱"),
    ]
    
    for memory_id, content in documents:
        search.add_document(memory_id, content)
    
    print(f"\n索引统计: {search.get_stats()}")
    
    # 搜索
    print("\n搜索'咖啡':")
    results = search.search("咖啡", top_k=3)
    for result in results:
        print(f"  {result.memory_id}: {result.content[:20]}... (score: {result.score:.3f})")
        print(f"    匹配词: {result.matched_keywords}")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)
