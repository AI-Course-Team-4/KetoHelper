import asyncio
import time
import random
from typing import Optional
from fake_useragent import UserAgent
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class RateLimitedHTTPClient:
    """Rate-limited HTTP client with retry logic"""

    def __init__(self, rate_limit_seconds: float = 2.0,
                 random_sleep_min: float = 0.5,
                 random_sleep_max: float = 2.0,
                 request_timeout: int = 10):
        self.rate_limit_seconds = rate_limit_seconds
        self.random_sleep_min = random_sleep_min
        self.random_sleep_max = random_sleep_max
        self.request_timeout = request_timeout
        self.last_request_time = 0

        # User agent rotation
        self.ua = UserAgent()

        # Setup session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    async def get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Rate-limited GET request with retry logic"""

        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_seconds:
            sleep_time = self.rate_limit_seconds - time_since_last
            await asyncio.sleep(sleep_time)

        # Random additional delay
        random_delay = random.uniform(self.random_sleep_min, self.random_sleep_max)
        await asyncio.sleep(random_delay)

        # Set headers
        headers = kwargs.get('headers', {})
        headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        kwargs['headers'] = headers

        # Set timeout
        kwargs['timeout'] = kwargs.get('timeout', self.request_timeout)

        try:
            response = await asyncio.to_thread(
                self.session.get, url, **kwargs
            )
            self.last_request_time = time.time()

            if response.status_code == 200:
                # 인코딩 문제 해결
                if response.encoding == 'ISO-8859-1':
                    # ISO-8859-1로 감지된 경우 UTF-8로 강제 설정
                    response.encoding = 'utf-8'
                elif not response.encoding or response.encoding.lower() in ['iso-8859-1', 'windows-1252']:
                    # 인코딩이 제대로 감지되지 않은 경우 UTF-8로 강제 설정
                    response.encoding = 'utf-8'
                
                return response
            else:
                print(f"HTTP {response.status_code} for {url}")
                return None

        except Exception as e:
            print(f"Request failed for {url}: {e}")
            return None

    def close(self):
        """Close the session"""
        self.session.close()