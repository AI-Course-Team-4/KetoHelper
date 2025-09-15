"""
검색 결과 비교 분석 도구
"""
import time
from typing import List, Dict, Any, Tuple
from ..core.keyword_search import keyword_search_engine
from ..core.vector_search import vector_search_engine
from ..core.hybrid_search import hybrid_search_engine
from ..utils.formatter import result_formatter

class SearchComparator:
    """검색 결과 비교 분석기"""
    
    def __init__(self):
        self.keyword_engine = keyword_search_engine
        self.vector_engine = vector_search_engine
        self.hybrid_engine = hybrid_search_engine
        self.formatter = result_formatter
    
    def compare_all_search_methods(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """모든 검색 방식 비교"""
        start_time = time.time()
        
        print(f"\n🔍 검색 비교 시작: '{query}'")
        print("=" * 60)
        
        try:
            # 1. 각 검색 방식 실행
            keyword_results = self.keyword_engine.search(query, top_k)
            vector_results = self.vector_engine.search(query, top_k)
            hybrid_results = self.hybrid_engine.search(query, top_k)
            
            # 2. 비교 분석
            comparison = self._analyze_comparison(
                query, keyword_results, vector_results, hybrid_results
            )
            
            # 3. 검색 시간 추가
            total_time = (time.time() - start_time) * 1000
            comparison['total_search_time_ms'] = total_time
            
            return comparison
            
        except Exception as e:
            print(f"❌ 검색 비교 실패: {e}")
            return {'error': str(e)}
    
    def _analyze_comparison(self, query: str, 
                          keyword_results: List[Dict[str, Any]], 
                          vector_results: List[Dict[str, Any]], 
                          hybrid_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """검색 결과 비교 분석"""
        
        # 기본 통계
        stats = {
            'query': query,
            'keyword': self._calculate_stats(keyword_results, 'keyword'),
            'vector': self._calculate_stats(vector_results, 'vector'),
            'hybrid': self._calculate_stats(hybrid_results, 'hybrid')
        }
        
        # 결과 겹침 분석
        overlap_analysis = self._analyze_result_overlap(
            keyword_results, vector_results, hybrid_results
        )
        
        # 점수 분포 분석
        score_analysis = self._analyze_score_distribution(
            keyword_results, vector_results, hybrid_results
        )
        
        # 순위 일치도 분석
        rank_analysis = self._analyze_rank_correlation(
            keyword_results, vector_results, hybrid_results
        )
        
        return {
            'query': query,
            'search_stats': stats,
            'overlap_analysis': overlap_analysis,
            'score_analysis': score_analysis,
            'rank_analysis': rank_analysis,
            'results': {
                'keyword': keyword_results,
                'vector': vector_results,
                'hybrid': hybrid_results
            }
        }
    
    def _calculate_stats(self, results: List[Dict[str, Any]], search_type: str) -> Dict[str, Any]:
        """개별 검색 방식 통계 계산"""
        if not results:
            return {
                'count': 0,
                'top_score': 0.0,
                'avg_score': 0.0,
                'min_score': 0.0,
                'max_score': 0.0,
                'score_std': 0.0
            }
        
        scores = [r.get('similarity_percentage', 0) for r in results]
        
        return {
            'count': len(results),
            'top_score': max(scores),
            'avg_score': sum(scores) / len(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'score_std': self._calculate_std(scores)
        }
    
    def _analyze_result_overlap(self, 
                              keyword_results: List[Dict[str, Any]], 
                              vector_results: List[Dict[str, Any]], 
                              hybrid_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """결과 겹침 분석"""
        
        # 레시피 ID 세트 생성
        keyword_ids = set(r['recipe_id'] for r in keyword_results)
        vector_ids = set(r['recipe_id'] for r in vector_results)
        hybrid_ids = set(r['recipe_id'] for r in hybrid_results)
        
        # 겹침 계산
        keyword_vector_overlap = len(keyword_ids & vector_ids)
        keyword_hybrid_overlap = len(keyword_ids & hybrid_ids)
        vector_hybrid_overlap = len(vector_ids & hybrid_ids)
        all_three_overlap = len(keyword_ids & vector_ids & hybrid_ids)
        
        return {
            'keyword_vector_overlap': {
                'count': keyword_vector_overlap,
                'percentage': (keyword_vector_overlap / max(len(keyword_ids), len(vector_ids), 1)) * 100
            },
            'keyword_hybrid_overlap': {
                'count': keyword_hybrid_overlap,
                'percentage': (keyword_hybrid_overlap / max(len(keyword_ids), len(hybrid_ids), 1)) * 100
            },
            'vector_hybrid_overlap': {
                'count': vector_hybrid_overlap,
                'percentage': (vector_hybrid_overlap / max(len(vector_ids), len(hybrid_ids), 1)) * 100
            },
            'all_three_overlap': {
                'count': all_three_overlap,
                'percentage': (all_three_overlap / max(len(keyword_ids), len(vector_ids), len(hybrid_ids), 1)) * 100
            }
        }
    
    def _analyze_score_distribution(self, 
                                  keyword_results: List[Dict[str, Any]], 
                                  vector_results: List[Dict[str, Any]], 
                                  hybrid_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """점수 분포 분석"""
        
        def get_score_ranges(results):
            if not results:
                return {'high': 0, 'medium': 0, 'low': 0}
            
            high = sum(1 for r in results if r.get('similarity_percentage', 0) >= 70)
            medium = sum(1 for r in results if 30 <= r.get('similarity_percentage', 0) < 70)
            low = sum(1 for r in results if r.get('similarity_percentage', 0) < 30)
            
            return {'high': high, 'medium': medium, 'low': low}
        
        return {
            'keyword': get_score_ranges(keyword_results),
            'vector': get_score_ranges(vector_results),
            'hybrid': get_score_ranges(hybrid_results)
        }
    
    def _analyze_rank_correlation(self, 
                                keyword_results: List[Dict[str, Any]], 
                                vector_results: List[Dict[str, Any]], 
                                hybrid_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """순위 일치도 분석"""
        
        # 공통 레시피들의 순위 비교
        all_ids = set()
        for results in [keyword_results, vector_results, hybrid_results]:
            all_ids.update(r['recipe_id'] for r in results)
        
        rank_correlations = {}
        
        for recipe_id in all_ids:
            ranks = {}
            for search_type, results in [('keyword', keyword_results), 
                                       ('vector', vector_results), 
                                       ('hybrid', hybrid_results)]:
                for i, result in enumerate(results):
                    if result['recipe_id'] == recipe_id:
                        ranks[search_type] = i + 1
                        break
            
            if len(ranks) >= 2:  # 최소 2개 검색 방식에서 발견된 경우
                rank_correlations[recipe_id] = ranks
        
        return {
            'common_recipes_count': len(rank_correlations),
            'rank_correlations': rank_correlations
        }
    
    def _calculate_std(self, scores: List[float]) -> float:
        """표준편차 계산"""
        if len(scores) <= 1:
            return 0.0
        
        mean = sum(scores) / len(scores)
        variance = sum((x - mean) ** 2 for x in scores) / (len(scores) - 1)
        return variance ** 0.5
    
    def print_comparison_summary(self, comparison: Dict[str, Any]):
        """비교 결과 요약 출력"""
        if 'error' in comparison:
            print(f"❌ 비교 분석 실패: {comparison['error']}")
            return
        
        print(f"\n📊 검색 결과 비교 분석: '{comparison['query']}'")
        print("=" * 80)
        
        # 기본 통계
        stats = comparison['search_stats']
        print(f"\n📈 기본 통계:")
        for search_type, stat in stats.items():
            print(f"\n{search_type.upper()}:")
            print(f"  📊 결과 수: {stat['count']}개")
            print(f"  🏆 최고 점수: {stat['top_score']:.1f}%")
            print(f"  📊 평균 점수: {stat['avg_score']:.1f}%")
            print(f"  📉 최저 점수: {stat['min_score']:.1f}%")
            print(f"  📊 표준편차: {stat['score_std']:.1f}%")
        
        # 겹침 분석
        overlap = comparison['overlap_analysis']
        print(f"\n🔄 결과 겹침 분석:")
        print(f"  🔗 키워드-벡터 겹침: {overlap['keyword_vector_overlap']['count']}개 ({overlap['keyword_vector_overlap']['percentage']:.1f}%)")
        print(f"  🔗 키워드-하이브리드 겹침: {overlap['keyword_hybrid_overlap']['count']}개 ({overlap['keyword_hybrid_overlap']['percentage']:.1f}%)")
        print(f"  🔗 벡터-하이브리드 겹침: {overlap['vector_hybrid_overlap']['count']}개 ({overlap['vector_hybrid_overlap']['percentage']:.1f}%)")
        print(f"  🔗 3방식 모두 겹침: {overlap['all_three_overlap']['count']}개 ({overlap['all_three_overlap']['percentage']:.1f}%)")
        
        # 점수 분포
        score_dist = comparison['score_analysis']
        print(f"\n📊 점수 분포:")
        for search_type, dist in score_dist.items():
            print(f"  {search_type.upper()}: 높음({dist['high']}) 중간({dist['medium']}) 낮음({dist['low']})")
        
        # 검색 시간
        if 'total_search_time_ms' in comparison:
            print(f"\n⏱️ 총 검색 시간: {comparison['total_search_time_ms']:.1f}ms")

# 전역 검색 비교기 인스턴스
search_comparator = SearchComparator()
