"""
Rate Limiter 및 서킷 브레이커 구현
"""

import asyncio
import time
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """서킷 브레이커 상태"""
    CLOSED = "closed"        # 정상 상태
    OPEN = "open"           # 차단 상태
    HALF_OPEN = "half_open" # 반개방 상태

@dataclass
class RateLimitConfig:
    """Rate Limiter 설정"""
    requests_per_second: float = 0.5  # 초당 요청 수
    burst_size: int = 1               # 버스트 크기
    max_tokens: int = 10              # 최대 토큰 수

@dataclass
class CircuitBreakerConfig:
    """서킷 브레이커 설정"""
    failure_threshold: int = 5        # 실패 임계값
    timeout_seconds: int = 900        # 타임아웃 (15분)
    success_threshold: int = 3        # 반개방시 성공 임계값
    failure_rate_threshold: float = 0.5  # 실패율 임계값

@dataclass
class CircuitBreakerStats:
    """서킷 브레이커 통계"""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    total_requests: int = 0
    total_failures: int = 0

class TokenBucket:
    """토큰 버킷 알고리즘 구현"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.max_tokens
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> bool:
        """토큰 획득 시도"""
        async with self._lock:
            now = time.time()

            # 토큰 보충
            time_passed = now - self.last_update
            new_tokens = time_passed * self.config.requests_per_second
            self.tokens = min(self.config.max_tokens, self.tokens + new_tokens)
            self.last_update = now

            # 토큰 소비
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def wait_for_token(self, tokens: int = 1) -> None:
        """토큰 획득까지 대기"""
        while not await self.acquire(tokens):
            wait_time = tokens / self.config.requests_per_second
            await asyncio.sleep(wait_time)

class CircuitBreaker:
    """서킷 브레이커 구현"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """서킷 브레이커를 통한 함수 호출"""
        async with self._lock:
            if not self._can_execute():
                raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e

    def _can_execute(self) -> bool:
        """실행 가능 여부 확인"""
        now = time.time()

        if self.stats.state == CircuitState.CLOSED:
            return True
        elif self.stats.state == CircuitState.OPEN:
            # 타임아웃 시간이 지났으면 반개방 상태로 전환
            if now - self.stats.last_state_change >= self.config.timeout_seconds:
                self._transition_to_half_open()
                return True
            return False
        elif self.stats.state == CircuitState.HALF_OPEN:
            return True

        return False

    async def _on_success(self):
        """성공 처리"""
        async with self._lock:
            self.stats.total_requests += 1

            if self.stats.state == CircuitState.HALF_OPEN:
                self.stats.success_count += 1
                if self.stats.success_count >= self.config.success_threshold:
                    self._transition_to_closed()
            elif self.stats.state == CircuitState.CLOSED:
                # 성공시 실패 카운트 리셋
                self.stats.failure_count = 0

    async def _on_failure(self):
        """실패 처리"""
        async with self._lock:
            self.stats.total_requests += 1
            self.stats.total_failures += 1
            self.stats.failure_count += 1
            self.stats.last_failure_time = time.time()

            if self.stats.state == CircuitState.CLOSED:
                if self.stats.failure_count >= self.config.failure_threshold:
                    self._transition_to_open()
            elif self.stats.state == CircuitState.HALF_OPEN:
                self._transition_to_open()

    def _transition_to_open(self):
        """OPEN 상태로 전환"""
        logger.warning(f"Circuit breaker opening - failure count: {self.stats.failure_count}")
        self.stats.state = CircuitState.OPEN
        self.stats.last_state_change = time.time()
        self.stats.success_count = 0

    def _transition_to_half_open(self):
        """HALF_OPEN 상태로 전환"""
        logger.info("Circuit breaker transitioning to half-open")
        self.stats.state = CircuitState.HALF_OPEN
        self.stats.last_state_change = time.time()
        self.stats.success_count = 0
        self.stats.failure_count = 0

    def _transition_to_closed(self):
        """CLOSED 상태로 전환"""
        logger.info("Circuit breaker closing - service recovered")
        self.stats.state = CircuitState.CLOSED
        self.stats.last_state_change = time.time()
        self.stats.failure_count = 0
        self.stats.success_count = 0

    @property
    def failure_rate(self) -> float:
        """실패율 계산"""
        if self.stats.total_requests == 0:
            return 0.0
        return self.stats.total_failures / self.stats.total_requests

    def get_stats(self) -> CircuitBreakerStats:
        """통계 반환"""
        return self.stats

class RateLimiter:
    """Rate Limiter 메인 클래스"""

    def __init__(
        self,
        rate_config: RateLimitConfig = None,
        circuit_config: CircuitBreakerConfig = None
    ):
        self.rate_config = rate_config or RateLimitConfig()
        self.circuit_config = circuit_config or CircuitBreakerConfig()

        self.token_bucket = TokenBucket(self.rate_config)
        self.circuit_breaker = CircuitBreaker(self.circuit_config)

        # 통계
        self.total_requests = 0
        self.rate_limited_requests = 0
        self.circuit_opened_requests = 0

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Rate Limiting과 Circuit Breaking을 적용한 함수 실행"""
        self.total_requests += 1

        # Rate Limiting 확인
        if not await self.token_bucket.acquire():
            self.rate_limited_requests += 1
            raise RateLimitExceededError("Rate limit exceeded")

        # Circuit Breaker를 통한 실행
        try:
            return await self.circuit_breaker.call(func, *args, **kwargs)
        except CircuitBreakerOpenError:
            self.circuit_opened_requests += 1
            raise

    async def wait_and_execute(self, func: Callable, *args, **kwargs) -> Any:
        """Rate Limit에 걸리면 대기 후 실행"""
        self.total_requests += 1

        # 토큰 획득까지 대기
        await self.token_bucket.wait_for_token()

        # Circuit Breaker를 통한 실행
        try:
            return await self.circuit_breaker.call(func, *args, **kwargs)
        except CircuitBreakerOpenError:
            self.circuit_opened_requests += 1
            raise

    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        circuit_stats = self.circuit_breaker.get_stats()

        return {
            "rate_limiter": {
                "total_requests": self.total_requests,
                "rate_limited_requests": self.rate_limited_requests,
                "current_tokens": self.token_bucket.tokens,
                "max_tokens": self.rate_config.max_tokens,
                "requests_per_second": self.rate_config.requests_per_second
            },
            "circuit_breaker": {
                "state": circuit_stats.state.value,
                "total_requests": circuit_stats.total_requests,
                "total_failures": circuit_stats.total_failures,
                "failure_count": circuit_stats.failure_count,
                "success_count": circuit_stats.success_count,
                "failure_rate": self.circuit_breaker.failure_rate,
                "circuit_opened_requests": self.circuit_opened_requests
            }
        }

    def reset(self):
        """통계 리셋"""
        self.total_requests = 0
        self.rate_limited_requests = 0
        self.circuit_opened_requests = 0
        self.circuit_breaker.stats = CircuitBreakerStats()

