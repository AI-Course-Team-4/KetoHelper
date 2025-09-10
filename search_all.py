"""
통합 검색 시스템

벡터 검색, 키워드 검색, 하이브리드 검색을 모두 테스트할 수 있는 인터페이스
"""

import os
import sys
import time
from typing import Dict, Any, List
from dotenv import load_dotenv
from loguru import logger

# 프로젝트 루트를 Python path에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.vector_searcher import VectorSearcher
from src.keyword_searcher import KeywordSearcher
from src.hybrid_searcher import HybridSearcher, HybridSearchConfig


class SearchComparator:
    """검색 방법 비교 클래스"""
    
    def __init__(self):
        """검색 비교기 초기화"""
        load_dotenv()
        
        # 환경변수 확인
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not all([self.supabase_url, self.supabase_key, self.openai_api_key]):
            raise ValueError("필요한 환경변수가 설정되지 않았습니다.")
        
        # 검색기들 초기화
        try:
            # VectorSearcher는 환경변수 기반으로 초기화됨
            self.vector_searcher = VectorSearcher()
            self.keyword_searcher = KeywordSearcher(
                self.supabase_url, self.supabase_key
            )
            
            # 하이브리드 검색 설정
            # 추천 기본값 사용 (rrf_k=20, 0.6/0.4, 최종 5개)
            hybrid_config = HybridSearchConfig()
            self.hybrid_searcher = HybridSearcher(
                self.supabase_url, self.supabase_key, self.openai_api_key, hybrid_config
            )
            
            logger.info("모든 검색기 초기화 완료")
            
        except Exception as e:
            logger.error(f"검색기 초기화 실패: {e}")
            raise
    
    def compare_all_methods(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """모든 검색 방법 비교 실행
        
        Args:
            query: 검색어
            limit: 각 검색 방법별 결과 수
            
        Returns:
            모든 검색 결과와 성능 정보
        """
        results = {
            'query': query,
            'vector': {'results': [], 'time': 0, 'error': None},
            'keyword': {'results': [], 'time': 0, 'error': None},
            'hybrid': {'results': [], 'time': 0, 'error': None}
        }
        
        # 1. 벡터 검색
        try:
            start_time = time.time()
            vector_results = self.vector_searcher.search_similar_menus(
                query=query, match_count=limit, match_threshold=0.1
            )
            end_time = time.time()
            
            results['vector']['results'] = vector_results
            results['vector']['time'] = end_time - start_time
            logger.info(f"벡터 검색 완료: {len(vector_results)}개, {results['vector']['time']:.3f}초")
            
        except Exception as e:
            results['vector']['error'] = str(e)
            logger.error(f"벡터 검색 오류: {e}")
        
        # 2. 키워드 검색
        try:
            start_time = time.time()
            keyword_results = self.keyword_searcher.search_menus(
                query=query, limit=limit
            )
            end_time = time.time()
            
            results['keyword']['results'] = keyword_results
            results['keyword']['time'] = end_time - start_time
            logger.info(f"키워드 검색 완료: {len(keyword_results)}개, {results['keyword']['time']:.3f}초")
            
        except Exception as e:
            results['keyword']['error'] = str(e)
            logger.error(f"키워드 검색 오류: {e}")
        
        # 3. 하이브리드 검색
        try:
            start_time = time.time()
            hybrid_results = self.hybrid_searcher.search(query)
            end_time = time.time()
            
            results['hybrid']['results'] = hybrid_results
            results['hybrid']['time'] = end_time - start_time
            logger.info(f"하이브리드 검색 완료: {len(hybrid_results)}개, {results['hybrid']['time']:.3f}초")
            
        except Exception as e:
            results['hybrid']['error'] = str(e)
            logger.error(f"하이브리드 검색 오류: {e}")
        
        return results
    
    def print_comparison_results(self, results: Dict[str, Any]):
        """검색 결과 비교 출력"""
        query = results['query']
        
        print(f"\n{'='*80}")
        print(f"🔍 검색어: '{query}'")
        print(f"{'='*80}")
        
        # 각 검색 방법별 결과 출력
        methods = [
            ('벡터 검색 🎯', 'vector'),
            ('키워드 검색 🔍', 'keyword'),
            ('하이브리드 검색 🔥', 'hybrid')
        ]
        
        for method_name, method_key in methods:
            method_data = results[method_key]
            
            print(f"\n{'-'*50}")
            print(f"{method_name}")
            print(f"{'-'*50}")
            
            if method_data['error']:
                print(f"❌ 오류: {method_data['error']}")
                continue
            
            method_results = method_data['results']
            search_time = method_data['time']
            
            print(f"⏱️  검색 시간: {search_time:.3f}초")
            print(f"📊 결과 수: {len(method_results)}개")
            
            if method_results:
                print(f"\n🏆 상위 결과:")
                for i, result in enumerate(method_results[:3], 1):
                    if method_key == 'hybrid':
                        data = result['data']
                        score = result['hybrid_score']
                        score_type = "하이브리드"
                    else:
                        data = result
                        if method_key == 'vector':
                            score = result.get('similarity', 0)
                            score_type = "유사도"
                        else:  # keyword
                            score = result.get('rank', 0)
                            score_type = "랭킹"
                    
                    print(f"  {i}. 🏪 {data['restaurant_name']}")
                    print(f"     🍽️ {data['menu_name']}")
                    print(f"     📈 {score_type}: {score:.4f}")
                    
                    if method_key == 'hybrid':
                        print(f"     📊 벡터순위: {result.get('vector_rank', 'N/A')}, "
                              f"키워드순위: {result.get('keyword_rank', 'N/A')}")
                    print()
            else:
                print("❌ 검색 결과 없음")
        
        # 성능 요약
        print(f"\n{'='*50}")
        print("📈 성능 요약")
        print(f"{'='*50}")
        
        for method_name, method_key in methods:
            method_data = results[method_key]
            if not method_data['error']:
                result_count = len(method_data['results'])
                search_time = method_data['time']
                print(f"{method_name:<15}: {result_count:>2}개 결과, {search_time:>6.3f}초")


def main():
    """메인 함수"""
    try:
        # 검색 비교기 초기화
        comparator = SearchComparator()
        
        print("🚀 통합 검색 시스템")
        print("=" * 80)
        print("💡 벡터 검색, 키워드 검색, 하이브리드 검색을 모두 비교합니다")
        print("❌ 종료하려면 'quit' 또는 'exit'를 입력하세요")
        print("=" * 80)
        
        while True:
            try:
                # 사용자 입력
                query = input("\n🔍 검색어를 입력하세요: ").strip()
                
                if not query:
                    continue
                
                if query.lower() in ['quit', 'exit', '종료']:
                    print("\n👋 검색 시스템을 종료합니다.")
                    break
                
                print(f"\n🔍 검색 중: '{query}'")
                print("⏳ 잠시만 기다려주세요...")
                
                # 모든 검색 방법 비교 실행
                results = comparator.compare_all_methods(query)
                
                # 결과 출력
                comparator.print_comparison_results(results)
                
            except KeyboardInterrupt:
                print("\n\n👋 사용자가 프로그램을 중단했습니다.")
                break
            except Exception as e:
                logger.error(f"검색 실행 중 오류: {e}")
                print(f"❌ 검색 중 오류가 발생했습니다: {e}")
    
    except Exception as e:
        logger.error(f"프로그램 초기화 실패: {e}")
        print(f"❌ 프로그램 초기화 실패: {e}")


if __name__ == "__main__":
    main()
