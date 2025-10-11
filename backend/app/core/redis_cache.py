"""
Redis 캐시 관리 클래스
서버리스/컨테이너 환경에서도 안전하게 동작하도록 초기화/로깅 강화
"""

import json
import logging
from typing import Any, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis 캐시 관리 클래스"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.enabled: bool = False
        self.init_error: Optional[str] = None  # ⬅ 초기화 실패 원인 저장(상태 엔드포인트 노출용)

        # 설정값 읽기
        redis_url: str = (getattr(settings, "redis_url", "") or "").strip()
        is_production: bool = str(getattr(settings, "environment", "")).strip().lower() == "production"
        redis_enabled_flag: bool = bool(getattr(settings, "redis_enabled", False))
        force_enable: bool = str(getattr(settings, "redis_force_enable", "false")).lower() == "true"
        no_verify: bool = str(getattr(settings, "redis_ssl_no_verify", "false")).lower() == "true"

        logger.info(
            "🔎 Redis boot check | env=%r, prod=%r, redis_enabled=%r, url_set=%r, force=%r",
            getattr(settings, "environment", None),
            is_production,
            redis_enabled_flag,
            bool(redis_url),
            force_enable,
        )

        # 활성화 게이트: (URL 있고, 플래그 true이고, prod) 또는 강제활성
        if (redis_url and redis_enabled_flag and is_production) or force_enable:
            try:
                # 서버리스에서 너무 짧으면 불안정, 너무 길면 지연 → 5초 정도 권장
                socket_timeout = 5

                # redis-py는 rediss:// 스킴이면 내부적으로 TLS 적용
                client_kwargs = dict(
                    decode_responses=True,
                    socket_timeout=socket_timeout,
                    socket_connect_timeout=socket_timeout,
                    health_check_interval=30,
                    retry_on_timeout=True,
                )

                # 인증서 검증 이슈(Managed Redis/프록시 환경 등) 있을 때만 임시 완화
                if redis_url.startswith("rediss://") and no_verify:
                    client_kwargs["ssl"] = True
                    client_kwargs["ssl_cert_reqs"] = None  # 구버전 호환 목적

                self.redis_client = redis.from_url(redis_url, **client_kwargs)

                # 연결 확인 + 간단한 read/write 검증
                self.redis_client.ping()
                self.redis_client.setex("healthcheck", 30, "ok")
                assert self.redis_client.get("healthcheck") == "ok"

                self.enabled = True
                self.init_error = None
                logger.info(
                    "✅ Redis 연결 성공 (scheme=%s)",
                    "rediss" if redis_url.startswith("rediss://") else "redis",
                )

            except Exception as e:
                # 실패시 메모리 모드로 폴백
                self.redis_client = None
                self.enabled = False
                self.init_error = repr(e)
                logger.warning("❌ Redis 연결 실패 → 메모리 캐시 사용: %r", e)

        else:
            # 게이트에서 비활성화된 케이스(원인을 기록)
            reasons = []
            if not redis_url:
                reasons.append("no_url")
            if not redis_enabled_flag:
                reasons.append("flag_off")
            if not is_production and not force_enable:
                reasons.append("not_prod")
            self.enabled = False
            self.redis_client = None
            self.init_error = f"disabled_by_gate({','.join(reasons)})"
            logger.info("ℹ️ Redis 비활성: %s", self.init_error)

    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 가져오기 (JSON 역직렬화)"""
        if not self.enabled or not self.redis_client:
            return None
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.warning("Redis GET 오류: %r", e)
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """캐시에 값 저장 (JSON 직렬화)"""
        if not self.enabled or not self.redis_client:
            return False
        try:
            serialized_value = json.dumps(value, ensure_ascii=False)
            self.redis_client.setex(key, ttl, serialized_value)
            return True
        except Exception as e:
            logger.warning("Redis SET 오류: %r", e)
            return False

    def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        if not self.enabled or not self.redis_client:
            return False
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning("Redis DELETE 오류: %r", e)
            return False

    def exists(self, key: str) -> bool:
        """키 존재 여부"""
        if not self.enabled or not self.redis_client:
            return False
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.warning("Redis EXISTS 오류: %r", e)
            return False


# 전역 단일 인스턴스 — 상태 엔드포인트 등에서 반드시 이걸 참조
redis_cache = RedisCache()
