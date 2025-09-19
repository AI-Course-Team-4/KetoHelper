"""
데이터베이스 연결 관리
"""

import asyncio
import asyncpg
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import logging
from config.settings import DatabaseConfig, settings

logger = logging.getLogger(__name__)

class DatabasePool:
    """데이터베이스 연결 풀 관리자"""

    def __init__(self, config: DatabaseConfig = None):
        self.config = config or settings.database
        self._pool: Optional[asyncpg.Pool] = None
        self._is_initialized = False

    async def initialize(self):
        """연결 풀 초기화"""
        if self._is_initialized:
            return

        try:
            logger.info(f"Initializing database connection pool to {self.config.host}:{self.config.port}")

            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                min_size=1,
                max_size=self.config.pool_size,
                max_inactive_connection_lifetime=300,  # 5분
                command_timeout=self.config.timeout
            )

            # 연결 테스트
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            self._is_initialized = True
            logger.info("Database connection pool initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close(self):
        """연결 풀 종료"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._is_initialized = False
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def acquire(self):
        """연결 획득 컨텍스트 매니저"""
        if not self._is_initialized:
            await self.initialize()

        connection = await self._pool.acquire()
        try:
            yield connection
        finally:
            await self._pool.release(connection)

    @asynccontextmanager
    async def transaction(self):
        """트랜잭션 컨텍스트 매니저"""
        async with self.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def execute(self, query: str, *args) -> str:
        """쿼리 실행"""
        async with self.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> list:
        """다중 레코드 조회"""
        async with self.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """단일 레코드 조회"""
        async with self.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """단일 값 조회"""
        async with self.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        try:
            start_time = asyncio.get_event_loop().time()
            async with self.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                response_time = asyncio.get_event_loop().time() - start_time

            return {
                "status": "healthy",
                "response_time_ms": round(response_time * 1000, 2),
                "pool_size": self._pool.get_size() if self._pool else 0,
                "pool_idle": self._pool.get_idle_size() if self._pool else 0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    @property
    def is_initialized(self) -> bool:
        """초기화 상태"""
        return self._is_initialized

    @property
    def pool_stats(self) -> Dict[str, int]:
        """풀 통계"""
        if not self._pool:
            return {"size": 0, "idle": 0, "used": 0}

        return {
            "size": self._pool.get_size(),
            "idle": self._pool.get_idle_size(),
            "used": self._pool.get_size() - self._pool.get_idle_size()
        }

class DatabaseMigrator:
    """데이터베이스 마이그레이션 관리"""

    def __init__(self, db_pool: DatabasePool):
        self.db_pool = db_pool

    async def run_migrations(self, migrations_dir: str = "infrastructure/database/migrations"):
        """마이그레이션 실행"""
        import os
        from pathlib import Path

        migrations_path = Path(migrations_dir)
        if not migrations_path.exists():
            logger.warning(f"Migrations directory not found: {migrations_path}")
            return

        # 마이그레이션 테이블 생성
        await self._ensure_migration_table()

        # 마이그레이션 파일들 정렬
        migration_files = sorted([
            f for f in os.listdir(migrations_path)
            if f.endswith('.sql')
        ])

        for migration_file in migration_files:
            await self._run_migration(migrations_path / migration_file)

    async def _ensure_migration_table(self):
        """마이그레이션 추적 테이블 생성"""
        query = """
        CREATE TABLE IF NOT EXISTS __migrations (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) UNIQUE NOT NULL,
            executed_at TIMESTAMPTZ DEFAULT NOW()
        )
        """
        await self.db_pool.execute(query)

    async def _run_migration(self, migration_path: Path):
        """개별 마이그레이션 실행"""
        filename = migration_path.name

        # 이미 실행된 마이그레이션인지 확인
        executed = await self.db_pool.fetchval(
            "SELECT 1 FROM __migrations WHERE filename = $1",
            filename
        )

        if executed:
            logger.info(f"Migration {filename} already executed, skipping")
            return

        logger.info(f"Running migration: {filename}")

        try:
            # 마이그레이션 파일 읽기
            with open(migration_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()

            # 트랜잭션으로 실행
            async with self.db_pool.transaction() as conn:
                await conn.execute(sql_content)
                await conn.execute(
                    "INSERT INTO __migrations (filename) VALUES ($1)",
                    filename
                )

            logger.info(f"Migration {filename} completed successfully")

        except Exception as e:
            logger.error(f"Migration {filename} failed: {e}")
            raise

# 글로벌 데이터베이스 풀 인스턴스
db_pool = DatabasePool()