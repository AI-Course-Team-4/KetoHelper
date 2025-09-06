"""
벡터 검색 서비스 모듈
"""
import logging
from typing import List, Dict, Any, Optional

from database import DatabaseManager
from embedding import EmbeddingGenerator

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self):
        """검색 서비스 초기화"""
        self.db = DatabaseManager()
        self.embedding_gen = EmbeddingGenerator(self.db)
        logger.info("검색 서비스 초기화 완료")
    
    def search(self, preference_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        벡터 유사도 기반 메뉴 검색
        
        Args:
            preference_text: 사용자 선호도 텍스트
            top_k: 반환할 결과 개수
        
        Returns:
            검색 결과 리스트
        """
        try:
            # 1. 검색 쿼리 임베딩 생성
            query_embedding = self.embedding_gen.generate_embedding(preference_text)
            if not query_embedding:
                logger.error("쿼리 임베딩 생성 실패")
                return []
            
            # 2. 벡터 검색 수행
            raw_results = self.db.vector_search(query_embedding, top_k)
            
            # 3. 결과 포맷팅
            formatted_results = []
            for result in raw_results:
                formatted_result = {
                    'restaurant_name': result.get('restaurant_name'),
                    'menu_name': result.get('menu_name'),
                    'address': result.get('address'),
                    'price': result.get('price'),
                    'category': result.get('category'),
                    'score': round(result.get('similarity', 0), 4)  # 유사도 점수
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"검색 완료: '{preference_text}' -> {len(formatted_results)}개 결과")
            return formatted_results
            
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {e}")
            return []
    
    def get_search_stats(self) -> Dict[str, Any]:
        """검색 가능한 메뉴 통계"""
        try:
            total_count = self.db.get_menu_count()
            without_embedding = len(self.db.get_menus_without_embedding())
            searchable_count = total_count - without_embedding
            
            return {
                'total_menus': total_count,
                'searchable_menus': searchable_count,
                'non_searchable_menus': without_embedding,
                'search_coverage': (searchable_count / total_count * 100) if total_count > 0 else 0
            }
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """서비스 상태 확인"""
        try:
            # 데이터베이스 연결 확인
            db_healthy = self.db.test_connection()
            
            # 검색 가능한 메뉴 수 확인
            stats = self.get_search_stats()
            searchable_count = stats.get('searchable_menus', 0)
            
            # 간단한 검색 테스트
            test_results = self.search("테스트", 1)
            search_working = len(test_results) > 0
            
            status = "healthy" if (db_healthy and searchable_count > 0 and search_working) else "unhealthy"
            
            return {
                'status': status,
                'database_connected': db_healthy,
                'searchable_menus': searchable_count,
                'search_working': search_working,
                'timestamp': None  # 필요시 추가
            }
        except Exception as e:
            logger.error(f"헬스체크 실패: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
