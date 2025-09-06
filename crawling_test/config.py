"""
크롤링 시스템 환경 설정 관리
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# OpenAI 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 크롤링 설정
CRAWLING_DELAY = float(os.getenv("CRAWLING_DELAY", "2.0"))  # 요청 간 지연 시간
CRAWLING_TIMEOUT = int(os.getenv("CRAWLING_TIMEOUT", "10"))  # 타임아웃 (초)

# Flask 설정
FLASK_HOST = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"

def validate_config():
    """필수 환경 변수가 설정되어 있는지 확인"""
    missing = []
    
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    if not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
    
    if missing:
        raise ValueError(f"다음 환경 변수가 설정되지 않았습니다: {', '.join(missing)}")
    
    return True

def get_user_agent():
    """크롤링용 User-Agent 헤더 반환"""
    return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def get_crawling_headers():
    """크롤링용 HTTP 헤더 반환"""
    return {
        'User-Agent': get_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
