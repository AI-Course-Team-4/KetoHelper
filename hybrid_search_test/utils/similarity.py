"""
유사도 계산 유틸리티
"""
import numpy as np
from typing import List, Dict, Any, Tuple
from ..config.settings import config

class SimilarityCalculator:
    """유사도 계산기"""
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """코사인 유사도 계산"""
        try:
            # numpy 배열로 변환
            a = np.array(vec1, dtype=np.float32)
            b = np.array(vec2, dtype=np.float32)
            
            # 정규화
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            # 코사인 유사도 계산
            similarity = np.dot(a, b) / (norm_a * norm_b)
            
            # 0~1 범위로 클램핑
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            print(f"코사인 유사도 계산 실패: {e}")
            return 0.0
    
    @staticmethod
    def normalize_score(similarity: float) -> float:
        """유사도 점수를 0-100% 범위로 정규화"""
        return config.normalize_score(similarity)
    
    @staticmethod
    def calculate_hybrid_score(
        vector_score: float, 
        keyword_score: float,
        vector_weight: float = None,
        keyword_weight: float = None
    ) -> float:
        """하이브리드 점수 계산 (가중 평균)"""
        if vector_weight is None:
            vector_weight = config.VECTOR_WEIGHT
        if keyword_weight is None:
            keyword_weight = config.KEYWORD_WEIGHT
        
        # 가중치 정규화
        total_weight = vector_weight + keyword_weight
        if total_weight > 0:
            vector_weight = vector_weight / total_weight
            keyword_weight = keyword_weight / total_weight
        
        # 가중 평균 계산
        hybrid_score = (vector_score * vector_weight) + (keyword_score * keyword_weight)
        
        return hybrid_score
    
    @staticmethod
    def rank_results(results: List[Dict[str, Any]], score_key: str = 'similarity') -> List[Dict[str, Any]]:
        """결과를 점수 순으로 정렬"""
        return sorted(results, key=lambda x: x.get(score_key, 0), reverse=True)
    
    @staticmethod
    def add_rank_to_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """결과에 순위 추가"""
        for i, result in enumerate(results):
            result['rank'] = i + 1
        return results

# 전역 유사도 계산기 인스턴스
similarity_calculator = SimilarityCalculator()
