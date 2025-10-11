"""
Redis 연결 상태 확인 엔드포인트
배포 후 Redis 설정이 제대로 되어있는지 확인하는 용도
"""

from fastapi import APIRouter, HTTPException
from app.core.redis_cache import redis_cache
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/redis-status")
async def check_redis_status():
    """Redis 연결 상태 확인"""
    try:
        # 환경 변수 확인
        redis_url = getattr(settings, 'redis_url', None)
        redis_enabled = getattr(settings, 'redis_enabled', False)
        environment = settings.environment
        
        status = {
            "environment": environment,
            "redis_enabled": redis_enabled,
            "redis_url_configured": bool(redis_url),
            "redis_client_enabled": redis_cache.enabled,
            "redis_client_connected": False,
            "test_result": None,
            "error": None
        }
        
        # Redis 클라이언트 연결 상태 확인
        if redis_cache.enabled and redis_cache.redis_client:
            try:
                # 연결 테스트
                redis_cache.redis_client.ping()
                status["redis_client_connected"] = True
                
                # 테스트 데이터 저장/조회
                test_key = "redis_test_key"
                test_value = {"test": "data", "timestamp": "2024-01-01"}
                
                # 저장 테스트
                save_success = redis_cache.set(test_key, test_value, ttl=60)
                if save_success:
                    # 조회 테스트
                    retrieved_value = redis_cache.get(test_key)
                    if retrieved_value == test_value:
                        status["test_result"] = "SUCCESS"
                        # 테스트 데이터 삭제
                        redis_cache.delete(test_key)
                    else:
                        status["test_result"] = "RETRIEVAL_FAILED"
                else:
                    status["test_result"] = "SAVE_FAILED"
                    
            except Exception as e:
                status["error"] = str(e)
                status["test_result"] = "CONNECTION_FAILED"
        
        return status
        
    except Exception as e:
        logger.error(f"Redis 상태 확인 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Redis 상태 확인 실패: {str(e)}")
