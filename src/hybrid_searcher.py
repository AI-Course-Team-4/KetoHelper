"""
하이브리드 검색 모듈

벡터 검색과 키워드 검색을 결합한 RRF(Reciprocal Rank Fusion) 알고리즘
"""

import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

from .vector_searcher import VectorSearcher
from .keyword_searcher import KeywordSearcher


@dataclass
class HybridSearchConfig:
    """하이브리드 검색 설정"""
    vector_weight: float = 0.6  # 벡터 검색 가중치 (0.0 ~ 1.0)
    keyword_weight: float = 0.4  # 키워드 검색 가중치 (0.0 ~ 1.0)
    rrf_k: int = 20  # RRF 상수 (상위 가중 강화)
    vector_results_count: int = 20  # 벡터 검색에서 가져올 결과 수
    keyword_results_count: int = 20  # 키워드 검색에서 가져올 결과 수
    final_results_count: int = 5  # 최종 결과 수
    vector_threshold: float = 0.1  # 벡터 검색 유사도 임계값
    keyword_min_rank: float = 0.01  # 키워드 검색 최소 랭킹 점수


class HybridSearcher:
    """하이브리드 검색 클래스"""
    
    def __init__(self, supabase_url: str, supabase_key: str, openai_api_key: str, 
                 config: Optional[HybridSearchConfig] = None):
        """하이브리드 검색기 초기화"""
        self.config = config or HybridSearchConfig()
        
        # 가중치 정규화
        total_weight = self.config.vector_weight + self.config.keyword_weight
        if total_weight != 1.0:
            self.config.vector_weight = self.config.vector_weight / total_weight
            self.config.keyword_weight = self.config.keyword_weight / total_weight
            logger.info(f"가중치 정규화: 벡터={self.config.vector_weight:.2f}, 키워드={self.config.keyword_weight:.2f}")
        
        try:
            # 벡터 검색기 초기화 (환경변수 기반 초기화)
            self.vector_searcher = VectorSearcher()
            
            # 키워드 검색기 초기화
            self.keyword_searcher = KeywordSearcher(supabase_url, supabase_key)
            
            logger.info("HybridSearcher 초기화 완료")
            
        except Exception as e:
            logger.error(f"HybridSearcher 초기화 실패: {e}")
            raise
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """하이브리드 검색 실행
        
        Args:
            query: 검색어
            
        Returns:
            하이브리드 점수가 포함된 검색 결과 리스트
        """
        try:
            logger.info(f"하이브리드 검색 실행 - 쿼리: '{query}'")
            
            # 1. 벡터 검색 실행
            vector_results = self._get_vector_results(query)
            logger.info(f"벡터 검색 결과: {len(vector_results)}개")
            
            # 2. 키워드 검색 실행
            keyword_results = self._get_keyword_results(query)
            logger.info(f"키워드 검색 결과: {len(keyword_results)}개")
            
            # 3. RRF 점수 계산 및 결합
            hybrid_results = self._combine_results_rrf(vector_results, keyword_results)
            logger.info(f"하이브리드 검색 완료: {len(hybrid_results)}개 결과")
            
            return hybrid_results
            
        except Exception as e:
            logger.error(f"하이브리드 검색 중 오류 발생: {e}")
            return []
    
    def _get_vector_results(self, query: str) -> List[Dict[str, Any]]:
        """벡터 검색 결과 가져오기"""
        try:
            results = self.vector_searcher.search_similar_menus(
                query=query,
                match_count=self.config.vector_results_count,
                match_threshold=self.config.vector_threshold
            )
            return results
        except Exception as e:
            logger.error(f"벡터 검색 실행 중 오류: {e}")
            return []
    
    def _get_keyword_results(self, query: str) -> List[Dict[str, Any]]:
        """키워드 검색 결과 가져오기"""
        try:
            results = self.keyword_searcher.search_with_ranking(
                query=query,
                limit=self.config.keyword_results_count,
                min_rank=self.config.keyword_min_rank
            )
            return results
        except Exception as e:
            logger.error(f"키워드 검색 실행 중 오류: {e}")
            return []
    
    def _combine_results_rrf(self, vector_results: List[Dict], keyword_results: List[Dict]) -> List[Dict]:
        """RRF(Reciprocal Rank Fusion) 알고리즘으로 결과 결합
        
        RRF 공식: score = 1 / (k + rank)
        하이브리드 점수 = vector_weight * vector_rrf + keyword_weight * keyword_rrf
        """
        combined_scores = {}
        k = self.config.rrf_k
        
        # 벡터 검색 결과의 RRF 점수 계산
        for rank, result in enumerate(vector_results, 1):
            item_id = result.get('id')
            if item_id is None:
                continue
                
            vector_rrf = 1 / (k + rank)
            combined_scores[item_id] = {
                'data': result,
                'vector_rrf': vector_rrf,
                'keyword_rrf': 0.0,
                'vector_rank': rank,
                'keyword_rank': None,
                'vector_score': result.get('similarity', 0.0),
                'keyword_score': 0.0
            }
        
        # 키워드 검색 결과의 RRF 점수 계산
        for rank, result in enumerate(keyword_results, 1):
            item_id = result.get('id')
            if item_id is None:
                continue
                
            keyword_rrf = 1 / (k + rank)
            keyword_score = result.get('rank', 0.0)
            
            if item_id in combined_scores:
                # 이미 벡터 검색에서 발견된 항목
                combined_scores[item_id]['keyword_rrf'] = keyword_rrf
                combined_scores[item_id]['keyword_rank'] = rank
                combined_scores[item_id]['keyword_score'] = keyword_score
            else:
                # 키워드 검색에서만 발견된 항목
                combined_scores[item_id] = {
                    'data': result,
                    'vector_rrf': 0.0,
                    'keyword_rrf': keyword_rrf,
                    'vector_rank': None,
                    'keyword_rank': rank,
                    'vector_score': 0.0,
                    'keyword_score': keyword_score
                }
        
        # 하이브리드 점수 계산
        for item in combined_scores.values():
            item['hybrid_score'] = (
                self.config.vector_weight * item['vector_rrf'] + 
                self.config.keyword_weight * item['keyword_rrf']
            )
        
        # 하이브리드 점수로 정렬
        sorted_results = sorted(
            combined_scores.values(),
            key=lambda x: x['hybrid_score'],
            reverse=True
        )
        
        # 최종 결과 수만큼 반환
        final_results = sorted_results[:self.config.final_results_count]
        
        # 결과 통계 로깅
        vector_only = sum(1 for r in final_results if r['keyword_rank'] is None)
        keyword_only = sum(1 for r in final_results if r['vector_rank'] is None)
        both = sum(1 for r in final_results if r['vector_rank'] is not None and r['keyword_rank'] is not None)
        
        logger.info(f"결과 구성: 벡터만={vector_only}, 키워드만={keyword_only}, 둘다={both}")
        
        return final_results
    
    def search_with_details(self, query: str) -> Dict[str, Any]:
        """상세 정보가 포함된 하이브리드 검색
        
        Returns:
            검색 결과와 함께 각 검색 방법별 결과도 포함
        """
        try:
            logger.info(f"상세 하이브리드 검색 실행 - 쿼리: '{query}'")
            
            # 각 검색 방법별 결과
            vector_results = self._get_vector_results(query)
            keyword_results = self._get_keyword_results(query)
            hybrid_results = self._combine_results_rrf(vector_results, keyword_results)
            
            return {
                'query': query,
                'hybrid_results': hybrid_results,
                'vector_results': vector_results[:5],  # 상위 5개만
                'keyword_results': keyword_results[:5],  # 상위 5개만
                'config': {
                    'vector_weight': self.config.vector_weight,
                    'keyword_weight': self.config.keyword_weight,
                    'rrf_k': self.config.rrf_k
                },
                'stats': {
                    'vector_count': len(vector_results),
                    'keyword_count': len(keyword_results),
                    'hybrid_count': len(hybrid_results)
                }
            }
            
        except Exception as e:
            logger.error(f"상세 하이브리드 검색 중 오류: {e}")
            return {
                'query': query,
                'hybrid_results': [],
                'vector_results': [],
                'keyword_results': [],
                'error': str(e)
            }


