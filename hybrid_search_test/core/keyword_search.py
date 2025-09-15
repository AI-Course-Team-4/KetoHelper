"""
키워드 검색 엔진
Supabase full-text search 활용
"""
import time
from typing import List, Dict, Any
from ..utils.database import db_manager
from ..utils.similarity import similarity_calculator
from ..utils.formatter import result_formatter
from ..config.settings import config

class KeywordSearchEngine:
    """키워드 검색 엔진"""
    
    def __init__(self):
        self.db = db_manager
        self.similarity = similarity_calculator
        self.formatter = result_formatter
    
    def search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """키워드 검색 실행"""
        if top_k is None:
            top_k = config.DEFAULT_TOP_K
        
        start_time = time.time()
        
        try:
            # 1. Supabase full-text search 실행
            raw_results = self.db.search_by_keyword(query, top_k)
            
            # 2. 키워드 매칭 점수 계산
            scored_results = self._calculate_keyword_scores(raw_results, query)
            
            # 3. 점수 순으로 정렬
            ranked_results = self.similarity.rank_results(scored_results, 'keyword_score')
            
            # 4. 결과 포맷팅
            formatted_results = self.formatter.format_search_results(ranked_results, 'keyword')
            
            # 5. 순위 추가
            final_results = self.similarity.add_rank_to_results(formatted_results)
            
            search_time = (time.time() - start_time) * 1000  # ms
            
            print(f"🔍 키워드 검색 완료: {len(final_results)}개 결과, {search_time:.1f}ms")
            
            return final_results
            
        except Exception as e:
            print(f"❌ 키워드 검색 실패: {e}")
            return []
    
    def _calculate_keyword_scores(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """키워드 매칭 점수 계산"""
        query_words = query.lower().split()
        scored_results = []
        
        for result in results:
            # 검색 대상 텍스트 수집
            search_text = self._extract_searchable_text(result)
            search_text_lower = search_text.lower()
            
            # 키워드 매칭 점수 계산
            score = self._calculate_matching_score(search_text_lower, query_words)
            
            # 결과에 점수 추가
            result_with_score = result.copy()
            result_with_score['keyword_score'] = score
            result_with_score['similarity'] = score  # 호환성을 위해
            
            scored_results.append(result_with_score)
        
        return scored_results
    
    def _extract_searchable_text(self, result: Dict[str, Any]) -> str:
        """검색 가능한 텍스트 추출"""
        text_parts = []
        
        # 제목
        if result.get('title'):
            text_parts.append(result['title'])
        
        # 구조화된 blob
        if result.get('structured_blob'):
            text_parts.append(result['structured_blob'])
        
        # LLM 메타데이터에서 키워드 추출
        llm_metadata = result.get('llm_metadata', {})
        if isinstance(llm_metadata, dict):
            # 키워드 필드들 추출
            keyword_fields = ['keywords', 'key_ingredients', 'cuisine_type', 'cooking_method', 'dish_category']
            for field in keyword_fields:
                value = llm_metadata.get(field)
                if value:
                    if isinstance(value, list):
                        text_parts.extend([str(item) for item in value])
                    else:
                        text_parts.append(str(value))
        
        return ' '.join(text_parts)
    
    def _calculate_matching_score(self, text: str, query_words: List[str]) -> float:
        """키워드 매칭 점수 계산 (0-1 범위)"""
        if not query_words or not text:
            return 0.0
        
        total_words = len(query_words)
        matched_words = 0
        
        for word in query_words:
            if word in text:
                matched_words += 1
        
        # 기본 매칭 점수
        base_score = matched_words / total_words
        
        # 추가 점수: 연속된 단어 매칭 보너스
        bonus_score = 0.0
        if len(query_words) > 1:
            query_phrase = ' '.join(query_words)
            if query_phrase in text:
                bonus_score = 0.2  # 20% 보너스
        
        # 최종 점수 (0-1 범위)
        final_score = min(1.0, base_score + bonus_score)
        
        return final_score
    
    def get_search_stats(self) -> Dict[str, Any]:
        """검색 엔진 통계"""
        try:
            total_count = self.db.get_total_count()
            return {
                'search_type': 'keyword',
                'total_recipes': total_count,
                'search_method': 'Supabase full-text search',
                'scoring_method': 'keyword matching + phrase bonus'
            }
        except Exception as e:
            return {'error': str(e)}

# 전역 키워드 검색 엔진 인스턴스
keyword_search_engine = KeywordSearchEngine()
