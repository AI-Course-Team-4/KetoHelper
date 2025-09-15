"""
검색 결과 포맷팅 유틸리티
"""
from typing import List, Dict, Any
from ..config.settings import config

class ResultFormatter:
    """검색 결과 포맷터"""
    
    @staticmethod
    def format_search_result(result: Dict[str, Any], search_type: str) -> Dict[str, Any]:
        """단일 검색 결과 포맷팅"""
        formatted = {
            'recipe_id': result.get('recipe_id', ''),
            'title': result.get('title', ''),
            'search_type': search_type,
            'similarity_score': 0.0,
            'similarity_percentage': 0.0,
            'rank': 0,
            'metadata': {
                'has_llm_metadata': bool(result.get('llm_metadata')),
                'has_basic_metadata': bool(result.get('basic_metadata')),
                'blob_length': len(result.get('structured_blob', '')),
                'ingredient_count': len(result.get('raw_ingredients', []))
            }
        }
        
        # 유사도 점수 처리
        if 'similarity' in result:
            formatted['similarity_score'] = result['similarity']
            formatted['similarity_percentage'] = config.normalize_score(result['similarity'])
        
        return formatted
    
    @staticmethod
    def format_search_results(results: List[Dict[str, Any]], search_type: str) -> List[Dict[str, Any]]:
        """검색 결과 리스트 포맷팅"""
        formatted_results = []
        
        for i, result in enumerate(results):
            formatted = ResultFormatter.format_search_result(result, search_type)
            formatted['rank'] = i + 1
            formatted_results.append(formatted)
        
        return formatted_results
    
    @staticmethod
    def format_comparison_summary(
        keyword_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]], 
        hybrid_results: List[Dict[str, Any]],
        query: str
    ) -> Dict[str, Any]:
        """검색 방식 비교 요약 포맷팅"""
        return {
            'query': query,
            'search_time': None,  # 나중에 추가
            'results_summary': {
                'keyword': {
                    'count': len(keyword_results),
                    'top_score': keyword_results[0]['similarity_percentage'] if keyword_results else 0,
                    'avg_score': sum(r['similarity_percentage'] for r in keyword_results) / len(keyword_results) if keyword_results else 0
                },
                'vector': {
                    'count': len(vector_results),
                    'top_score': vector_results[0]['similarity_percentage'] if vector_results else 0,
                    'avg_score': sum(r['similarity_percentage'] for r in vector_results) / len(vector_results) if vector_results else 0
                },
                'hybrid': {
                    'count': len(hybrid_results),
                    'top_score': hybrid_results[0]['similarity_percentage'] if hybrid_results else 0,
                    'avg_score': sum(r['similarity_percentage'] for r in hybrid_results) / len(hybrid_results) if hybrid_results else 0
                }
            }
        }
    
    @staticmethod
    def print_search_results(results: List[Dict[str, Any]], search_type: str, limit: int = 5):
        """검색 결과를 콘솔에 출력"""
        print(f"\n🔍 {search_type.upper()} 검색 결과 (상위 {min(limit, len(results))}개)")
        print("=" * 60)
        
        for i, result in enumerate(results[:limit]):
            print(f"\n{i+1}. {result['title']}")
            print(f"   📊 유사도: {result['similarity_percentage']:.1f}%")
            print(f"   🆔 ID: {result['recipe_id']}")
            
            # 메타데이터 정보
            metadata = result.get('metadata', {})
            if metadata.get('has_llm_metadata'):
                print(f"   🤖 LLM 분석: ✅")
            if metadata.get('ingredient_count', 0) > 0:
                print(f"   🥘 식재료 수: {metadata['ingredient_count']}개")
    
    @staticmethod
    def print_comparison_summary(summary: Dict[str, Any]):
        """비교 요약을 콘솔에 출력"""
        print(f"\n📈 검색 결과 비교: '{summary['query']}'")
        print("=" * 60)
        
        for search_type, stats in summary['results_summary'].items():
            print(f"\n{search_type.upper()}:")
            print(f"  📊 결과 수: {stats['count']}개")
            print(f"  🏆 최고 점수: {stats['top_score']:.1f}%")
            print(f"  📊 평균 점수: {stats['avg_score']:.1f}%")

# 전역 결과 포맷터 인스턴스
result_formatter = ResultFormatter()
