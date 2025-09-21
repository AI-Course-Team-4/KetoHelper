"""
데이터베이스 연결 관리 (슈퍼베이스 사용)
"""

import asyncio
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
import logging
from config.settings import settings
from infrastructure.database.supabase_connection import SupabaseConnection

logger = logging.getLogger(__name__)

class DatabasePool:
    """데이터베이스 연결 풀 관리자 (슈퍼베이스 사용)"""

    def __init__(self):
        self.supabase = SupabaseConnection()
        self._is_initialized = False

    async def initialize(self):
        """연결 풀 초기화"""
        if self._is_initialized:
            return

        try:
            logger.info("Initializing Supabase connection")

            await self.supabase.initialize()
            self._is_initialized = True
            logger.info("Supabase connection initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Supabase connection: {e}")
            raise

    async def close(self):
        """연결 풀 종료"""
        await self.supabase.close()
        self._is_initialized = False
        logger.info("Supabase connection closed")

    async def execute_query(self, table: str, operation: str, **kwargs) -> Any:
        """쿼리 실행"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.execute_query(table, operation, **kwargs)

    async def insert_restaurant(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """식당 데이터 삽입"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.insert_restaurant(restaurant_data)

    async def insert_menu(self, menu_data: Dict[str, Any]) -> Dict[str, Any]:
        """메뉴 데이터 삽입"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.insert_menu(menu_data)

    async def insert_keto_score(self, score_data: Dict[str, Any]) -> Dict[str, Any]:
        """키토 점수 데이터 삽입"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.insert_keto_score(score_data)

    async def get_restaurant_by_source_url(self, source: str, source_url: str) -> Optional[Dict[str, Any]]:
        """소스 URL로 식당 조회"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.get_restaurant_by_source_url(source, source_url)

    async def get_menus_by_restaurant_id(self, restaurant_id: str) -> List[Dict[str, Any]]:
        """식당 ID로 메뉴 목록 조회"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.get_menus_by_restaurant_id(restaurant_id)

    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.health_check()

    # 데이터 삽입 메서드들
    async def insert_restaurant(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """식당 데이터 삽입"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.insert_restaurant(restaurant_data)

    async def insert_menu(self, menu_data: Dict[str, Any]) -> Dict[str, Any]:
        """메뉴 데이터 삽입"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.insert_menu(menu_data)

    async def insert_keto_score(self, keto_score_data: Dict[str, Any]) -> Dict[str, Any]:
        """키토 점수 데이터 삽입"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.insert_keto_score(keto_score_data)

    async def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Dict[str, Any]]:
        """식당 ID로 조회"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.get_restaurant_by_id(restaurant_id)

    async def get_menu_by_id(self, menu_id: str) -> Optional[Dict[str, Any]]:
        """메뉴 ID로 조회"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.get_menu_by_id(menu_id)

    async def get_keto_score_by_id(self, keto_score_id: str) -> Optional[Dict[str, Any]]:
        """키토 점수 ID로 조회"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.get_keto_score_by_id(keto_score_id)

    async def get_restaurants(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """식당 목록 조회"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.get_restaurants(limit, offset)

    async def get_menus(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """메뉴 목록 조회"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.get_menus(limit, offset)

    async def count_restaurants(self) -> int:
        """식당 수 조회"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.count_restaurants()

    async def count_menus(self) -> int:
        """메뉴 수 조회"""
        if not self._is_initialized:
            await self.initialize()
        
        return await self.supabase.count_menus()

    @property
    def is_initialized(self) -> bool:
        """초기화 상태"""
        return self._is_initialized

class DatabaseMigrator:
    """데이터베이스 마이그레이션 관리 (슈퍼베이스는 스키마가 이미 존재)"""

    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool

    async def run_migrations(self, migrations_dir: str = "infrastructure/database/migrations"):
        """마이그레이션 실행 (슈퍼베이스는 스키마가 이미 존재하므로 스킵)"""
        logger.info("Supabase database schema already exists, skipping migrations")
        return

    async def check_schema_compatibility(self) -> bool:
        """스키마 호환성 확인"""
        try:
            # 기본 테이블들이 존재하는지 확인
            tables_to_check = ['restaurant', 'menu', 'keto_scores', 'ingredient']
            
            for table in tables_to_check:
                result = await self.db_pool.execute_query(table, 'select', columns='id', limit=1)
                if not result.data:
                    logger.warning(f"Table {table} exists but is empty")
            
            logger.info("Schema compatibility check passed")
            return True
            
        except Exception as e:
            logger.error(f"Schema compatibility check failed: {e}")
            return False

# 글로벌 데이터베이스 풀 인스턴스
db_pool = DatabasePool()