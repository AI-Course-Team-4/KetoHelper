import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

CRAWL_CONFIG = {
    "base_url": "https://www.10000recipe.com",
    "search_query": "키토",
    "max_pages": 50,  # 전체 페이지 크롤링을 위해 50페이지로 증가
    "consecutive_empty_pages": 3,
    "rate_limit_seconds": 2.0,
    "random_sleep_min": 0.5,
    "random_sleep_max": 2.0,
    "request_timeout": 10,
    "detail_timeout": 30,
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}