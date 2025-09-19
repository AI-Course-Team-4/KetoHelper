"""
기본 크롤러 추상 클래스
"""

import asyncio
import time
from typing import List, Dict, Any, AsyncIterator, Optional
from abc import ABC, abstractmethod
import httpx
from selectolax.parser import HTMLParser
import logging

from core.interfaces.crawler_interface import (
    CrawlerInterface, RestaurantCrawlerInterface, CrawlerStatus,
    CrawlResult, CrawlStatistics
)
from infrastructure.external.rate_limiter import RateLimiter, create_default_rate_limiter
from config.settings import settings

logger = logging.getLogger(__name__)

class BaseCrawler(RestaurantCrawlerInterface):
    """기본 크롤러 구현"""

    def __init__(
        self,
        rate_limiter: Optional[RateLimiter] = None,
        timeout: int = None,
        max_retries: int = 3
    ):
        self.rate_limiter = rate_limiter or create_default_rate_limiter(
            settings.crawler.rate_limit
        )
        self.timeout = timeout or settings.crawler.timeout
        self.max_retries = max_retries

        # 상태 관리
        self._status = CrawlerStatus.IDLE
        self._statistics = CrawlStatistics()
        self._start_time = None

        # HTTP 클라이언트
        self._client: Optional[httpx.AsyncClient] = None
        self._session_headers = {
            'User-Agent': settings.crawler.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    async def initialize(self) -> None:
        """크롤러 초기화"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self._session_headers,
                follow_redirects=True,
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20
                )
            )
            logger.info(f"{self.source_name} crawler initialized")

    async def cleanup(self) -> None:
        """크롤러 정리"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info(f"{self.source_name} crawler cleaned up")

    async def test_connection(self) -> bool:
        """연결 테스트"""
        try:
            await self.initialize()
            test_url = self.get_search_url("테스트", 1)

            async def test_request():
                response = await self._client.get(test_url)
                return response.status_code == 200

            result = await self.rate_limiter.wait_and_execute(test_request)
            return result
        except Exception as e:
            logger.error(f"Connection test failed for {self.source_name}: {e}")
            return False

    async def crawl_restaurant_list(self, keywords: List[str], max_pages: int = 5) -> List[str]:
        """키워드로 식당 URL 목록 크롤링"""
        await self.initialize()
        self._status = CrawlerStatus.RUNNING
        self._start_time = time.time()

        restaurant_urls = []

        try:
            for keyword in keywords:
                logger.info(f"Crawling restaurant list for keyword: {keyword}")

                for page in range(1, max_pages + 1):
                    try:
                        search_url = self.get_search_url(keyword, page)
                        page_urls = await self._crawl_search_page(search_url)

                        if not page_urls:
                            logger.info(f"No more results for keyword '{keyword}' at page {page}")
                            break

                        restaurant_urls.extend(page_urls)
                        logger.info(f"Found {len(page_urls)} URLs on page {page} for '{keyword}'")

                    except Exception as e:
                        logger.error(f"Error crawling page {page} for keyword '{keyword}': {e}")
                        continue

            # 중복 제거
            unique_urls = list(set(restaurant_urls))
            logger.info(f"Total unique restaurant URLs found: {len(unique_urls)}")

            return unique_urls

        finally:
            self._status = CrawlerStatus.IDLE

    async def crawl_restaurant_detail(self, url: str) -> CrawlResult:
        """식당 상세 정보 크롤링"""
        await self.initialize()
        start_time = time.time()

        async def fetch_and_parse():
            response = await self._client.get(url)
            response.raise_for_status()

            # HTML 파싱 및 정보 추출
            restaurant_info = await self.extract_restaurant_info(response.text, url)
            menu_list = await self.extract_menu_list(response.text, url)

            return {
                'restaurant': restaurant_info,
                'menus': menu_list,
                'source_url': url,
                'source_name': self.source_name
            }

        try:
            data = await self.rate_limiter.wait_and_execute(fetch_and_parse)
            response_time = time.time() - start_time

            # 통계 업데이트
            self._statistics.processed_urls += 1
            self._statistics.successful_urls += 1
            self._statistics.total_time_elapsed += response_time

            return CrawlResult(
                url=url,
                success=True,
                data=data,
                response_time=response_time,
                status_code=200
            )

        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)

            # 통계 업데이트
            self._statistics.processed_urls += 1
            self._statistics.failed_urls += 1
            self._statistics.total_time_elapsed += response_time

            logger.error(f"Error crawling {url}: {error_msg}")

            return CrawlResult(
                url=url,
                success=False,
                error=error_msg,
                response_time=response_time
            )

    async def crawl_batch(
        self,
        urls: List[str],
        max_concurrent: int = 5
    ) -> AsyncIterator[CrawlResult]:
        """URL 리스트 일괄 크롤링"""
        await self.initialize()
        self._status = CrawlerStatus.RUNNING
        self._start_time = time.time()
        self._statistics.total_urls = len(urls)

        semaphore = asyncio.Semaphore(max_concurrent)

        async def crawl_single_url(url: str) -> CrawlResult:
            async with semaphore:
                return await self.crawl_restaurant_detail(url)

        try:
            # 비동기 작업 생성
            tasks = [crawl_single_url(url) for url in urls]

            # 완료되는 대로 결과 yield
            for coro in asyncio.as_completed(tasks):
                result = await coro
                yield result

        finally:
            self._status = CrawlerStatus.IDLE
            # 평균 응답 시간 계산
            if self._statistics.processed_urls > 0:
                self._statistics.average_response_time = (
                    self._statistics.total_time_elapsed / self._statistics.processed_urls
                )

    async def _crawl_search_page(self, search_url: str) -> List[str]:
        """검색 페이지에서 식당 URL 추출"""
        async def fetch_search_page():
            response = await self._client.get(search_url)
            response.raise_for_status()
            return response.text

        try:
            html = await self.rate_limiter.wait_and_execute(fetch_search_page)
            return self._extract_restaurant_urls_from_search(html)
        except Exception as e:
            logger.error(f"Error crawling search page {search_url}: {e}")
            return []

    def _extract_restaurant_urls_from_search(self, html: str) -> List[str]:
        """검색 결과 HTML에서 식당 URL 추출 (서브클래스에서 구현)"""
        tree = HTMLParser(html)
        urls = []

        # 기본 구현: 'a' 태그에서 식당 URL 패턴 찾기
        for link in tree.css('a[href]'):
            href = link.attributes.get('href', '')
            if self.is_restaurant_url(href):
                urls.append(self._normalize_url(href))

        return urls

    def _normalize_url(self, url: str) -> str:
        """URL 정규화"""
        if url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"https://{self._get_base_domain()}{url}"
        elif not url.startswith('http'):
            return f"https://{self._get_base_domain()}/{url}"
        return url

    @property
    def status(self) -> CrawlerStatus:
        """현재 크롤러 상태"""
        return self._status

    @property
    def statistics(self) -> CrawlStatistics:
        """크롤링 통계"""
        return self._statistics

    def reset_statistics(self):
        """통계 리셋"""
        self._statistics = CrawlStatistics()

    # 추상 메서드들 (서브클래스에서 구현)
    @property
    @abstractmethod
    def source_name(self) -> str:
        """소스 이름"""
        pass

    @abstractmethod
    async def extract_restaurant_info(self, html: str, url: str) -> Dict[str, Any]:
        """HTML에서 식당 정보 추출"""
        pass

    @abstractmethod
    async def extract_menu_list(self, html: str, url: str) -> List[Dict[str, Any]]:
        """HTML에서 메뉴 리스트 추출"""
        pass

    @abstractmethod
    def get_search_url(self, keyword: str, page: int = 1) -> str:
        """검색 URL 생성"""
        pass

    @abstractmethod
    def is_restaurant_url(self, url: str) -> bool:
        """식당 상세 페이지 URL 여부 확인"""
        pass

    @abstractmethod
    def _get_base_domain(self) -> str:
        """기본 도메인 반환"""
        pass

    # 헬퍼 메서드들
    def _extract_text(self, element, default: str = "") -> str:
        """요소에서 텍스트 추출"""
        if element is None:
            return default
        return element.text(strip=True) or default

    def _extract_number(self, text: str, default: int = None) -> Optional[int]:
        """텍스트에서 숫자 추출"""
        import re
        numbers = re.findall(r'\d+', text.replace(',', ''))
        if numbers:
            try:
                return int(numbers[0])
            except ValueError:
                pass
        return default

    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        if not text:
            return ""
        import re
        # 연속된 공백을 단일 공백으로
        text = re.sub(r'\s+', ' ', text.strip())
        return text

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()