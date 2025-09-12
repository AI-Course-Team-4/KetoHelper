"""
🔧 설정 로더 모듈
- YAML 설정 파일 로드
- 환경변수 치환
- 설정 유효성 검증
"""

import os
import yaml
import re
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, ValidationError
from loguru import logger
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class DatabaseConfig(BaseModel):
    """데이터베이스 설정 (Supabase)"""
    # Supabase 연결 정보
    supabase_url: Optional[str] = None
    supabase_anon_key: Optional[str] = None
    supabase_service_key: Optional[str] = None
    
    # PostgreSQL 직접 연결
    host: str = "localhost"
    port: int = 5432
    name: str = "postgres"
    user: str = "postgres"
    password: str = "password"
    
    # 연결 풀 설정
    pool_size: int = 5
    max_overflow: int = 10
    timeout: int = 30
    
    # Supabase 설정
    enable_realtime: bool = True
    enable_rest_api: bool = True


class CrawlerConfig(BaseModel):
    """크롤러 설정"""
    max_concurrent_tabs: int = 3
    default_timeout: int = 10
    page_timeout: int = 15
    rate_limits: Dict[str, float] = {"siksin": 0.5, "default": 0.3}
    retry: Dict[str, Any] = {
        "max_attempts": 3,
        "backoff_multiplier": 2,
        "initial_delay": 5,
        "max_delay": 300
    }
    user_agents: list = []
    playwright: Dict[str, Any] = {
        "headless": True,
        "slow_mo": 1000,
        "viewport": {"width": 1280, "height": 720}
    }


class ValidationConfig(BaseModel):
    """데이터 검증 설정"""
    restaurant_required_fields: list = ["name", "lat", "lng"]
    menu_required_fields: list = ["name"]
    quality_thresholds: Dict[str, float] = {"min_quality_score": 50, "min_confidence": 0.3}
    geo_bounds: Dict[str, float] = {
        "lat_min": 37.4, "lat_max": 37.7,
        "lng_min": 126.8, "lng_max": 127.2
    }
    price_bounds: Dict[str, int] = {"min": 1000, "max": 100000}
    text_limits: Dict[str, Any] = {}


class LoggingConfig(BaseModel):
    """로깅 설정"""
    level: str = "INFO"
    format: str = "[{time:YYYY-MM-DD HH:mm:ss}] {level} - {name} - {message}"
    files: Dict[str, str] = {
        "main": "logs/crawler.log",
        "error": "logs/error.log",
        "access": "logs/access.log"
    }
    rotation: Dict[str, Any] = {
        "size": "10 MB",
        "retention": "7 days",
        "backup_count": 5
    }


class AppConfig(BaseModel):
    """전체 애플리케이션 설정"""
    name: str = "Restaurant Crawler MVP"
    version: str = "1.0.0"
    debug: bool = False


