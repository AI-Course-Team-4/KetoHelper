"""
핵심 설정 관리 시스템
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv
import json

# 환경 변수 로드
load_dotenv()

@dataclass
class DatabaseConfig:
    """데이터베이스 설정"""
    host: str = "localhost"
    port: int = 5432
    database: str = "restaurant_db"
    username: str = "postgres"
    password: str = ""
    pool_size: int = 20
    max_overflow: int = 10
    timeout: int = 30

    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "restaurant_db"),
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            pool_size=int(os.getenv("DB_POOL_SIZE", "20")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
            timeout=int(os.getenv("DB_TIMEOUT", "30"))
        )

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class SupabaseConfig:
    """Supabase 설정 (대안 DB)"""
    url: str = ""
    anon_key: str = ""
    service_key: str = ""

    @classmethod
    def from_env(cls) -> 'SupabaseConfig':
        return cls(
            url=os.getenv("SUPABASE_URL", ""),
            anon_key=os.getenv("SUPABASE_ANON_KEY", ""),
            service_key=os.getenv("SUPABASE_SERVICE_KEY", "")
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.anon_key)

@dataclass
class CrawlerConfig:
    """크롤링 설정"""
    rate_limit: float = 0.5
    timeout: int = 30
    retry_count: int = 3
    user_agent: str = "RestaurantBot/1.0"
    max_concurrent: int = 5
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 900  # 15분

    @classmethod
    def from_env(cls) -> 'CrawlerConfig':
        return cls(
            rate_limit=float(os.getenv("CRAWLER_RATE_LIMIT", "0.5")),
            timeout=int(os.getenv("CRAWLER_TIMEOUT", "30")),
            retry_count=int(os.getenv("CRAWLER_RETRY", "3")),
            user_agent=os.getenv("USER_AGENT", "RestaurantBot/1.0"),
            max_concurrent=int(os.getenv("CRAWLER_MAX_CONCURRENT", "5")),
            circuit_breaker_threshold=int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5")),
            circuit_breaker_timeout=int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "900"))
        )

@dataclass
class ExternalAPIConfig:
    """외부 API 설정"""
    kakao_rest_api_key: str = ""
    naver_client_id: str = ""
    naver_client_secret: str = ""

    @classmethod
    def from_env(cls) -> 'ExternalAPIConfig':
        return cls(
            kakao_rest_api_key=os.getenv("KAKAO_REST_API_KEY", ""),
            naver_client_id=os.getenv("NAVER_CLIENT_ID", ""),
            naver_client_secret=os.getenv("NAVER_CLIENT_SECRET", "")
        )

@dataclass
class CacheConfig:
    """캐시 설정"""
    enabled: bool = True
    strategy: str = "file"  # 'file', 'memory', 'redis'
    ttl: int = 3600
    max_size: int = 1000
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    @classmethod
    def from_env(cls) -> 'CacheConfig':
        return cls(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            strategy=os.getenv("CACHE_STRATEGY", "file"),
            ttl=int(os.getenv("CACHE_TTL", "3600")),
            max_size=int(os.getenv("CACHE_MAX_SIZE", "1000")),
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", "6379")),
            redis_password=os.getenv("REDIS_PASSWORD", ""),
            redis_db=int(os.getenv("REDIS_DB", "0"))
        )

@dataclass
class LoggingConfig:
    """로깅 설정"""
    level: str = "INFO"
    format: str = "json"  # 'json', 'text'
    file_enabled: bool = True
    console_enabled: bool = True
    file_path: str = "logs/app.log"
    max_file_size: str = "100MB"
    backup_count: int = 5

    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO"),
            format=os.getenv("LOG_FORMAT", "json"),
            file_enabled=os.getenv("LOG_FILE_ENABLED", "true").lower() == "true",
            console_enabled=os.getenv("LOG_CONSOLE_ENABLED", "true").lower() == "true",
            file_path=os.getenv("LOG_FILE_PATH", "logs/app.log"),
            max_file_size=os.getenv("LOG_MAX_FILE_SIZE", "100MB"),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5"))
        )

@dataclass
class KetoScoringConfig:
    """키토 점수화 설정"""
    rule_version: str = "v1.0"
    confidence_threshold: float = 0.5
    review_threshold: float = 0.4
    keywords_path: str = "data/config/keywords"
    rules_path: str = "data/config/rules"

    @classmethod
    def from_env(cls) -> 'KetoScoringConfig':
        return cls(
            rule_version=os.getenv("KETO_RULE_VERSION", "v1.0"),
            confidence_threshold=float(os.getenv("KETO_CONFIDENCE_THRESHOLD", "0.5")),
            review_threshold=float(os.getenv("KETO_REVIEW_THRESHOLD", "0.4")),
            keywords_path=os.getenv("KETO_KEYWORDS_PATH", "data/config/keywords"),
            rules_path=os.getenv("KETO_RULES_PATH", "data/config/rules")
        )

class Settings:
    """중앙 설정 관리 클래스"""

    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"

        # 하위 설정들
        self.database = DatabaseConfig.from_env()
        self.supabase = SupabaseConfig.from_env()
        self.crawler = CrawlerConfig.from_env()
        self.external_apis = ExternalAPIConfig.from_env()
        self.cache = CacheConfig.from_env()
        self.logging = LoggingConfig.from_env()
        self.keto_scoring = KetoScoringConfig.from_env()

        # 디렉토리 생성
        self._ensure_directories()

    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        directories = [
            self.data_dir,
            self.data_dir / "raw",
            self.data_dir / "processed",
            self.data_dir / "cache",
            self.data_dir / "config" / "keywords",
            self.data_dir / "config" / "rules",
            self.data_dir / "reports",
            self.base_dir / "logs"
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"

    def get_data_path(self, *paths) -> Path:
        """데이터 디렉토리 경로 생성"""
        return self.data_dir.joinpath(*paths)

    def get_config_path(self, *paths) -> Path:
        """설정 디렉토리 경로 생성"""
        return self.data_dir.joinpath("config", *paths)

    def to_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 변환"""
        return {
            "environment": self.environment,
            "base_dir": str(self.base_dir),
            "data_dir": str(self.data_dir),
            "database": self.database.__dict__,
            "supabase": self.supabase.__dict__,
            "crawler": self.crawler.__dict__,
            "external_apis": self.external_apis.__dict__,
            "cache": self.cache.__dict__,
            "logging": self.logging.__dict__,
            "keto_scoring": self.keto_scoring.__dict__
        }

    def save_to_file(self, file_path: str):
        """설정을 파일로 저장"""
        config_dict = self.to_dict()

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

    def validate(self) -> List[str]:
        """설정 검증"""
        errors = []

        # 데이터베이스 설정 검증
        if not self.database.host:
            errors.append("Database host is required")
        if not self.database.database:
            errors.append("Database name is required")
        if not self.database.username:
            errors.append("Database username is required")

        # Supabase 대안 체크
        if not self.database.password and not self.supabase.is_configured:
            errors.append("Either database password or Supabase configuration is required")

        # 외부 API 키 체크 (경고만)
        if not self.external_apis.kakao_rest_api_key:
            errors.append("Warning: Kakao API key not configured - geocoding will be disabled")

        return errors

# 글로벌 설정 인스턴스
settings = Settings()

# 개발 편의용 함수들
def get_database_url() -> str:
    """데이터베이스 URL 반환"""
    if settings.supabase.is_configured:
        return settings.supabase.url
    return settings.database.connection_string

def is_cache_enabled() -> bool:
    """캐시 활성화 여부"""
    return settings.cache.enabled

def get_log_level() -> str:
    """로그 레벨 반환"""
    return settings.logging.level