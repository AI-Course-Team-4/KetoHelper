"""
Redis 캐시 관리 클래스
서버리스 환경에서도 작동하는 캐시 시스템
"""

import json
import redis
from typing import Any, Optional, Union
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis 캐시 관리 클래스"""
    
    def __init__(self):
        self.redis_client = None
        self.enabled = False
        
        # Redis 설정 확인 (배포 환경에서만 활성화)
        redis_url = getattr(settings, 'redis_url', None)
        is_production = settings.environment == "production"
        
        if redis_url and getattr(settings, 'redis_enabled', False) and is_production:
            try:
                # TLS 설정 확인
                use_ssl = redis_url.startswith("rediss://")
                
                # 연결 타임아웃 설정
                socket_timeout = 1 if settings.environment == "development" else 5
                
                self.redis_client = redis.from_url(
                    redis_url, 
                    decode_responses=True,
                    socket_timeout=socket_timeout,
                    socket_connect_timeout=socket_timeout,
                    ssl=use_ssl,  # TLS 설정 추가
                    ssl_cert_reqs=None,  # 인증서 검증 완화 (Upstash 호환)
                    health_check_interval=30,  # 연결 유지
                    retry_on_timeout=True
                )
                
                # 연결 테스트 (동기식이지만 초기화 시에만 사용)
                self.redis_client.ping()
                self.enabled = True
                logger.info(f"✅ Redis 캐시 연결 성공 (배포 환경, SSL: {use_ssl})")
            except Exception as e:
                logger.warning(f"❌ Redis 연결 실패, 메모리 캐시 사용: {e}")
                self.enabled = False
        else:
            if not is_production:
                logger.info("ℹ️ 로컬 환경 - 메모리 캐시 사용 (빠름)")
            else:
                logger.info("ℹ️ Redis 설정 없음, 메모리 캐시 사용")
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기"""
        if not self.enabled or not self.redis_client:
            return None
            
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis GET 오류: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """캐시에 값 저장하기"""
        if not self.enabled or not self.redis_client:
            return False
            
        try:
            serialized_value = json.dumps(value, ensure_ascii=False)
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.warning(f"Redis SET 오류: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """캐시에서 값 삭제하기"""
        if not self.enabled or not self.redis_client:
            return False
            
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis DELETE 오류: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """캐시 키 존재 여부 확인"""
        if not self.enabled or not self.redis_client:
            return False
            
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.warning(f"Redis EXISTS 오류: {e}")
            return False

# 전역 Redis 캐시 인스턴스
redis_cache = RedisCache()
