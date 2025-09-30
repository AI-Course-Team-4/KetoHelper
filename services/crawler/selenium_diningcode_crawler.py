#!/usr/bin/env python3
"""
Selenium 기반 Diningcode 무한 스크롤 크롤러
ChromeDriver 문제 해결을 위한 개선된 버전
"""

import asyncio
import time
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import httpx
from selectolax.parser import HTMLParser

from .base_crawler import BaseCrawler
from core.domain.restaurant import Restaurant
from core.domain.menu import Menu
from core.interfaces.crawler_interface import CrawlResult


class SeleniumDiningcodeCrawler(BaseCrawler):
    """Selenium 기반 Diningcode 크롤러 (무한 스크롤 지원)"""
    
    def __init__(self, rate_limiter=None):
        super().__init__(rate_limiter)
        self.driver = None
        self.base_url = "https://www.diningcode.com"
        self.search_url = "https://www.diningcode.com/list.php"
    
    @property
    def source_name(self) -> str:
        return "diningcode"
    
    def _get_base_domain(self) -> str:
        return "diningcode.com"
    
    def get_search_url(self, keywords: List[str]) -> str:
        """검색 URL 생성"""
        keyword = keywords[0] if keywords else "맛집"
        return f"{self.search_url}?query={keyword}&query_type=keyword"
    
    def is_restaurant_url(self, url: str) -> bool:
        """레스토랑 상세 페이지 URL인지 확인"""
        return "profile.php?rid=" in url
    
    def extract_restaurant_info(self, html: str, url: str) -> Dict[str, Any]:
        """레스토랑 정보 추출 (기존 로직 재사용)"""
        from .diningcode_crawler import DiningcodeCrawler
        temp_crawler = DiningcodeCrawler()
        # 실제로는 파싱만 수행하므로 초기화 없이 메서드만 호출
        return temp_crawler._extract_restaurant_info(html, url)
    
    def extract_menu_list(self, html: str, url: str) -> List[Dict[str, Any]]:
        """메뉴 목록 추출 (기존 로직 재사용)"""
        from .diningcode_crawler import DiningcodeCrawler
        temp_crawler = DiningcodeCrawler()
        # 실제로는 파싱만 수행하므로 초기화 없이 메서드만 호출
        return temp_crawler._extract_menu_list(html, url)
        
    async def initialize(self) -> None:
        """크롤러 초기화"""
        print("🔄 Selenium 크롤러 초기화 중...")
        try:
            # Chrome 옵션 설정
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # 헤드리스 모드
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-webgl")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")  # JS 비활성화로 무한 스크롤 방지
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # ChromeDriver 자동 다운로드 및 설정
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print("✅ ChromeDriver 초기화 성공")
            except Exception as e:
                print(f"❌ ChromeDriver 초기화 실패: {e}")
                # Edge 대안 시도
                try:
                    from webdriver_manager.microsoft import EdgeChromiumDriverManager
                    from selenium.webdriver.edge.options import Options as EdgeOptions
                    from selenium.webdriver.edge.service import Service as EdgeService
                    from selenium.webdriver.edge.webdriver import WebDriver as EdgeWebDriver
                    
                    edge_options = EdgeOptions()
                    edge_options.add_argument("--headless")
                    edge_options.add_argument("--no-sandbox")
                    edge_options.add_argument("--disable-dev-shm-usage")
                    edge_options.add_argument("--disable-gpu")
                    edge_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                    
                    edge_service = EdgeService(EdgeChromiumDriverManager().install())
                    self.driver = EdgeWebDriver(service=edge_service, options=edge_options)
                    print("✅ EdgeDriver 초기화 성공 (Chrome 대안)")
                except Exception as edge_e:
                    print(f"❌ EdgeDriver 초기화도 실패: {edge_e}")
                    raise Exception("Chrome과 Edge 모두 초기화 실패")
            
            # HTTP 클라이언트 초기화 (백업용)
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            
            print("✅ Selenium 크롤러 초기화 완료")
            
        except Exception as e:
            print(f"❌ 크롤러 초기화 실패: {e}")
            raise

    async def crawl_restaurant_list(
        self, 
        keywords: List[str], 
        max_pages: int = 2,
        target_count: int = 100
    ) -> List[str]:
        """무한 스크롤로 식당 목록 크롤링"""
        print(f"🔄 무한 스크롤 크롤링 시작: {keywords}, 목표 {target_count}개")
        
        all_urls = []
        
        for keyword in keywords:
            print(f"\n🔍 키워드 '{keyword}' 무한 스크롤 중...")
            
            try:
                # 검색 URL 구성
                search_params = {
                    'query': keyword,
                    'query_type': 'keyword'
                }
                
                search_url = f"{self.search_url}?" + "&".join([f"{k}={v}" for k, v in search_params.items()])
                print(f"   📍 검색 URL: {search_url}")
                
                # Selenium으로 페이지 로드
                self.driver.get(search_url)
                time.sleep(3)  # 초기 로딩 대기
                
                # 무한 스크롤 수행
                urls_for_keyword = await self._perform_infinite_scroll(search_url, target_count)
                print(f"   ✅ '{keyword}'에서 {len(urls_for_keyword)}개 URL 발견")
                
                all_urls.extend(urls_for_keyword)
                
                # 목표 달성 시 중단
                if len(all_urls) >= target_count:
                    print(f"🎉 목표 {target_count}개 달성! 중단")
                    break
                    
            except Exception as e:
                print(f"   ❌ 키워드 '{keyword}' 크롤링 실패: {e}")
                continue
        
        # 중복 제거
        unique_urls = list(set(all_urls))
        print(f"\n📊 최종 결과:")
        print(f"   총 발견된 URL: {len(all_urls)}개")
        print(f"   중복 제거 후: {len(unique_urls)}개")
        
        return unique_urls[:target_count]

    async def _perform_infinite_scroll(self, url: str, target_count: int) -> List[str]:
        """무한 스크롤 수행 및 URL 추출"""
        print(f"   🔄 무한 스크롤 시작... (목표: {target_count}개)")
        
        collected_urls = set()
        scroll_count = 0
        max_scrolls = 50  # 최대 스크롤 횟수 제한
        
        try:
            while len(collected_urls) < target_count and scroll_count < max_scrolls:
                # 현재 페이지에서 URL 추출
                current_urls = await self._extract_restaurant_urls_from_page()
                collected_urls.update(current_urls)
                
                print(f"   📍 스크롤 {scroll_count + 1}: {len(current_urls)}개 새 URL, 총 {len(collected_urls)}개")
                
                # 더 이상 새 URL이 없으면 중단
                if len(current_urls) == 0:
                    print(f"   ⚠️ 새 URL 없음, 스크롤 중단")
                    break
                
                # 스크롤 다운
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)  # 스크롤 후 로딩 대기
                scroll_count += 1
                
                # 진행률 표시
                if scroll_count % 10 == 0:
                    print(f"   📊 진행률: {scroll_count}번 스크롤, {len(collected_urls)}개 URL 수집")
            
            print(f"   ✅ 무한 스크롤 완료: {scroll_count}번 스크롤, {len(collected_urls)}개 URL")
            return list(collected_urls)
            
        except Exception as e:
            print(f"   ❌ 무한 스크롤 중 오류: {e}")
            return list(collected_urls)

    async def _extract_restaurant_urls_from_page(self) -> List[str]:
        """현재 페이지에서 식당 URL 추출"""
        try:
            # 페이지 소스 가져오기
            page_source = self.driver.page_source
            
            # HTML 파싱
            parser = HTMLParser(page_source)
            
            # 식당 링크 찾기 (다이닝코드 패턴)
            restaurant_urls = []
            
            # profile.php?rid= 패턴 찾기
            links = parser.css('a[href*="profile.php?rid="]')
            for link in links:
                href = link.attributes.get('href', '')
                if 'profile.php?rid=' in href:
                    full_url = urljoin(self.base_url, href)
                    restaurant_urls.append(full_url)
            
            # JavaScript에서 rid 추출
            scripts = parser.css('script')
            for script in scripts:
                script_content = script.text()
                if script_content:
                    # rid= 패턴 찾기
                    rid_matches = re.findall(r'rid["\']?\s*[:=]\s*["\']?([a-zA-Z0-9]+)', script_content)
                    for rid in rid_matches:
                        if len(rid) > 5:  # 유효한 rid 길이 체크
                            url = f"{self.base_url}/profile.php?rid={rid}"
                            restaurant_urls.append(url)
            
            return list(set(restaurant_urls))  # 중복 제거
            
        except Exception as e:
            print(f"   ❌ URL 추출 중 오류: {e}")
            return []

    async def crawl_restaurant_detail(self, url: str) -> CrawlResult:
        """식당 상세 정보 크롤링 (기존 httpx 방식 사용)"""
        try:
            # httpx 클라이언트로 상세 정보 크롤링
            response = await self._client.get(url)
            response.raise_for_status()
            
            # 기존 로직 재사용
            from .diningcode_crawler import DiningcodeCrawler
            temp_crawler = DiningcodeCrawler()
            await temp_crawler.initialize()
            
            # 상세 정보 파싱
            result = await temp_crawler._parse_restaurant_detail(response.text, url)
            
            return result
            
        except Exception as e:
            print(f"❌ 상세 정보 크롤링 실패: {url} - {e}")
            return CrawlResult(success=False, error=str(e), data=None)

    async def close(self) -> None:
        """크롤러 정리"""
        try:
            if self.driver:
                self.driver.quit()
                print("✅ Selenium 드라이버 종료")
            
            if hasattr(self, '_client') and self._client:
                await self._client.aclose()
                print("✅ HTTP 클라이언트 종료")
                
        except Exception as e:
            print(f"⚠️ 크롤러 정리 중 오류: {e}")