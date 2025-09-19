"""
크롤러 팩토리 구현
"""

from typing import Dict, Type, List
import logging

from core.interfaces.crawler_interface import CrawlerInterface, CrawlerFactoryInterface
from infrastructure.external.rate_limiter import (
    RateLimiter, create_default_rate_limiter, create_conservative_rate_limiter
)

logger = logging.getLogger(__name__)

class CrawlerFactory(CrawlerFactoryInterface):
    """크롤러 팩토리 구현"""

    def __init__(self):
        self._crawlers: Dict[str, Type[CrawlerInterface]] = {}
        self._rate_limiters: Dict[str, RateLimiter] = {}

    def register(self, source_name: str, crawler_class: Type[CrawlerInterface]) -> None:
        """크롤러 등록"""
        if not issubclass(crawler_class, CrawlerInterface):
            raise ValueError(f"Crawler class must implement CrawlerInterface")

        self._crawlers[source_name] = crawler_class
        logger.info(f"Registered crawler for source: {source_name}")

    def create(self, source_name: str, **kwargs) -> CrawlerInterface:
        """크롤러 생성"""
        if source_name not in self._crawlers:
            raise ValueError(f"Unknown crawler source: {source_name}")

        crawler_class = self._crawlers[source_name]

        # Rate Limiter 가져오기 또는 생성
        if 'rate_limiter' not in kwargs:
            kwargs['rate_limiter'] = self._get_or_create_rate_limiter(source_name)

        try:
            instance = crawler_class(**kwargs)
            logger.info(f"Created crawler instance for source: {source_name}")
            return instance
        except Exception as e:
            logger.error(f"Failed to create crawler for {source_name}: {e}")
            raise

    def list_sources(self) -> List[str]:
        """사용 가능한 소스 목록"""
        return list(self._crawlers.keys())

    def is_registered(self, source_name: str) -> bool:
        """소스 등록 여부 확인"""
        return source_name in self._crawlers

    def _get_or_create_rate_limiter(self, source_name: str) -> RateLimiter:
        """소스별 Rate Limiter 가져오기 또는 생성"""
        if source_name not in self._rate_limiters:
            # 소스별 다른 Rate Limiting 정책 적용
            if source_name == 'diningcode':
                # 다이닝코드는 보수적으로
                self._rate_limiters[source_name] = create_conservative_rate_limiter(0.5)
            elif source_name == 'siksin':
                # 식신은 기본값
                self._rate_limiters[source_name] = create_default_rate_limiter(0.3)
            else:
                # 기타는 매우 보수적으로
                self._rate_limiters[source_name] = create_conservative_rate_limiter(0.2)

        return self._rate_limiters[source_name]

    def get_rate_limiter_stats(self, source_name: str = None) -> Dict:
        """Rate Limiter 통계 반환"""
        if source_name:
            if source_name in self._rate_limiters:
                return {source_name: self._rate_limiters[source_name].get_stats()}
            else:
                return {}
        else:
            return {
                name: limiter.get_stats()
                for name, limiter in self._rate_limiters.items()
            }

    def reset_rate_limiter_stats(self, source_name: str = None):
        """Rate Limiter 통계 리셋"""
        if source_name:
            if source_name in self._rate_limiters:
                self._rate_limiters[source_name].reset()
        else:
            for limiter in self._rate_limiters.values():
                limiter.reset()

# 글로벌 팩토리 인스턴스
crawler_factory = CrawlerFactory()