def main():
    """테스트용 메인 함수"""
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 환경변수 확인
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not all([supabase_url, supabase_key, openai_api_key]):
        logger.error("필요한 환경변수가 설정되지 않았습니다.")
        return
    
    try:
        # 하이브리드 검색기 초기화
        config = HybridSearchConfig(
            vector_weight=0.6,
            keyword_weight=0.4,
            final_results_count=5
        )
        searcher = HybridSearcher(supabase_url, supabase_key, openai_api_key, config)
        
        # 테스트 검색어
        test_queries = [
            "매운 음식",
            "청양",
            "마라탕",
            "달달한 디저트"
        ]
        
        for query in test_queries:
            print(f"\n🔥 하이브리드 검색 테스트: '{query}'")
            print("=" * 60)
            
            # 상세 검색 실행
            results = searcher.search_with_details(query)
            
            # 하이브리드 결과 출력
            hybrid_results = results.get('hybrid_results', [])
            if hybrid_results:
                print(f"🎯 하이브리드 검색 결과 ({len(hybrid_results)}개):")
                for i, result in enumerate(hybrid_results, 1):
                    data = result['data']
                    print(f"\n{i}. 🏪 {data['restaurant_name']} - {data['menu_name']}")
                    print(f"   🔥 하이브리드 점수: {result['hybrid_score']:.4f}")
                    print(f"   📊 벡터 순위: {result['vector_rank']} (점수: {result['vector_score']:.3f})")
                    print(f"   🔍 키워드 순위: {result['keyword_rank']} (점수: {result['keyword_score']:.4f})")
            else:
                print("❌ 하이브리드 검색 결과 없음")
            
            # 통계 정보
            stats = results.get('stats', {})
            print(f"\n📈 검색 통계:")
            print(f"   - 벡터 검색: {stats.get('vector_count', 0)}개")
            print(f"   - 키워드 검색: {stats.get('keyword_count', 0)}개")
            print(f"   - 하이브리드 결과: {stats.get('hybrid_count', 0)}개")
            
            print("-" * 60)
    
    except Exception as e:
        logger.error(f"테스트 실행 중 오류: {e}")


if __name__ == "__main__":
    main()
