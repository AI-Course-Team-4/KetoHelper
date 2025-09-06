"""
정규화된 3개 테이블 구조를 위한 Supabase 데이터베이스 어댑터
"""
from supabase import create_client, Client
from typing import List, Dict, Any, Optional, Tuple
import logging
from datetime import datetime

from config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

class DatabaseAdapter:
    def __init__(self):
        """Supabase 클라이언트 초기화"""
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL과 KEY가 설정되지 않았습니다")
        
        self.client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase 클라이언트 초기화 완료")
    
    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            result = self.client.table('restaurants').select('count').execute()
            logger.info("데이터베이스 연결 테스트 성공")
            return True
        except Exception as e:
            logger.error(f"데이터베이스 연결 테스트 실패: {e}")
            return False
    
    # ========== RESTAURANTS 테이블 관련 ==========
    
    def upsert_restaurant(self, restaurant_data: Dict[str, Any]) -> str:
        """식당 정보 저장 또는 업데이트 (중복 체크)"""
        try:
            # 동일한 이름과 주소의 식당이 있는지 확인
            existing = self.client.table('restaurants').select('id').eq(
                'name', restaurant_data['name']
            ).eq('address', restaurant_data['address']).execute()
            
            if existing.data:
                # 기존 식당 업데이트
                restaurant_id = existing.data[0]['id']
                restaurant_data['updated_at'] = datetime.now().isoformat()
                
                self.client.table('restaurants').update(restaurant_data).eq(
                    'id', restaurant_id
                ).execute()
                
                logger.info(f"식당 정보 업데이트: {restaurant_data['name']} ({restaurant_id})")
                return restaurant_id
            else:
                # 새 식당 저장
                result = self.client.table('restaurants').insert(restaurant_data).execute()
                restaurant_id = result.data[0]['id']
                logger.info(f"새 식당 저장: {restaurant_data['name']} ({restaurant_id})")
                return restaurant_id
                
        except Exception as e:
            logger.error(f"식당 저장 실패: {e}")
            return None
    
    def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Dict[str, Any]]:
        """ID로 식당 정보 조회"""
        try:
            result = self.client.table('restaurants').select('*').eq('id', restaurant_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"식당 조회 실패: {e}")
            return None
    
    def get_restaurants_by_source(self, source: str) -> List[Dict[str, Any]]:
        """소스별 식당 목록 조회"""
        try:
            result = self.client.table('restaurants').select('*').eq('source', source).execute()
            return result.data
        except Exception as e:
            logger.error(f"소스별 식당 조회 실패: {e}")
            return []
    
    # ========== MENUS 테이블 관련 ==========
    
    def insert_menu(self, menu_data: Dict[str, Any]) -> Optional[str]:
        """단일 메뉴 저장"""
        try:
            result = self.client.table('menus').insert(menu_data).execute()
            if result.data:
                menu_id = result.data[0]['id']
                logger.info(f"메뉴 저장 성공: {menu_data['name']} ({menu_id})")
                return menu_id
            return None
        except Exception as e:
            logger.error(f"메뉴 저장 실패: {e}")
            return None
    
    def insert_menus_batch(self, menus_data: List[Dict[str, Any]]) -> List[str]:
        """배치로 메뉴 저장"""
        try:
            result = self.client.table('menus').insert(menus_data).execute()
            menu_ids = [menu['id'] for menu in result.data]
            logger.info(f"메뉴 배치 저장 성공: {len(menu_ids)}개")
            return menu_ids
        except Exception as e:
            logger.error(f"메뉴 배치 저장 실패: {e}")
            return []
    
    def update_menu_embedding(self, menu_id: str, embedding: List[float]) -> bool:
        """메뉴의 임베딩 업데이트"""
        try:
            self.client.table('menus').update({
                'embedding': embedding,
                'updated_at': datetime.now().isoformat()
            }).eq('id', menu_id).execute()
            return True
        except Exception as e:
            logger.error(f"임베딩 업데이트 실패: {e}")
            return False
    
    def get_menus_without_embedding(self) -> List[Dict[str, Any]]:
        """임베딩이 없는 메뉴들 조회 (JOIN으로 식당 정보 포함)"""
        try:
            result = self.client.table('menus').select(
                'id, name, menu_text, restaurant_id, restaurants(name, address)'
            ).is_('embedding', 'null').execute()
            return result.data
        except Exception as e:
            logger.error(f"임베딩 없는 메뉴 조회 실패: {e}")
            return []
    
    def get_menus_by_restaurant(self, restaurant_id: str) -> List[Dict[str, Any]]:
        """특정 식당의 메뉴 목록 조회"""
        try:
            result = self.client.table('menus').select('*').eq(
                'restaurant_id', restaurant_id
            ).execute()
            return result.data
        except Exception as e:
            logger.error(f"식당별 메뉴 조회 실패: {e}")
            return []
    
    # ========== CRAWLING_LOGS 테이블 관련 ==========
    
    def insert_crawling_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """크롤링 로그 저장"""
        try:
            result = self.client.table('crawling_logs').insert(log_data).execute()
            if result.data:
                log_id = result.data[0]['id']
                logger.info(f"크롤링 로그 저장: {log_data.get('site')} - {log_data.get('status')}")
                return log_id
            return None
        except Exception as e:
            logger.error(f"크롤링 로그 저장 실패: {e}")
            return None
    
    def get_crawling_logs(self, restaurant_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """크롤링 로그 조회"""
        try:
            query = self.client.table('crawling_logs').select(
                '*, restaurants(name, address)'
            ).order('crawled_at', desc=True).limit(limit)
            
            if restaurant_id:
                query = query.eq('restaurant_id', restaurant_id)
            
            result = query.execute()
            return result.data
        except Exception as e:
            logger.error(f"크롤링 로그 조회 실패: {e}")
            return []
    
    # ========== 벡터 검색 관련 ==========
    
    def vector_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """벡터 검색 (JOIN된 결과 반환)"""
        try:
            result = self.client.rpc('vector_search_with_restaurant', {
                'query_embedding': query_embedding,
                'match_threshold': 0.0,
                'match_count': top_k
            }).execute()
            return result.data
        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            return []
    
    # ========== 통계 및 모니터링 ==========
    
    def get_statistics(self) -> Dict[str, int]:
        """전체 통계 조회"""
        try:
            restaurants_count = len(self.client.table('restaurants').select('count').execute().data)
            menus_count = len(self.client.table('menus').select('count').execute().data)
            
            menus_with_embedding = len(
                self.client.table('menus').select('count').not_.is_('embedding', 'null').execute().data
            )
            
            recent_crawls = len(
                self.client.table('crawling_logs').select('count').gte(
                    'crawled_at', datetime.now().replace(hour=0, minute=0, second=0).isoformat()
                ).execute().data
            )
            
            return {
                'restaurants_count': restaurants_count,
                'menus_count': menus_count,
                'menus_with_embedding': menus_with_embedding,
                'embedding_coverage': (menus_with_embedding / menus_count * 100) if menus_count > 0 else 0,
                'recent_crawls_today': recent_crawls
            }
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {}
    
    def cleanup_old_logs(self, days: int = 30) -> int:
        """오래된 크롤링 로그 정리"""
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            result = self.client.table('crawling_logs').delete().lt(
                'crawled_at', cutoff_date.isoformat()
            ).execute()
            
            deleted_count = len(result.data) if result.data else 0
            logger.info(f"오래된 로그 {deleted_count}개 정리 완료")
            return deleted_count
        except Exception as e:
            logger.error(f"로그 정리 실패: {e}")
            return 0