class RateLimitExceededError(Exception):
    """Rate Limit 초과 예외"""
    pass

class CircuitBreakerOpenError(Exception):
    """서킷 브레이커 OPEN 상태 예외"""
    pass

# 편의 함수들
def create_default_rate_limiter(requests_per_second: float = 0.5) -> RateLimiter:
    """기본 Rate Limiter 생성"""
    rate_config = RateLimitConfig(requests_per_second=requests_per_second)
    circuit_config = CircuitBreakerConfig()
    return RateLimiter(rate_config, circuit_config)

def create_aggressive_rate_limiter(requests_per_second: float = 2.0) -> RateLimiter:
    """공격적인 Rate Limiter 생성 (빠른 크롤링용)"""
    rate_config = RateLimitConfig(
        requests_per_second=requests_per_second,
        burst_size=5,
        max_tokens=10
    )
    circuit_config = CircuitBreakerConfig(
        failure_threshold=10,
        timeout_seconds=600  # 10분
    )
    return RateLimiter(rate_config, circuit_config)

def create_conservative_rate_limiter(requests_per_second: float = 0.2) -> RateLimiter:
    """보수적인 Rate Limiter 생성 (안전한 크롤링용)"""
    rate_config = RateLimitConfig(
        requests_per_second=requests_per_second,
        burst_size=1,
        max_tokens=3
    )
    circuit_config = CircuitBreakerConfig(
        failure_threshold=3,
        timeout_seconds=1800  # 30분
    )
    return RateLimiter(rate_config, circuit_config)