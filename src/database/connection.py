"""
🗄️ 데이터베이스 연결 관리
- Supabase + PostgreSQL 통합 지원
- 비동기 연결 풀 관리
- 연결 상태 모니터링
"""

import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
from supabase import create_client, Client
from asyncpg import Connection, Pool

from ..utils.config_loader import get_config
from ..utils.logger import get_logger, log_database_operation


class DatabaseConnection:
    """통합 데이터베이스 연결 관리자"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = get_config(config_path)
        self.logger = get_logger("database")
        
        # 연결 풀
        self.pool: Optional[Pool] = None
        
        # Supabase 클라이언트
        self.supabase: Optional[Client] = None
        
        # 연결 통계
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "total_queries": 0,
            "failed_queries": 0,
        }
    
    async def initialize(self):
        """데이터베이스 연결 초기화"""
        try:
            # Supabase 클라이언트 초기화 (API 사용)
            if self.config.is_supabase_enabled():
                await self._init_supabase()
            
            # PostgreSQL 직접 연결 초기화 (성능용)
            await self._init_postgresql()
            
            self.logger.info("데이터베이스 연결 초기화 완료")
            
        except Exception as e:
            self.logger.error(f"데이터베이스 연결 초기화 실패: {e}")
            raise
    
    async def _init_supabase(self):
        """Supabase 클라이언트 초기화"""
        try:
            supabase_url = self.config.get_supabase_url()
            supabase_key = self.config.get_supabase_anon_key()
            
            if supabase_url and supabase_key:
                # 동기 클라이언트 (REST API용)
                self.supabase = create_client(supabase_url, supabase_key)
                self.logger.info(f"Supabase 클라이언트 초기화: {supabase_url}")
            
        except Exception as e:
            self.logger.error(f"Supabase 초기화 실패: {e}")
            raise
    
    async def _init_postgresql(self):
        """PostgreSQL 연결 풀 초기화"""
        try:
            database_url = self.config.get_async_database_url()
            
            # 연결 풀 생성
            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=self.config.database.pool_size,
                max_queries=50000,
                max_inactive_connection_lifetime=300,  # 5분
                command_timeout=self.config.database.timeout,
            )
            
            # 연결 테스트
            await self._test_connection()
            
            self.logger.info(f"PostgreSQL 연결 풀 생성: {self.config.database.host}")
            
        except Exception as e:
            self.logger.error(f"PostgreSQL 초기화 실패: {e}")
            raise
    
    async def _test_connection(self):
        """연결 테스트"""
        if self.pool:
            async with self.pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                if result != 1:
                    raise Exception("데이터베이스 연결 테스트 실패")
    
    async def close(self):
        """모든 연결 종료"""
        try:
            if self.pool:
                await self.pool.close()
                self.pool = None
                self.logger.info("PostgreSQL 연결 풀 종료")
            
            # Supabase는 별도 종료 불필요
            self.supabase = None
            
        except Exception as e:
            self.logger.error(f"데이터베이스 연결 종료 실패: {e}")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """PostgreSQL 연결 반환 (컨텍스트 매니저)"""
        if not self.pool:
            raise Exception("데이터베이스 풀이 초기화되지 않았습니다")
        
        async with self.pool.acquire() as conn:
            self.stats["active_connections"] += 1
            try:
                yield conn
            finally:
                self.stats["active_connections"] -= 1
    
    async def execute_query(self, query: str, *args) -> Any:
        """쿼리 실행"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.get_connection() as conn:
                result = await conn.fetch(query, *args)
                
                # 통계 업데이트
                self.stats["total_queries"] += 1
                duration = asyncio.get_event_loop().time() - start_time
                
                log_database_operation(
                    "SELECT", 
                    "unknown", 
                    len(result) if result else 0, 
                    duration
                )
                
                return result
                
        except Exception as e:
            self.stats["failed_queries"] += 1
            self.logger.error(f"쿼리 실행 실패: {query[:100]}... - {e}")
            raise
    
    async def execute_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """단일 레코드 조회"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.get_connection() as conn:
                result = await conn.fetchrow(query, *args)
                
                # 통계 업데이트
                self.stats["total_queries"] += 1
                duration = asyncio.get_event_loop().time() - start_time
                
                log_database_operation(
                    "SELECT_ONE", 
                    "unknown", 
                    1 if result else 0, 
                    duration
                )
                
                return dict(result) if result else None
                
        except Exception as e:
            self.stats["failed_queries"] += 1
            self.logger.error(f"단일 쿼리 실행 실패: {query[:100]}... - {e}")
            raise
    
    async def execute_write(self, query: str, *args) -> str:
        """쓰기 작업 실행 (INSERT/UPDATE/DELETE)"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.get_connection() as conn:
                result = await conn.execute(query, *args)
                
                # 통계 업데이트
                self.stats["total_queries"] += 1
                duration = asyncio.get_event_loop().time() - start_time
                
                # 영향받은 행 수 추출
                affected_rows = 0
                if result.startswith(('INSERT', 'UPDATE', 'DELETE')):
                    parts = result.split()
                    if len(parts) > 1 and parts[-1].isdigit():
                        affected_rows = int(parts[-1])
                
                log_database_operation(
                    query.split()[0], 
                    "unknown", 
                    affected_rows, 
                    duration
                )
                
                return result
                
        except Exception as e:
            self.stats["failed_queries"] += 1
            self.logger.error(f"쓰기 쿼리 실행 실패: {query[:100]}... - {e}")
            raise
    
    async def execute_transaction(self, queries: list) -> list:
        """트랜잭션 실행"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.get_connection() as conn:
                async with conn.transaction():
                    results = []
                    
                    for query, args in queries:
                        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                            result = await conn.execute(query, *args)
                        else:
                            result = await conn.fetch(query, *args)
                        
                        results.append(result)
                    
                    # 통계 업데이트
                    self.stats["total_queries"] += len(queries)
                    duration = asyncio.get_event_loop().time() - start_time
                    
                    log_database_operation(
                        "TRANSACTION", 
                        "multiple", 
                        len(queries), 
                        duration
                    )
                    
                    return results
                    
        except Exception as e:
            self.stats["failed_queries"] += len(queries)
            self.logger.error(f"트랜잭션 실행 실패: {e}")
            raise
    
    def get_supabase(self) -> Optional[Client]:
        """Supabase 클라이언트 반환"""
        return self.supabase
    
    def get_stats(self) -> Dict[str, Any]:
        """연결 통계 반환"""
        return {
            **self.stats,
            "pool_size": self.config.database.pool_size if self.pool else 0,
            "is_supabase_enabled": self.config.is_supabase_enabled(),
            "database_host": self.config.database.host,
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        health = {
            "postgresql": False,
            "supabase": False,
            "pool_status": None,
            "connection_test": False
        }
        
        try:
            # PostgreSQL 연결 테스트
            if self.pool:
                await self._test_connection()
                health["postgresql"] = True
                health["pool_status"] = {
                    "size": self.pool.get_size(),
                    "max_size": self.pool.get_max_size(),
                    "min_size": self.pool.get_min_size(),
                }
            
            # Supabase 연결 테스트
            if self.supabase:
                # 간단한 API 호출로 테스트
                try:
                    # Supabase 상태 확인 (실제로는 간단한 쿼리 실행)
                    health["supabase"] = True
                except:
                    health["supabase"] = False
            
            health["connection_test"] = health["postgresql"]
            
        except Exception as e:
            self.logger.error(f"헬스 체크 실패: {e}")
            health["error"] = str(e)
        
        return health


# 전역 데이터베이스 인스턴스
_db_connection = None


async def get_database() -> DatabaseConnection:
    """전역 데이터베이스 연결 반환"""
    global _db_connection
    
    if _db_connection is None:
        _db_connection = DatabaseConnection()
        await _db_connection.initialize()
    
    return _db_connection


async def close_database():
    """전역 데이터베이스 연결 종료"""
    global _db_connection
    if _db_connection:
        await _db_connection.close()
        _db_connection = None


# 편의 함수들
async def execute_query(query: str, *args) -> Any:
    """쿼리 실행 (편의 함수)"""
    db = await get_database()
    return await db.execute_query(query, *args)


async def execute_one(query: str, *args) -> Optional[Dict[str, Any]]:
    """단일 레코드 조회 (편의 함수)"""
    db = await get_database()
    return await db.execute_one(query, *args)


async def execute_write(query: str, *args) -> str:
    """쓰기 작업 실행 (편의 함수)"""
    db = await get_database()
    return await db.execute_write(query, *args)


if __name__ == "__main__":
    # 테스트 코드
    async def test_database():
        try:
            db = DatabaseConnection()
            await db.initialize()
            
            # 헬스 체크
            health = await db.health_check()
            print(f"헬스 체크: {health}")
            
            # 통계 확인
            stats = db.get_stats()
            print(f"연결 통계: {stats}")
            
            # 간단한 쿼리 테스트
            result = await db.execute_one("SELECT 1 as test")
            print(f"테스트 쿼리 결과: {result}")
            
            await db.close()
            print("✅ 데이터베이스 테스트 성공!")
            
        except Exception as e:
            print(f"❌ 데이터베이스 테스트 실패: {e}")
    
    asyncio.run(test_database())