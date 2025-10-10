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
    
    # MealPlannerAgent 전용 LLM 설정
    meal_planner_provider: str = os.getenv("MEAL_PLANNER_PROVIDER", llm_provider).lower()
    meal_planner_model: str = os.getenv("MEAL_PLANNER_MODEL", llm_model)
    meal_planner_temperature: float = float(os.getenv("MEAL_PLANNER_TEMPERATURE", str(llm_temperature)))
    meal_planner_max_tokens: int = int(os.getenv("MEAL_PLANNER_MAX_TOKENS", str(llm_max_tokens)))
    meal_planner_timeout: int = int(os.getenv("MEAL_PLANNER_TIMEOUT", str(llm_timeout)))
    
    # PlaceSearchAgent 전용 LLM 설정
    place_search_provider: str = os.getenv("PLACE_SEARCH_PROVIDER", llm_provider).lower()
    place_search_model: str = os.getenv("PLACE_SEARCH_MODEL", llm_model)
    place_search_temperature: float = float(os.getenv("PLACE_SEARCH_TEMPERATURE", str(llm_temperature)))
    place_search_max_tokens: int = int(os.getenv("PLACE_SEARCH_MAX_TOKENS", str(llm_max_tokens)))
    place_search_timeout: int = int(os.getenv("PLACE_SEARCH_TIMEOUT", str(llm_timeout)))
    
    # ChatAgent 전용 LLM 설정
    chat_agent_provider: str = os.getenv("CHAT_AGENT_PROVIDER", llm_provider).lower()
    chat_agent_model: str = os.getenv("CHAT_AGENT_MODEL", llm_model)
    chat_agent_temperature: float = float(os.getenv("CHAT_AGENT_TEMPERATURE", str(llm_temperature)))
    chat_agent_max_tokens: int = int(os.getenv("CHAT_AGENT_MAX_TOKENS", str(llm_max_tokens)))
    chat_agent_timeout: int = int(os.getenv("CHAT_AGENT_TIMEOUT", str(llm_timeout)))
    
    # DateParser 전용 LLM 설정
    date_parser_provider: str = os.getenv("DATE_PARSER_PROVIDER", llm_provider).lower()
    date_parser_model: str = os.getenv("DATE_PARSER_MODEL", llm_model)
    date_parser_temperature: float = float(os.getenv("DATE_PARSER_TEMPERATURE", "0.0"))
    date_parser_max_tokens: int = int(os.getenv("DATE_PARSER_MAX_TOKENS", "512"))
    date_parser_timeout: int = int(os.getenv("DATE_PARSER_TIMEOUT", "10"))
    
    # temporary_dislikes_extractor 전용 LLM 설정
    dislikes_extractor_provider: str = os.getenv("DISLIKES_EXTRACTOR_PROVIDER", llm_provider).lower()
    dislikes_extractor_model: str = os.getenv("DISLIKES_EXTRACTOR_MODEL", llm_model)
    dislikes_extractor_temperature: float = float(os.getenv("DISLIKES_EXTRACTOR_TEMPERATURE", "0.0"))
    dislikes_extractor_max_tokens: int = int(os.getenv("DISLIKES_EXTRACTOR_MAX_TOKENS", "512"))
    dislikes_extractor_timeout: int = int(os.getenv("DISLIKES_EXTRACTOR_TIMEOUT", "10"))
    
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
