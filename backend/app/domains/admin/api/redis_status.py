"""
Redis 연결 상태 확인 엔드포인트
배포 후 Redis 설정/연결이 제대로 되었는지 점검
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.core.redis_cache import redis_cache

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/redis-status")
async def check_redis_status():
    """Redis 연결 상태/간단 read-write 테스트 결과를 반환"""
    try:
        redis_url = getattr(settings, "redis_url", None)
        redis_enabled = bool(getattr(settings, "redis_enabled", False))
        environment = getattr(settings, "environment", None)

        status = {
            "environment": environment,
            "redis_enabled": redis_enabled,
            "redis_url_configured": bool(redis_url),
            "redis_client_enabled": bool(redis_cache.enabled),
            "redis_client_connected": False,
            "test_result": None,
            "error": None,
            "init_error": redis_cache.init_error,  # ⬅ 초기화 실패 원인을 그대로 노출
        }

        # 실제 연결/테스트
        if redis_cache.enabled and redis_cache.redis_client:
            try:
                # 연결 확인
                status["redis_client_connected"] = bool(redis_cache.redis_client.ping())

                # read/write 검증
                test_key = "redis_status_test_key"
                test_value = {
                    "ok": True,
                    "ts": datetime.now(timezone.utc).isoformat(),
                }

                saved = redis_cache.set(test_key, test_value, ttl=60)
                if not saved:
                    status["test_result"] = "SAVE_FAILED"
                else:
                    got = redis_cache.get(test_key)
                    if got == test_value:
                        status["test_result"] = "SUCCESS"
                    else:
                        status["test_result"] = "RETRIEVAL_FAILED"
                    # 정리
                    redis_cache.delete(test_key)

            except Exception as e:
                status["error"] = repr(e)
                status["test_result"] = "CONNECTION_FAILED"
        else:
            # 비활성화 사유 표면화
            if not status["init_error"]:
                status["error"] = "Redis client not initialized (disabled)"
            else:
                status["error"] = status["init_error"]

        return status

    except Exception as e:
        logger.error("Redis 상태 확인 오류: %r", e)
        raise HTTPException(status_code=500, detail=f"Redis 상태 확인 실패: {e!r}")
