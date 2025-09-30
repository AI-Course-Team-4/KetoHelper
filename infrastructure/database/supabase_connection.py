"""
슈퍼베이스 데이터베이스 연결 관리
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from supabase import create_client, Client
from config.settings import settings

logger = logging.getLogger(__name__)

class SupabaseConnection:
    """슈퍼베이스 연결 관리자"""

    def __init__(self, config: Optional[Dict[str, str]] = None):
        self.config = config or {
            'url': settings.supabase.url,
            'key': settings.supabase.anon_key
        }
        self._client: Optional[Client] = None
        self._is_initialized = False

    async def initialize(self):
        """연결 초기화"""
        if self._is_initialized:
            return

        try:
            logger.info(f"Initializing Supabase connection to {self.config['url']}")

            self._client = create_client(
                self.config['url'],
                self.config['key']
            )

            # 연결 테스트
            await self._test_connection()

            self._is_initialized = True
            logger.info("Supabase connection initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Supabase connection: {e}")
            raise

    async def _test_connection(self):
        """연결 테스트 (타임아웃 발생 시 경고만 남기고 진행)"""
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            try:
                _ = self._client.table('restaurant').select('id').limit(1).execute()
                logger.debug("Supabase connection test successful")
                return
            except Exception as e:
                logger.warning(f"Supabase connection test attempt {attempt}/{max_attempts} failed: {e}")
                if attempt < max_attempts:
                    time.sleep(1.0)
                else:
                    # 마지막 시도 실패: 경고 로그만 남기고 계속 진행
                    logger.warning("Proceeding without successful connection test due to timeout/error.")
                    return

    async def close(self):
        """연결 종료"""
        self._client = None
        self._is_initialized = False
        logger.info("Supabase connection closed")

    # 데이터 삽입 메서드들
    async def insert_restaurant(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """식당 데이터 삽입"""
        try:
            result = self._client.table('restaurant').insert(restaurant_data).execute()
            logger.debug(f"Restaurant inserted: {restaurant_data.get('name')}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to insert restaurant: {e}")
            raise

    async def insert_menu(self, menu_data: Dict[str, Any]) -> Dict[str, Any]:
        """메뉴 데이터 삽입"""
        try:
            result = self._client.table('menu').insert(menu_data).execute()
            logger.debug(f"Menu inserted: {menu_data.get('name')}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to insert menu: {e}")
            raise

    async def insert_keto_score(self, keto_score_data: Dict[str, Any]) -> Dict[str, Any]:
        """키토 점수 데이터 삽입"""
        try:
            result = self._client.table('keto_scores').insert(keto_score_data).execute()
            logger.debug(f"Keto score inserted: {keto_score_data.get('score')}")
            return result.data[0] if result.data else {}
        except Exception as e:
            logger.error(f"Failed to insert keto score: {e}")
            raise

    async def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Dict[str, Any]]:
        """식당 ID로 조회"""
        try:
            result = self._client.table('restaurant').select('*').eq('id', restaurant_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get restaurant by ID: {e}")
            return None

    async def get_menu_by_id(self, menu_id: str) -> Optional[Dict[str, Any]]:
        """메뉴 ID로 조회"""
        try:
            result = self._client.table('menu').select('*').eq('id', menu_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get menu by ID: {e}")
            return None

    async def get_keto_score_by_id(self, keto_score_id: str) -> Optional[Dict[str, Any]]:
        """키토 점수 ID로 조회"""
        try:
            result = self._client.table('keto_scores').select('*').eq('id', keto_score_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get keto score by ID: {e}")
            return None

    async def get_restaurants(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """식당 목록 조회"""
        try:
            result = self._client.table('restaurant').select('*').range(offset, offset + limit - 1).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get restaurants: {e}")
            return []

    async def get_menus(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """메뉴 목록 조회"""
        try:
            result = self._client.table('menu').select('*').range(offset, offset + limit - 1).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get menus: {e}")
            return []

    async def count_restaurants(self) -> int:
        """식당 수 조회"""
        try:
            result = self._client.table('restaurant').select('id', count='exact').execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Failed to count restaurants: {e}")
            return 0

    async def count_menus(self) -> int:
        """메뉴 수 조회"""
        try:
            result = self._client.table('menu').select('id', count='exact').execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Failed to count menus: {e}")
            return 0

    @property
    def client(self) -> Client:
        """슈퍼베이스 클라이언트 반환"""
        if not self._is_initialized:
            raise RuntimeError("Supabase connection not initialized")
        return self._client

    async def execute_query(self, table: str, operation: str, **kwargs) -> Any:
        """쿼리 실행"""
        if not self._is_initialized:
            await self.initialize()

        try:
            query = self.client.table(table)
            
            if operation == 'select':
                return query.select(kwargs.get('columns', '*')).execute()
            elif operation == 'insert':
                return query.insert(kwargs['data']).execute()
            elif operation == 'update':
                return query.update(kwargs['data']).eq(kwargs['column'], kwargs['value']).execute()
            elif operation == 'delete':
                return query.delete().eq(kwargs['column'], kwargs['value']).execute()
            else:
                raise ValueError(f"Unsupported operation: {operation}")

        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

    async def insert_restaurant(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """식당 데이터 삽입"""
        try:
            result = self.client.table('restaurant').insert(restaurant_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to insert restaurant: {e}")
            raise

    async def insert_menu(self, menu_data: Dict[str, Any]) -> Dict[str, Any]:
        """메뉴 데이터 삽입"""
        try:
            result = self.client.table('menu').insert(menu_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to insert menu: {e}")
            raise

    async def insert_keto_score(self, score_data: Dict[str, Any]) -> Dict[str, Any]:
        """키토 점수 데이터 삽입"""
        try:
            result = self.client.table('keto_scores').insert(score_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to insert keto score: {e}")
            raise

    async def get_restaurant_by_source_url(self, source: str, source_url: str) -> Optional[Dict[str, Any]]:
        """소스 URL로 식당 조회"""
        try:
            result = self.client.table('restaurant').select('*').eq('source', source).eq('source_url', source_url).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Failed to get restaurant by source URL: {e}")
            return None

    async def get_menus_by_restaurant_id(self, restaurant_id: str) -> List[Dict[str, Any]]:
        """식당 ID로 메뉴 목록 조회"""
        try:
            result = self.client.table('menu').select('*').eq('restaurant_id', restaurant_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get menus by restaurant ID: {e}")
            return []

    async def get_keto_scores_by_menu_id(self, menu_id: str) -> List[Dict[str, Any]]:
        """메뉴 ID로 키토 점수 조회"""
        try:
            result = self.client.table('keto_scores').select('*').eq('menu_id', menu_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Failed to get keto scores by menu ID: {e}")
            return []

    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        try:
            start_time = asyncio.get_event_loop().time()
            await self._test_connection()
            response_time = asyncio.get_event_loop().time() - start_time

            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "connection_type": "supabase"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "connection_type": "supabase"
            }

    async def get_table_count(self, table_name: str) -> int:
        """테이블 레코드 수 조회"""
        try:
            result = self.client.table(table_name).select('id', count='exact').execute()
            return result.count or 0
        except Exception as e:
            logger.error(f"Failed to get count for table {table_name}: {e}")
            return 0

    async def clear_table(self, table_name: str) -> bool:
        """테이블의 모든 데이터 삭제"""
        try:
            result = self.client.table(table_name).delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            logger.info(f"Cleared table {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear table {table_name}: {e}")
            return False

    @property
    def is_initialized(self) -> bool:
        """초기화 상태"""
        return self._is_initialized

# 글로벌 슈퍼베이스 연결 인스턴스
supabase_connection = SupabaseConnection()
