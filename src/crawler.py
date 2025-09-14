import asyncio
from typing import List, Set, Dict
from urllib.parse import urljoin
from .config import CRAWL_CONFIG
from .http_client import RateLimitedHTTPClient
from .parsers import RecipeListParser, RecipeDetailParser
from .supabase_client import SupabaseClient

class KetoCrawler:
    """만개의레시피 키토 크롤러"""

    def __init__(self):
        self.config = CRAWL_CONFIG
        self.http_client = RateLimitedHTTPClient(
            rate_limit_seconds=self.config['rate_limit_seconds'],
            random_sleep_min=self.config['random_sleep_min'],
            random_sleep_max=self.config['random_sleep_max'],
            request_timeout=self.config['request_timeout']
        )
        self.list_parser = RecipeListParser(self.config['base_url'])
        self.detail_parser = RecipeDetailParser()
        self.supabase_client = SupabaseClient()

        # 크롤링 상태
        self.discovered_urls: Set[str] = set()
        self.processed_urls: Set[str] = set()
        self.failed_urls: List[str] = []
        self.consecutive_empty_pages = 0
        self.run_id: str = ""

        # 통계
        self.stats = {
            'pages_crawled': 0,
            'recipes_discovered': 0,
            'recipes_processed': 0,
            'recipes_inserted': 0,
            'recipes_updated': 0,
            'recipes_failed': 0
        }

    async def run(self) -> Dict:
        """크롤링 실행"""
        print(f"Starting Keto recipe crawling for query: {self.config['search_query']}")

        try:
            # 크롤링 실행 이력 생성
            self.run_id = await self.supabase_client.create_crawl_run(
                query=self.config['search_query'],
                page_start=1
            )

            # 기존 레시피 URL 로드
            existing_urls = await self.supabase_client.get_existing_recipe_urls()
            print(f"Found {len(existing_urls)} existing recipes in database")

            # 목록 페이지 크롤링
            await self._crawl_recipe_lists()

            # 새로운 레시피만 필터링
            new_urls = self.discovered_urls - existing_urls
            print(f"Discovered {len(self.discovered_urls)} total URLs, {len(new_urls)} are new")

            # 상세 페이지 크롤링
            await self._crawl_recipe_details(new_urls)

            # 실행 이력 업데이트
            await self.supabase_client.update_crawl_run(
                self.run_id,
                page_end=self.stats['pages_crawled'],
                inserted_count=self.stats['recipes_inserted'],
                updated_count=self.stats['recipes_updated'],
                error_count=self.stats['recipes_failed'],
                notes=f"Processed {self.stats['recipes_processed']} recipes"
            )

            print("Crawling completed!")
            print(f"Statistics: {self.stats}")

            return self.stats

        except Exception as e:
            print(f"Crawling failed: {e}")
            if self.run_id:
                await self.supabase_client.update_crawl_run(
                    self.run_id,
                    error_count=self.stats['recipes_failed'],
                    notes=f"Failed: {str(e)}"
                )
            raise
        finally:
            self.http_client.close()

    async def _crawl_recipe_lists(self):
        """레시피 목록 페이지 크롤링"""
        page = 1
        self.consecutive_empty_pages = 0

        while (page <= self.config['max_pages'] and
               self.consecutive_empty_pages < self.config['consecutive_empty_pages']):

            print(f"Crawling page {page}...")

            # 검색 결과 페이지 URL 구성
            search_url = f"{self.config['base_url']}/recipe/list.html?q={self.config['search_query']}&page={page}"

            # 페이지 요청
            response = await self.http_client.get(search_url)
            if not response:
                print(f"Failed to fetch page {page}")
                page += 1
                continue

            # 레시피 링크 추출
            recipe_links = self.list_parser.parse_recipe_links(response.text)
            new_links_count = 0

            for link in recipe_links:
                if link not in self.discovered_urls:
                    self.discovered_urls.add(link)
                    new_links_count += 1

            print(f"Page {page}: Found {len(recipe_links)} total links, {new_links_count} new")

            # 증분 종료 조건 확인
            if new_links_count == 0:
                self.consecutive_empty_pages += 1
                print(f"No new links found. Consecutive empty pages: {self.consecutive_empty_pages}")
            else:
                self.consecutive_empty_pages = 0

            self.stats['pages_crawled'] = page
            self.stats['recipes_discovered'] = len(self.discovered_urls)

            # 다음 페이지 확인
            if not self.list_parser.has_next_page(response.text, search_url):
                print("No more pages available")
                break

            page += 1

        print(f"Recipe list crawling completed. Pages: {self.stats['pages_crawled']}, URLs: {len(self.discovered_urls)}")

    async def _crawl_recipe_details(self, urls_to_process: Set[str]):
        """레시피 상세 정보 크롤링"""
        if not urls_to_process:
            print("No new URLs to process")
            return

        # 5개 제한이 있는 경우
        if hasattr(self, 'max_recipes') and self.max_recipes:
            urls_to_process = list(urls_to_process)[:self.max_recipes]
            print(f"Processing {len(urls_to_process)} recipe detail pages (limited to {self.max_recipes})...")
        else:
            print(f"Processing {len(urls_to_process)} recipe detail pages...")

        for i, url in enumerate(urls_to_process, 1):
            print(f"Processing recipe {i}/{len(urls_to_process)}: {url}")

            try:
                # 상세 페이지 요청
                response = await self.http_client.get(url, timeout=self.config['detail_timeout'])
                if not response:
                    self.failed_urls.append(url)
                    self.stats['recipes_failed'] += 1
                    continue

                # 레시피 정보 파싱
                recipe_data = self.detail_parser.parse_recipe(response.text, url)

                # 데이터 검증
                if not self._validate_recipe_data(recipe_data):
                    print(f"Invalid recipe data for {url}")
                    self.failed_urls.append(url)
                    self.stats['recipes_failed'] += 1
                    continue

                # Supabase에 저장
                success = await self.supabase_client.upsert_recipe(recipe_data)
                if success:
                    if url in await self.supabase_client.get_existing_recipe_urls():
                        self.stats['recipes_updated'] += 1
                    else:
                        self.stats['recipes_inserted'] += 1
                    self.processed_urls.add(url)
                else:
                    self.failed_urls.append(url)
                    self.stats['recipes_failed'] += 1

                self.stats['recipes_processed'] += 1

                # 진행상황 출력
                if i % 10 == 0:
                    print(f"Progress: {i}/{len(urls_to_process)} processed")

            except Exception as e:
                print(f"Error processing {url}: {e}")
                self.failed_urls.append(url)
                self.stats['recipes_failed'] += 1

        print(f"Recipe detail crawling completed. Processed: {self.stats['recipes_processed']}")

    def _validate_recipe_data(self, recipe_data: Dict) -> bool:
        """레시피 데이터 유효성 검사"""
        required_fields = ['source_url', 'title']

        for field in required_fields:
            if not recipe_data.get(field):
                return False

        # 재료나 조리순서 중 하나는 있어야 함
        if not recipe_data.get('ingredients') and not recipe_data.get('steps'):
            return False

        return True

    async def test_run(self, max_pages: int = 3) -> Dict:
        """테스트용 제한된 크롤링"""
        print(f"Starting test crawling (max {max_pages} pages)")

        original_max = self.config['max_pages']
        self.config['max_pages'] = max_pages

        try:
            result = await self.run()
            return result
        finally:
            self.config['max_pages'] = original_max