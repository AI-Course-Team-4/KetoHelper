"""
크롤러 인터페이스 정의
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator, Optional
from dataclasses import dataclass
from enum import Enum

class CrawlerStatus(Enum):
    """크롤러 상태"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"

@dataclass
class CrawlResult:
    """크롤링 결과"""
    url: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_time: Optional[float] = None
    status_code: Optional[int] = None

@dataclass
class CrawlStatistics:
    """크롤링 통계"""
    total_urls: int = 0
    processed_urls: int = 0
    successful_urls: int = 0
    failed_urls: int = 0
    rate_limited_count: int = 0
    average_response_time: float = 0.0
    total_time_elapsed: float = 0.0

class CrawlerInterface(ABC):
    """크롤러 기본 인터페이스"""

    @abstractmethod
    async def initialize(self) -> None:
        """크롤러 초기화"""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """크롤러 정리"""
        pass

    @abstractmethod
    async def crawl_restaurant_list(self, keywords: List[str], max_pages: int = 5) -> List[str]:
        """키워드로 식당 URL 목록 크롤링

        Args:
            keywords: 검색 키워드 리스트
            max_pages: 최대 페이지 수

        Returns:
            식당 상세 페이지 URL 리스트
        """
        pass

    @abstractmethod
    async def crawl_restaurant_detail(self, url: str) -> CrawlResult:
        """식당 상세 정보 크롤링

        Args:
            url: 식당 상세 페이지 URL

        Returns:
            크롤링 결과 객체
        """
        pass

    @abstractmethod
    async def crawl_batch(
        self,
        urls: List[str],
        max_concurrent: int = 5
    ) -> AsyncIterator[CrawlResult]:
        """URL 리스트 일괄 크롤링

        Args:
            urls: 크롤링할 URL 리스트
            max_concurrent: 최대 동시 실행 수

        Yields:
            크롤링 결과 객체들
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """연결 테스트"""
        pass

    @property
    @abstractmethod
    def status(self) -> CrawlerStatus:
        """현재 크롤러 상태"""
        pass

    @property
    @abstractmethod
    def statistics(self) -> CrawlStatistics:
        """크롤링 통계"""
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """소스 이름 (예: 'diningcode')"""
        pass

class RestaurantCrawlerInterface(CrawlerInterface):
    """식당 전용 크롤러 인터페이스"""

    @abstractmethod
    async def extract_restaurant_info(self, html: str, url: str) -> Dict[str, Any]:
        """HTML에서 식당 정보 추출

        Args:
            html: HTML 컨텐츠
            url: 원본 URL

        Returns:
            추출된 식당 정보
        """
        pass

    @abstractmethod
    async def extract_menu_list(self, html: str, url: str) -> List[Dict[str, Any]]:
        """HTML에서 메뉴 리스트 추출

        Args:
            html: HTML 컨텐츠
            url: 원본 URL

        Returns:
            추출된 메뉴 리스트
        """
        pass

    @abstractmethod
    def get_search_url(self, keyword: str, page: int = 1) -> str:
        """검색 URL 생성

        Args:
            keyword: 검색 키워드
            page: 페이지 번호

        Returns:
            검색 URL
        """
        pass

    @abstractmethod
    def is_restaurant_url(self, url: str) -> bool:
        """식당 상세 페이지 URL 여부 확인

        Args:
            url: 확인할 URL

        Returns:
            식당 URL 여부
        """
        pass

class CrawlerFactoryInterface(ABC):
    """크롤러 팩토리 인터페이스"""

    @abstractmethod
    def register(self, source_name: str, crawler_class: type) -> None:
        """크롤러 등록"""
        pass

    @abstractmethod
    def create(self, source_name: str, **kwargs) -> CrawlerInterface:
        """크롤러 생성"""
        pass

    @abstractmethod
    def list_sources(self) -> List[str]:
        """사용 가능한 소스 목록"""
        pass

    @abstractmethod
    def is_registered(self, source_name: str) -> bool:
        """소스 등록 여부 확인"""
        pass