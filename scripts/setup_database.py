#!/usr/bin/env python3
"""
데이터베이스 설정 스크립트
"""

import asyncio
import sys
import logging
from pathlib import Path

# 프로젝트 루트를 Python 패스에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from infrastructure.database.connection import DatabasePool, DatabaseMigrator

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """메인 함수"""
    logger.info("데이터베이스 설정 시작")

    # 설정 검증
    errors = settings.validate()
    if errors:
        logger.error("설정 오류:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    # 데이터베이스 연결
    db_pool = DatabasePool(settings.database)

    try:
        logger.info("데이터베이스 연결 중...")
        await db_pool.initialize()

        # 연결 테스트
        health = await db_pool.health_check()
        if health["status"] == "healthy":
            logger.info(f"데이터베이스 연결 성공 (응답시간: {health['response_time_ms']}ms)")
        else:
            logger.error(f"데이터베이스 연결 실패: {health.get('error', 'Unknown error')}")
            return False

        # 마이그레이션 실행
        logger.info("데이터베이스 마이그레이션 실행 중...")
        migrator = DatabaseMigrator(db_pool)
        await migrator.run_migrations()

        # 최종 확인
        logger.info("데이터베이스 설정 확인 중...")
        result = await verify_database_setup(db_pool)

        if result:
            logger.info("✅ 데이터베이스 설정 완료!")
            logger.info(f"환경: {settings.environment}")
            logger.info(f"데이터베이스: {settings.database.host}:{settings.database.port}/{settings.database.database}")

            # 통계 출력
            await print_database_stats(db_pool)
        else:
            logger.error("❌ 데이터베이스 설정 실패")
            return False

    except Exception as e:
        logger.error(f"데이터베이스 설정 중 오류 발생: {e}")
        return False

    finally:
        await db_pool.close()

    return True

async def verify_database_setup(db_pool: DatabasePool) -> bool:
    """데이터베이스 설정 검증"""
    try:
        # 필수 테이블 존재 확인
        required_tables = [
            'restaurants',
            'restaurant_sources',
            'menus',
            'menu_ingredients',
            'keto_scores',
            'geocoding_cache',
            'crawl_jobs'
        ]

        for table in required_tables:
            exists = await db_pool.fetchval(
                "SELECT 1 FROM information_schema.tables WHERE table_name = $1",
                table
            )
            if not exists:
                logger.error(f"필수 테이블 누락: {table}")
                return False

        # 필수 확장 기능 확인
        required_extensions = ['uuid-ossp', 'pg_trgm', 'btree_gin']
        for ext in required_extensions:
            exists = await db_pool.fetchval(
                "SELECT 1 FROM pg_extension WHERE extname = $1",
                ext
            )
            if not exists:
                logger.warning(f"확장 기능 누락: {ext} (일부 기능이 제한될 수 있습니다)")

        logger.info("데이터베이스 구조 검증 완료")
        return True

    except Exception as e:
        logger.error(f"데이터베이스 검증 실패: {e}")
        return False

async def print_database_stats(db_pool: DatabasePool):
    """데이터베이스 통계 출력"""
    try:
        logger.info("=== 데이터베이스 통계 ===")

        # 테이블별 레코드 수
        tables = [
            'restaurants',
            'restaurant_sources',
            'menus',
            'menu_ingredients',
            'keto_scores',
            'geocoding_cache',
            'crawl_jobs'
        ]

        for table in tables:
            count = await db_pool.fetchval(f"SELECT COUNT(*) FROM {table}")
            logger.info(f"{table}: {count:,}개")

        # 연결 풀 상태
        pool_stats = db_pool.pool_stats
        logger.info(f"연결 풀 - 전체: {pool_stats['size']}, 사용중: {pool_stats['used']}, 유휴: {pool_stats['idle']}")

    except Exception as e:
        logger.warning(f"통계 출력 실패: {e}")

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)