class Config:
    """통합 설정 클래스"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.raw_config = {}
        self.app = AppConfig()
        self.database = DatabaseConfig()
        self.crawler = CrawlerConfig()
        self.validation = ValidationConfig()
        self.logging = LoggingConfig()
        
        # 사이트별 파서 설정
        self.parsers = {}
        
        # 설정 로드
        self._load_config()
        self._load_parser_configs()
        
    def _get_default_config_path(self) -> str:
        """기본 설정 파일 경로 반환"""
        current_dir = Path(__file__).parent.parent.parent
        return str(current_dir / "config" / "settings.yaml")
    
    def _load_config(self):
        """메인 설정 파일 로드"""
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"설정 파일을 찾을 수 없습니다: {self.config_path}")
                return
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 환경변수 치환
            content = self._substitute_env_vars(content)
            
            # YAML 파싱
            self.raw_config = yaml.safe_load(content)
            
            # 설정 객체 생성
            self._create_config_objects()
            
            logger.info(f"설정 파일 로드 완료: {self.config_path}")
            
        except yaml.YAMLError as e:
            logger.error(f"YAML 파싱 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"설정 파일 로드 실패: {e}")
            raise
    
    def _substitute_env_vars(self, content: str) -> str:
        """환경변수 치환 (${VAR} 또는 ${VAR:default} 형식)"""
        def replace_env(match):
            var_expr = match.group(1)
            if ':' in var_expr:
                var_name, default_value = var_expr.split(':', 1)
                return os.getenv(var_name, default_value)
            else:
                var_value = os.getenv(var_expr)
                if var_value is None:
                    logger.warning(f"환경변수를 찾을 수 없습니다: {var_expr}")
                    return match.group(0)  # 원본 텍스트 반환
                return var_value
        
        # ${VAR} 또는 ${VAR:default} 패턴 치환
        pattern = r'\$\{([^}]+)\}'
        return re.sub(pattern, replace_env, content)
    
    def _create_config_objects(self):
        """설정 객체 생성"""
        try:
            # 각 섹션별로 설정 객체 생성
            if 'app' in self.raw_config:
                self.app = AppConfig(**self.raw_config['app'])
                
            if 'database' in self.raw_config:
                self.database = DatabaseConfig(**self.raw_config['database'])
                
            if 'crawler' in self.raw_config:
                self.crawler = CrawlerConfig(**self.raw_config['crawler'])
                
            if 'validation' in self.raw_config:
                self.validation = ValidationConfig(**self.raw_config['validation'])
                
            if 'logging' in self.raw_config:
                self.logging = LoggingConfig(**self.raw_config['logging'])
                
        except ValidationError as e:
            logger.error(f"설정 검증 실패: {e}")
            raise
    
    def _load_parser_configs(self):
        """사이트별 파서 설정 로드"""
        parsers_dir = Path(self.config_path).parent / "parsers"
        
        if not parsers_dir.exists():
            logger.warning(f"파서 설정 디렉토리를 찾을 수 없습니다: {parsers_dir}")
            return
            
        for config_file in parsers_dir.glob("*.yaml"):
            site_name = config_file.stem
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    parser_config = yaml.safe_load(f)
                
                self.parsers[site_name] = parser_config
                logger.debug(f"파서 설정 로드: {site_name}")
                
            except Exception as e:
                logger.error(f"파서 설정 로드 실패 ({site_name}): {e}")
    
    def get_parser_config(self, site: str) -> Dict[str, Any]:
        """특정 사이트의 파서 설정 반환"""
        if site not in self.parsers:
            logger.error(f"파서 설정을 찾을 수 없습니다: {site}")
            raise ValueError(f"Parser config not found for site: {site}")
        
        return self.parsers[site]
    
    def get_rate_limit(self, site: str) -> float:
        """사이트별 속도 제한 반환"""
        return self.crawler.rate_limits.get(site, self.crawler.rate_limits.get("default", 0.3))
    
    def get_database_url(self) -> str:
        """데이터베이스 연결 URL 생성"""
        return (
            f"postgresql://{self.database.user}:{self.database.password}@"
            f"{self.database.host}:{self.database.port}/{self.database.name}"
        )
    
    def get_async_database_url(self) -> str:
        """비동기 데이터베이스 연결 URL 생성"""
        return (
            f"postgresql+asyncpg://{self.database.user}:{self.database.password}@"
            f"{self.database.host}:{self.database.port}/{self.database.name}"
        )
    
    def get_supabase_url(self) -> Optional[str]:
        """Supabase URL 반환"""
        return self.database.supabase_url
    
    def get_supabase_anon_key(self) -> Optional[str]:
        """Supabase Anon Key 반환"""
        return self.database.supabase_anon_key
        
    def get_supabase_service_key(self) -> Optional[str]:
        """Supabase Service Key 반환"""
        return self.database.supabase_service_key
    
    def is_supabase_enabled(self) -> bool:
        """Supabase 사용 여부 확인"""
        return (self.database.supabase_url is not None and 
                self.database.supabase_anon_key is not None)
    
    def get_user_agent(self) -> str:
        """사용자 에이전트 반환 (로테이션)"""
        if not self.crawler.user_agents:
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        import random
        return random.choice(self.crawler.user_agents)
    
    def is_debug(self) -> bool:
        """디버그 모드 확인"""
        return self.app.debug
    
    def get_log_level(self) -> str:
        """로그 레벨 반환"""
        return self.logging.level
    
    def validate_coordinates(self, lat: float, lng: float) -> bool:
        """좌표 유효성 검증"""
        bounds = self.validation.geo_bounds
        return (bounds["lat_min"] <= lat <= bounds["lat_max"] and
                bounds["lng_min"] <= lng <= bounds["lng_max"])
    
    def validate_price(self, price: int) -> bool:
        """가격 유효성 검증"""
        bounds = self.validation.price_bounds
        return bounds["min"] <= price <= bounds["max"]
    
    def reload(self):
        """설정 파일 다시 로드"""
        logger.info("설정 파일을 다시 로드합니다...")
        self._load_config()
        self._load_parser_configs()
        logger.info("설정 파일 로드 완료")
    
    def __repr__(self) -> str:
        return f"<Config app={self.app.name} v={self.app.version}>"


# 전역 설정 인스턴스
config = None


def get_config(config_path: Optional[str] = None) -> Config:
    """전역 설정 인스턴스 반환 (싱글톤 패턴)"""
    global config
    
    if config is None:
        config = Config(config_path)
    
    return config


def reload_config():
    """설정 다시 로드"""
    global config
    if config:
        config.reload()


# 편의 함수들
def get_database_url() -> str:
    """데이터베이스 URL 반환"""
    return get_config().get_database_url()


def get_async_database_url() -> str:
    """비동기 데이터베이스 URL 반환"""
    return get_config().get_async_database_url()


def get_parser_config(site: str) -> Dict[str, Any]:
    """파서 설정 반환"""
    return get_config().get_parser_config(site)


def get_rate_limit(site: str) -> float:
    """사이트별 속도 제한 반환"""
    return get_config().get_rate_limit(site)


if __name__ == "__main__":
    # 테스트 코드
    try:
        cfg = get_config()
        print(f"앱 이름: {cfg.app.name}")
        print(f"데이터베이스 URL: {cfg.get_database_url()}")
        print(f"사이트별 속도 제한: {cfg.get_rate_limit('siksin')}")
        print("설정 로드 성공!")
    except Exception as e:
        print(f"설정 로드 실패: {e}")