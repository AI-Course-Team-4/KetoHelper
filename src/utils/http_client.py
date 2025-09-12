"""
🌐 HTTP 클라이언트 모듈
- Playwright 기반 크롤링
- 자동 재시도 및 백오프
- 차단 감지 및 회피
- 속도 제한 준수
"""

import asyncio
import time
import random
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from .config_loader import get_config
from .logger import get_logger, log_request, log_blocking_detected, log_rate_limit


class RateLimiter:
    """사이트별 속도 제한 관리"""
    
    def __init__(self):
        self.site_last_request = {}  # 사이트별 마지막 요청 시간
        self.site_qps = {}          # 사이트별 현재 QPS
        
    async def wait_for_rate_limit(self, site: str, target_qps: float):
        """속도 제한에 따른 대기"""
        now = time.time()
        last_request = self.site_last_request.get(site, 0)
        
        # QPS에 따른 최소 대기 시간 계산
        min_interval = 1.0 / target_qps
        elapsed = now - last_request
        
        if elapsed < min_interval:
            wait_time = min_interval - elapsed
            await asyncio.sleep(wait_time)
        
        self.site_last_request[site] = time.time()
    
    def update_qps(self, site: str, new_qps: float):
        """사이트별 QPS 업데이트"""
        old_qps = self.site_qps.get(site, 0)
        self.site_qps[site] = new_qps
        
        if old_qps != new_qps:
            log_rate_limit(site, old_qps, new_qps)


class BlockingDetector:
    """차단 감지기"""
    
    def __init__(self, config):
        self.config = config
        self.blocking_indicators = config.raw_config.get("error_handling", {}).get(
            "blocking_indicators", []
        )
    
    def detect_blocking(self, content: str, url: str) -> Optional[str]:
        """차단 감지"""
        content_lower = content.lower()
        
        for indicator in self.blocking_indicators:
            if indicator.lower() in content_lower:
                return indicator
                
        return None
    
    def is_empty_page(self, content: str, parser_config: Dict[str, Any]) -> bool:
        """빈 페이지 감지"""
        # HTML 길이가 너무 짧음
        if len(content.strip()) < 100:
            return True
            
        # 파서 설정에 정의된 빈 페이지 패턴 확인
        empty_patterns = parser_config.get("blocking_detection", {}).get(
            "empty_page_selectors", []
        )
        
        for pattern in empty_patterns:
            if pattern in content:
                return True
                
        return False


