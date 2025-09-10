"""
키워드 검색 모듈

PostgreSQL Full-text Search를 활용한 키워드 기반 검색
"""

import os
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from loguru import logger


class KeywordSearcher:
    """키워드 검색 클래스"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """키워드 검색기 초기화"""
        try:
            self.client: Client = create_client(supabase_url, supabase_key)
            logger.info("KeywordSearcher 초기화 완료")
        except Exception as e:
            logger.error(f"Supabase 클라이언트 초기화 실패: {e}")
            raise
    
    def search_menus(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """키워드 검색 실행
        
        Args:
            query: 검색어 (예: "마라탕", "매운", "소고기 & 국물")
            limit: 최대 결과 수
            
        Returns:
            검색 결과 리스트
        """
        try:
            logger.info(f"키워드 검색 실행 - 쿼리: '{query}', 결과 수: {limit}")
            
            # PostgreSQL Full-text Search 쿼리 전처리
            processed_query = self._preprocess_query(query)
            
            # Supabase RPC 호출
            result = self.client.rpc("keyword_search", {
                "search_query": processed_query,
                "match_count": limit
            }).execute()
            
            if result.data:
                logger.info(f"키워드 검색 완료 - {len(result.data)}개 결과 발견")
                return result.data
            else:
                logger.warning("키워드 검색 결과 없음")
                return []
                
        except Exception as e:
            logger.error(f"키워드 검색 중 오류 발생: {e}")
            return []
    
    def _preprocess_query(self, query: str) -> str:
        """PostgreSQL Full-text Search용 쿼리 전처리
        
        Args:
            query: 원본 검색어
            
        Returns:
            전처리된 검색어
        """
        # 간단한 전처리: 공백을 OR 연산자로 변환
        # "매운 국물" → "매운 | 국물"
        processed = query.strip()
        
        # 이미 연산자가 있으면 그대로 사용
        if any(op in processed for op in ['&', '|', '!', '(', ')']):
            return processed
        
        # 공백으로 분리된 단어들을 OR 연산자로 연결
        words = processed.split()
        if len(words) > 1:
            return ' | '.join(words)
        else:
            return processed
    
    def search_with_ranking(self, query: str, limit: int = 10, min_rank: float = 0.01) -> List[Dict[str, Any]]:
        """랭킹 점수가 포함된 키워드 검색
        
        Args:
            query: 검색어
            limit: 최대 결과 수
            min_rank: 최소 랭킹 점수 (너무 낮은 점수 필터링)
            
        Returns:
            랭킹 점수가 포함된 검색 결과
        """
        results = self.search_menus(query, limit)
        
        # 최소 랭킹 점수 필터링
        filtered_results = []
        for result in results:
            rank = result.get('rank', 0)
            if rank >= min_rank:
                filtered_results.append(result)
            else:
                logger.debug(f"낮은 랭킹으로 필터링됨: {result.get('menu_name')} (rank: {rank})")
        
        logger.info(f"랭킹 필터링 완료: {len(results)} → {len(filtered_results)}개 결과")
        return filtered_results


def main():
    """테스트용 메인 함수"""
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # 환경변수 확인
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL 또는 SUPABASE_KEY 환경변수가 설정되지 않았습니다.")
        return
    
    try:
        # 키워드 검색기 초기화
        searcher = KeywordSearcher(supabase_url, supabase_key)
        
        # 테스트 검색어들
        test_queries = [
            "마라탕",
            "매운",
            "소고기",
            "매운 국물",
            "치즈 파스타"
        ]
        
        for query in test_queries:
            print(f"\n🔍 키워드 검색 테스트: '{query}'")
            print("=" * 50)
            
            results = searcher.search_menus(query, limit=5)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"{i}. 🏪 {result['restaurant_name']}")
                    print(f"   🍽️ {result['menu_name']}")
                    print(f"   📊 랭킹: {result.get('rank', 0):.4f}")
                    print()
            else:
                print("❌ 검색 결과 없음")
            
            print("-" * 50)
    
    except Exception as e:
        logger.error(f"테스트 실행 중 오류: {e}")


if __name__ == "__main__":
    main()
