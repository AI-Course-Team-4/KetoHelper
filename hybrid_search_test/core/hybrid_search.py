"""
하이브리드 검색 엔진
키워드 검색과 벡터 검색의 가중 평균
"""
import time
from typing import List, Dict, Any
from .keyword_search import keyword_search_engine
from .vector_search import vector_search_engine
from ..utils.similarity import similarity_calculator
from ..utils.formatter import result_formatter
from ..config.settings import config

class HybridSearchEngine:
    """하이브리드 검색 엔진"""
    
    def __init__(self):
        self.keyword_engine = keyword_search_engine
        self.vector_engine = vector_search_engine
        self.similarity = similarity_calculator
        self.formatter = result_formatter
    
    def search(self, query: str, top_k: int = None, 
               vector_weight: float = None, keyword_weight: float = None) -> List[Dict[str, Any]]:
        """하이브리드 검색 실행"""
        if top_k is None:
            top_k = config.DEFAULT_TOP_K
        
        if vector_weight is None:
            vector_weight = config.VECTOR_WEIGHT
        if keyword_weight is None:
            keyword_weight = config.KEYWORD_WEIGHT
        
        start_time = time.time()
        
        try:
            # 1. 키워드 검색과 벡터 검색 병렬 실행
            keyword_results = self.keyword_engine.search(query, top_k * 2)  # 더 많은 결과 수집
            vector_results = self.vector_engine.search(query, top_k * 2)
            
            # 2. 하이브리드 점수 계산
            hybrid_results = self._calculate_hybrid_scores(
                keyword_results, vector_results, vector_weight, keyword_weight
            )
            
            # 3. 점수 순으로 정렬하고 상위 k개 선택
            ranked_results = self.similarity.rank_results(hybrid_results, 'hybrid_score')
            top_results = ranked_results[:top_k]
            
            # 4. 결과 포맷팅
            formatted_results = self.formatter.format_search_results(top_results, 'hybrid')
            
            # 5. 순위 추가
            final_results = self.similarity.add_rank_to_results(formatted_results)
            
            search_time = (time.time() - start_time) * 1000  # ms
            
            print(f"🔍 하이브리드 검색 완료: {len(final_results)}개 결과, {search_time:.1f}ms")
            print(f"   📊 가중치 - 벡터: {vector_weight:.1f}, 키워드: {keyword_weight:.1f}")
            
            return final_results
            
        except Exception as e:
            print(f"❌ 하이브리드 검색 실패: {e}")
            return []
    
    def _calculate_hybrid_scores(self, 
                                keyword_results: List[Dict[str, Any]], 
                                vector_results: List[Dict[str, Any]],
                                vector_weight: float, 
                                keyword_weight: float) -> List[Dict[str, Any]]:
        """하이브리드 점수 계산"""
        # 레시피 ID를 키로 하는 딕셔너리 생성
        recipe_scores = {}
        
        # 키워드 검색 결과 처리
        for result in keyword_results:
            recipe_id = result['recipe_id']
            keyword_score = result.get('similarity_percentage', 0) / 100  # 0-1 범위로 변환
            
            if recipe_id not in recipe_scores:
                recipe_scores[recipe_id] = {
                    'recipe_data': result,
                    'keyword_score': keyword_score,
                    'vector_score': 0.0,
                    'has_keyword': True,
                    'has_vector': False
                }
            else:
                recipe_scores[recipe_id]['keyword_score'] = keyword_score
                recipe_scores[recipe_id]['has_keyword'] = True
        
        # 벡터 검색 결과 처리
        for result in vector_results:
            recipe_id = result['recipe_id']
            vector_score = result.get('similarity_percentage', 0) / 100  # 0-1 범위로 변환
            
            if recipe_id not in recipe_scores:
                recipe_scores[recipe_id] = {
                    'recipe_data': result,
                    'keyword_score': 0.0,
                    'vector_score': vector_score,
                    'has_keyword': False,
                    'has_vector': True
                }
            else:
                recipe_scores[recipe_id]['vector_score'] = vector_score
                recipe_scores[recipe_id]['has_vector'] = True
        
        # 하이브리드 점수 계산
        hybrid_results = []
        for recipe_id, scores in recipe_scores.items():
            # 가중 평균으로 하이브리드 점수 계산
            hybrid_score = self.similarity.calculate_hybrid_score(
                scores['vector_score'], 
                scores['keyword_score'],
                vector_weight, 
                keyword_weight
            )
            
            # 결과 데이터 준비
            result_data = scores['recipe_data'].copy()
            result_data['hybrid_score'] = hybrid_score
            result_data['similarity'] = hybrid_score  # 호환성을 위해
            result_data['similarity_percentage'] = config.normalize_score(hybrid_score)
            result_data['component_scores'] = {
                'vector_score': scores['vector_score'],
                'keyword_score': scores['keyword_score'],
                'vector_weight': vector_weight,
                'keyword_weight': keyword_weight
            }
            
            hybrid_results.append(result_data)
        
        return hybrid_results
    
    def search_with_custom_weights(self, query: str, top_k: int = None, 
                                  vector_weight: float = 0.5, keyword_weight: float = 0.5) -> List[Dict[str, Any]]:
        """사용자 정의 가중치로 하이브리드 검색"""
        return self.search(query, top_k, vector_weight, keyword_weight)
    
    def get_search_stats(self) -> Dict[str, Any]:
        """검색 엔진 통계"""
        try:
            keyword_stats = self.keyword_engine.get_search_stats()
            vector_stats = self.vector_engine.get_search_stats()
            
            return {
                'search_type': 'hybrid',
                'total_recipes': keyword_stats.get('total_recipes', 0),
                'search_method': 'weighted combination of keyword + vector search',
                'default_weights': {
                    'vector': config.VECTOR_WEIGHT,
                    'keyword': config.KEYWORD_WEIGHT
                },
                'components': {
                    'keyword_engine': keyword_stats,
                    'vector_engine': vector_stats
                }
            }
        except Exception as e:
            return {'error': str(e)}

# 전역 하이브리드 검색 엔진 인스턴스
hybrid_search_engine = HybridSearchEngine()