class HttpClient:
    """고급 HTTP 클라이언트"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = get_config(config_path)
        self.logger = get_logger("http_client")
        self.rate_limiter = RateLimiter()
        self.blocking_detector = BlockingDetector(self.config)
        
        # Playwright 인스턴스
        self.playwright = None
        self.browser = None
        self.contexts = {}  # 사이트별 브라우저 컨텍스트
        
        # 통계
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "blocked_requests": 0
        }
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        await self.close()
    
    async def start(self):
        """클라이언트 시작"""
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            
            # 브라우저 시작
            playwright_config = self.config.crawler.playwright
            self.browser = await self.playwright.chromium.launch(
                headless=playwright_config["headless"],
                slow_mo=playwright_config["slow_mo"]
            )
            
            self.logger.info("HTTP 클라이언트 시작됨")
    
    async def close(self):
        """클라이언트 종료"""
        # 모든 컨텍스트 종료
        for context in self.contexts.values():
            await context.close()
        self.contexts.clear()
        
        # 브라우저 종료
        if self.browser:
            await self.browser.close()
            self.browser = None
            
        # Playwright 종료
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
            
        self.logger.info("HTTP 클라이언트 종료됨")
    
    async def get_context(self, site: str) -> BrowserContext:
        """사이트별 브라우저 컨텍스트 반환"""
        if site not in self.contexts:
            # 새 컨텍스트 생성
            viewport = self.config.crawler.playwright["viewport"]
            user_agent = self.config.get_user_agent()
            
            self.contexts[site] = await self.browser.new_context(
                viewport=viewport,
                user_agent=user_agent,
                # 리소스 차단으로 속도 향상
                # (이미지, 폰트, 미디어 차단)
            )
            
            # 리소스 차단 설정
            await self.contexts[site].route(
                "**/*", 
                lambda route: self._handle_route(route)
            )
            
        return self.contexts[site]
    
    async def _handle_route(self, route):
        """리소스 라우팅 처리 (차단)"""
        resource_type = route.request.resource_type
        
        # 불필요한 리소스 차단
        if resource_type in ["image", "font", "media", "websocket"]:
            await route.abort()
        else:
            await route.continue_()
    
    async def fetch(self, url: str, site: str, 
                   parser_config: Optional[Dict[str, Any]] = None,
                   max_retries: Optional[int] = None,
                   custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """웹페이지 크롤링"""
        if not await self._is_started():
            await self.start()
            
        max_retries = max_retries or self.config.crawler.retry["max_attempts"]
        start_time = time.time()
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 속도 제한 적용
                target_qps = self.config.get_rate_limit(site)
                await self.rate_limiter.wait_for_rate_limit(site, target_qps)
                
                # 요청 실행
                result = await self._fetch_page(
                    url, site, parser_config, custom_headers
                )
                
                # 성공 통계 업데이트
                self.stats["total_requests"] += 1
                self.stats["successful_requests"] += 1
                
                # 응답 시간 로깅
                response_time = time.time() - start_time
                log_request("GET", url, 200, response_time, site)
                
                return result
                
            except Exception as e:
                last_error = e
                self.stats["total_requests"] += 1
                self.stats["failed_requests"] += 1
                
                self.logger.warning(
                    f"요청 실패 (시도 {attempt + 1}/{max_retries}): {url} - {e}"
                )
                
                # 재시도 전 백오프
                if attempt < max_retries - 1:
                    backoff_time = await self._calculate_backoff(attempt, site, str(e))
                    await asyncio.sleep(backoff_time)
        
        # 모든 재시도 실패
        response_time = time.time() - start_time
        log_request("GET", url, 500, response_time, site)
        
        raise Exception(f"모든 재시도 실패: {url} - {last_error}")
    
    async def _fetch_page(self, url: str, site: str, 
                         parser_config: Optional[Dict[str, Any]],
                         custom_headers: Optional[Dict[str, str]]) -> Dict[str, Any]:
        """실제 페이지 크롤링"""
        context = await self.get_context(site)
        page = await context.new_page()
        
        try:
            # 커스텀 헤더 설정
            if custom_headers:
                await page.set_extra_http_headers(custom_headers)
            
            # 페이지 로드
            timeout = self.config.crawler.page_timeout * 1000
            
            await page.goto(url, timeout=timeout, wait_until="networkidle")
            
            # 페이지 로딩 완료 대기 (파서 설정에 따라)
            if parser_config:
                await self._wait_for_page_load(page, parser_config)
            
            # HTML 콘텐츠 추출
            content = await page.content()
            
            # 차단 감지
            blocking_indicator = self.blocking_detector.detect_blocking(content, url)
            if blocking_indicator:
                self.stats["blocked_requests"] += 1
                log_blocking_detected(site, url, blocking_indicator)
                raise Exception(f"차단 감지: {blocking_indicator}")
            
            # 빈 페이지 감지
            if parser_config and self.blocking_detector.is_empty_page(content, parser_config):
                raise Exception("빈 페이지 감지")
            
            # 페이지 정보 반환
            return {
                "url": url,
                "content": content,
                "title": await page.title(),
                "status": "success",
                "site": site
            }
            
        except PlaywrightTimeoutError:
            raise Exception("페이지 로드 타임아웃")
        except Exception as e:
            raise e
        finally:
            await page.close()
    
    async def _wait_for_page_load(self, page: Page, parser_config: Dict[str, Any]):
        """페이지 로딩 완료 대기"""
        timing_config = parser_config.get("timing", {})
        loading_selectors = parser_config.get("blocking_detection", {}).get(
            "loading_complete_selectors", []
        )
        
        # 특정 요소가 나타날 때까지 대기
        for selector in loading_selectors:
            try:
                await page.wait_for_selector(
                    selector, 
                    timeout=timing_config.get("element_timeout", 10) * 1000
                )
                break
            except PlaywrightTimeoutError:
                continue
        
        # 추가 대기
        action_delay = timing_config.get("action_delay", 1)
        await asyncio.sleep(action_delay)
    
    async def _calculate_backoff(self, attempt: int, site: str, error: str) -> float:
        """백오프 시간 계산"""
        retry_config = self.config.crawler.retry
        
        # 기본 지수 백오프
        base_delay = retry_config["initial_delay"]
        multiplier = retry_config["backoff_multiplier"]
        max_delay = retry_config["max_delay"]
        
        backoff_time = min(base_delay * (multiplier ** attempt), max_delay)
        
        # 차단 감지 시 추가 대기
        if "차단" in error or "block" in error.lower():
            backoff_time *= 2
            
            # QPS 감속
            current_qps = self.config.get_rate_limit(site)
            new_qps = current_qps * 0.5
            self.rate_limiter.update_qps(site, new_qps)
        
        # 랜덤 지터 추가 (±20%)
        jitter = random.uniform(0.8, 1.2)
        return backoff_time * jitter
    
    async def _is_started(self) -> bool:
        """클라이언트 시작 여부 확인"""
        return self.playwright is not None and self.browser is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """통계 반환"""
        total = self.stats["total_requests"]
        if total == 0:
            return self.stats
        
        return {
            **self.stats,
            "success_rate": self.stats["successful_requests"] / total,
            "failure_rate": self.stats["failed_requests"] / total,
            "blocking_rate": self.stats["blocked_requests"] / total
        }
    
    def reset_stats(self):
        """통계 초기화"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "blocked_requests": 0
        }


# 전역 클라이언트 인스턴스
_http_client = None


async def get_http_client() -> HttpClient:
    """전역 HTTP 클라이언트 반환"""
    global _http_client
    
    if _http_client is None:
        _http_client = HttpClient()
        await _http_client.start()
    
    return _http_client


async def fetch_page(url: str, site: str, 
                    parser_config: Optional[Dict[str, Any]] = None,
                    max_retries: Optional[int] = None,
                    custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """페이지 크롤링 (편의 함수)"""
    client = await get_http_client()
    return await client.fetch(url, site, parser_config, max_retries, custom_headers)


async def close_http_client():
    """전역 HTTP 클라이언트 종료"""
    global _http_client
    if _http_client:
        await _http_client.close()
        _http_client = None


if __name__ == "__main__":
    # 테스트 코드
    async def test_http_client():
        async with HttpClient() as client:
            try:
                result = await client.fetch(
                    "https://httpbin.org/html", 
                    "test_site"
                )
                print(f"성공: {result['title']}")
                print(f"통계: {client.get_stats()}")
                
            except Exception as e:
                print(f"실패: {e}")
    
    asyncio.run(test_http_client())