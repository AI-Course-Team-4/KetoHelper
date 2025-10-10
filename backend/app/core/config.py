"""
애플리케이션 설정 관리
환경 변수 기반 설정값 관리
"""

import os
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
    # OpenAI 설정 (임베딩/LLM 공통 사용)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "")
    
    # 공통 LLM 설정
    llm_provider: str = os.getenv("LLM_PROVIDER", "gemini").lower()
    llm_model: str = os.getenv(
        "LLM_MODEL",
        os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    )
    llm_temperature: float = float(
        os.getenv("LLM_TEMPERATURE", os.getenv("GEMINI_TEMPERATURE", "0.1"))
    )
    llm_max_tokens: int = int(
        os.getenv("LLM_MAX_TOKENS", os.getenv("GEMINI_MAX_TOKENS", "8192"))
    )
    llm_timeout: int = int(os.getenv("LLM_TIMEOUT", "60"))

    # Gemini 설정
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    
    # RecipeValidator 전용 LLM 설정
    recipe_validator_provider: str = os.getenv("RECIPE_VALIDATOR_PROVIDER", "openai").lower()
    recipe_validator_model: str = os.getenv("RECIPE_VALIDATOR_MODEL", "gpt-4o-mini")
    recipe_validator_temperature: float = float(os.getenv("RECIPE_VALIDATOR_TEMPERATURE", "0.1"))
    recipe_validator_max_tokens: int = int(os.getenv("RECIPE_VALIDATOR_MAX_TOKENS", "4096"))
    recipe_validator_timeout: int = int(os.getenv("RECIPE_VALIDATOR_TIMEOUT", "30"))
    
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
