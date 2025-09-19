"""
애플리케이션 설정 관리
환경 변수 기반 설정값 관리
"""

import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseSettings

class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 데이터베이스 설정
    database_url: str = os.getenv("DATABASE_URL", "")
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # AI/LLM 설정
    # OpenAI 설정 (주석 처리 - Gemini로 교체)
    # openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    # embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    # llm_model: str = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    
    # Gemini AI 설정
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    gemini_temperature: float = float(os.getenv("GEMINI_TEMPERATURE", "0.1"))
    gemini_max_tokens: int = int(os.getenv("GEMINI_MAX_TOKENS", "8192"))
    
    # 외부 API 설정
    kakao_rest_key: str = os.getenv("KAKAO_REST_KEY", "")
    
    # 애플리케이션 설정
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # RAG 설정
    max_search_results: int = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    
    # 캐시 설정
    enable_cache: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    
    # pydantic v2 설정 (예전 class Config 대체)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",   # 선언하지 않은 변수는 무시
    )

# 전역 설정 인스턴스
settings = Settings()
