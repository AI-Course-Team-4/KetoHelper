# 최적화된 시스템 아키텍처 설계

## 1. 전체 시스템 아키텍처 개요

### 1.1 레이어드 아키텍처 (Layered Architecture)
```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Web UI    │  │   CLI Tool  │  │   API REST  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                   Business Logic Layer                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Scoring   │  │  Analytics  │  │   Reports   │     │
│  │   Engine    │  │   Engine    │  │   Engine    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                     Service Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Crawler   │  │   Data      │  │   Cache     │     │
│  │   Service   │  │   Service   │  │   Service   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                   Data Access Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  PostgreSQL │  │  File Cache │  │  External   │     │
│  │  Repository │  │  Repository │  │  APIs       │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

### 1.2 마이크로서비스 지향 모듈 설계
```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Crawler    │    │   Processor  │    │   Scorer     │
│   Module     │───▶│   Module     │───▶│   Module     │
│              │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Raw Data     │    │ Normalized   │    │ Scored Data  │
│ Storage      │    │ Data Storage │    │ Storage      │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 2. 모듈 구조 설계

### 2.1 프로젝트 구조
```
final_ETL/
├── config/                          # 설정 관리
│   ├── __init__.py
│   ├── settings.py                  # 전역 설정
│   ├── database.py                  # DB 설정
│   └── sources.yaml                 # 크롤링 소스 설정
│
├── core/                            # 핵심 비즈니스 로직
│   ├── __init__.py
│   ├── domain/                      # 도메인 모델
│   │   ├── __init__.py
│   │   ├── restaurant.py
│   │   ├── menu.py
│   │   └── score.py
│   ├── interfaces/                  # 추상 인터페이스
│   │   ├── __init__.py
│   │   ├── crawler_interface.py
│   │   ├── processor_interface.py
│   │   └── scorer_interface.py
│   └── exceptions.py                # 커스텀 예외
│
├── services/                        # 서비스 레이어
│   ├── __init__.py
│   ├── crawler/                     # 크롤링 서비스
│   │   ├── __init__.py
│   │   ├── base_crawler.py
│   │   ├── diningcode_crawler.py
│   │   ├── siksin_crawler.py
│   │   └── crawler_factory.py
│   ├── processor/                   # 데이터 처리 서비스
│   │   ├── __init__.py
│   │   ├── data_processor.py
│   │   ├── geocoding_service.py
│   │   └── deduplication_service.py
│   ├── scorer/                      # 점수화 서비스
│   │   ├── __init__.py
│   │   ├── keto_scorer.py
│   │   ├── rule_engine.py
│   │   └── keyword_matcher.py
│   └── cache/                       # 캐시 서비스
│       ├── __init__.py
│       ├── cache_manager.py
│       └── cache_strategies.py
│
├── infrastructure/                  # 인프라 레이어
│   ├── __init__.py
│   ├── database/                    # 데이터베이스 접근
│   │   ├── __init__.py
│   │   ├── connection.py
│   │   ├── repositories/
│   │   │   ├── restaurant_repository.py
│   │   │   ├── menu_repository.py
│   │   │   └── score_repository.py
│   │   └── migrations/
│   │       ├── 001_create_tables.sql
│   │       └── 002_add_keto_fields.sql
│   ├── external/                    # 외부 API
│   │   ├── __init__.py
│   │   ├── kakao_geocoding.py
│   │   └── rate_limiter.py
│   └── storage/                     # 파일 저장소
│       ├── __init__.py
│       ├── file_manager.py
│       └── data_serializer.py
│
├── application/                     # 애플리케이션 레이어
│   ├── __init__.py
│   ├── orchestrators/               # 워크플로우 관리
│   │   ├── __init__.py
│   │   ├── etl_orchestrator.py
│   │   └── scoring_orchestrator.py
│   ├── commands/                    # 명령 패턴
│   │   ├── __init__.py
│   │   ├── crawl_command.py
│   │   ├── process_command.py
│   │   └── score_command.py
│   └── queries/                     # 쿼리 패턴
│       ├── __init__.py
│       ├── restaurant_queries.py
│       └── analytics_queries.py
│
├── presentation/                    # 프레젠테이션 레이어
│   ├── __init__.py
│   ├── cli/                         # CLI 인터페이스
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── commands/
│   ├── api/                         # REST API (선택적)
│   │   ├── __init__.py
│   │   ├── app.py
│   │   └── routes/
│   └── web/                         # 웹 UI (선택적)
│
├── utils/                           # 유틸리티
│   ├── __init__.py
│   ├── logging_config.py
│   ├── validators.py
│   ├── helpers.py
│   └── decorators.py
│
├── data/                            # 데이터 저장소
│   ├── raw/                         # 원본 데이터
│   ├── processed/                   # 처리된 데이터
│   ├── cache/                       # 캐시 데이터
│   ├── config/                      # 설정 데이터
│   │   ├── keywords/
│   │   │   ├── high_carb.json
│   │   │   ├── keto_friendly.json
│   │   │   ├── substitutions.json
│   │   │   └── negations.json
│   │   └── rules/
│   │       └── keto_scoring_v1.json
│   └── reports/                     # 리포트 출력
│
├── tests/                           # 테스트
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── scripts/                         # 스크립트
│   ├── setup_database.py
│   ├── migrate.py
│   └── backup.py
│
├── requirements.txt
├── requirements-dev.txt
├── setup.py
├── .env.example
└── README.md
```

## 3. 핵심 컴포넌트 설계

### 3.1 Configuration Management
```python
# config/settings.py
from dataclasses import dataclass
from typing import Dict, Any
import os
from pathlib import Path

@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    username: str
    password: str

@dataclass
class CrawlerConfig:
    rate_limit: float
    timeout: int
    retry_count: int
    user_agent: str

@dataclass
class CacheConfig:
    enabled: bool
    ttl: int
    max_size: int
    strategy: str  # 'memory', 'file', 'redis'

class Settings:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"

        # Environment-based configuration
        self.environment = os.getenv("ENVIRONMENT", "development")

        # Database configuration
        self.database = DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "restaurant_db"),
            username=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "")
        )

        # Crawler configuration
        self.crawler = CrawlerConfig(
            rate_limit=float(os.getenv("CRAWLER_RATE_LIMIT", "0.5")),
            timeout=int(os.getenv("CRAWLER_TIMEOUT", "30")),
            retry_count=int(os.getenv("CRAWLER_RETRY", "3")),
            user_agent=os.getenv("USER_AGENT", "RestaurantBot/1.0")
        )

        # Cache configuration
        self.cache = CacheConfig(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            ttl=int(os.getenv("CACHE_TTL", "3600")),
            max_size=int(os.getenv("CACHE_MAX_SIZE", "1000")),
            strategy=os.getenv("CACHE_STRATEGY", "file")
        )

# Singleton pattern
settings = Settings()
```

### 3.2 Domain Models
```python
# core/domain/restaurant.py
from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import uuid

@dataclass
class Restaurant:
    id: uuid.UUID
    name: str
    phone: Optional[str]
    addr_original: str
    addr_norm: Optional[str]
    lat: Optional[Decimal]
    lng: Optional[Decimal]
    geohash6: Optional[str]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self):
        if self.id is None:
            self.id = uuid.uuid4()

@dataclass
class Menu:
    id: uuid.UUID
    restaurant_id: uuid.UUID
    name: str
    name_norm: Optional[str]
    price: Optional[int]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

@dataclass
class KetoScore:
    id: uuid.UUID
    menu_id: uuid.UUID
    score: int
    reasons_json: dict
    needs_review: bool
    substitution_tags: Optional[dict]
    override_reason: Optional[str]
    final_carb_base: Optional[str]
    ingredients_confidence: Optional[Decimal]
    rule_version: str
    created_at: datetime
```

### 3.3 Repository Pattern
```python
# infrastructure/database/repositories/restaurant_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from core.domain.restaurant import Restaurant

class RestaurantRepositoryInterface(ABC):
    @abstractmethod
    async def save(self, restaurant: Restaurant) -> Restaurant:
        pass

    @abstractmethod
    async def find_by_id(self, restaurant_id: str) -> Optional[Restaurant]:
        pass

    @abstractmethod
    async def find_by_canonical_key(self, name: str, geohash: str) -> Optional[Restaurant]:
        pass

    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[Restaurant]:
        pass

class PostgresRestaurantRepository(RestaurantRepositoryInterface):
    def __init__(self, connection_pool):
        self.pool = connection_pool

    async def save(self, restaurant: Restaurant) -> Restaurant:
        query = """
        INSERT INTO restaurants (id, name, phone, addr_original, addr_norm, lat, lng, geohash6)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (id) DO UPDATE SET
            name = EXCLUDED.name,
            phone = EXCLUDED.phone,
            addr_original = EXCLUDED.addr_original,
            addr_norm = EXCLUDED.addr_norm,
            lat = EXCLUDED.lat,
            lng = EXCLUDED.lng,
            geohash6 = EXCLUDED.geohash6,
            updated_at = NOW()
        RETURNING *
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                restaurant.id,
                restaurant.name,
                restaurant.phone,
                restaurant.addr_original,
                restaurant.addr_norm,
                restaurant.lat,
                restaurant.lng,
                restaurant.geohash6
            )
            return self._row_to_restaurant(row)
```

### 3.4 Service Layer with Dependency Injection
```python
# services/crawler/base_crawler.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.interfaces.crawler_interface import CrawlerInterface
from infrastructure.external.rate_limiter import RateLimiter

class BaseCrawler(CrawlerInterface):
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.session = None

    async def __aenter__(self):
        await self.setup_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup_session()

    @abstractmethod
    async def crawl_restaurant_list(self, query: str) -> List[str]:
        """크롤링할 식당 URL 목록 반환"""
        pass

    @abstractmethod
    async def crawl_restaurant_detail(self, url: str) -> Dict[str, Any]:
        """식당 상세 정보 크롤링"""
        pass

    async def crawl_with_rate_limit(self, url: str) -> Dict[str, Any]:
        await self.rate_limiter.wait()
        return await self.crawl_restaurant_detail(url)
```

### 3.5 Command and Query Separation (CQRS)
```python
# application/commands/crawl_command.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CrawlCommand:
    source_name: str
    keywords: List[str]
    max_pages: int = 5
    force_new: bool = False
    use_cache: bool = True

class CrawlCommandHandler:
    def __init__(
        self,
        crawler_factory,
        data_processor,
        cache_manager
    ):
        self.crawler_factory = crawler_factory
        self.data_processor = data_processor
        self.cache_manager = cache_manager

    async def handle(self, command: CrawlCommand) -> Dict[str, Any]:
        # Check cache first
        if command.use_cache and not command.force_new:
            cached_data = await self.cache_manager.get_recent_data(
                command.source_name,
                max_age_hours=24
            )
            if cached_data:
                return cached_data

        # Create crawler
        crawler = self.crawler_factory.create(command.source_name)

        # Execute crawling
        async with crawler:
            raw_data = await crawler.crawl_restaurants(command.keywords)

        # Process data
        processed_data = await self.data_processor.process(raw_data)

        # Cache results
        await self.cache_manager.store_data(
            command.source_name,
            processed_data
        )

        return processed_data
```

## 4. 데이터 흐름 설계

### 4.1 ETL Pipeline Architecture
```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Extract    │    │  Transform   │    │     Load     │
│              │    │              │    │              │
│ • Web Scrape │───▶│ • Normalize  │───▶│ • Validate   │
│ • Cache Check│    │ • Geocoding  │    │ • Dedup      │
│ • Rate Limit │    │ • Clean Text │    │ • Store DB   │
└──────────────┘    └──────────────┘    └──────────────┘
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Raw Data    │    │ Intermediate │    │ Final Tables │
│  JSON Files  │    │    Data      │    │ PostgreSQL   │
└──────────────┘    └──────────────┘    └──────────────┘
```

### 4.2 Scoring Pipeline Architecture
```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Menu Data   │    │ Rule Engine  │    │ Score Output │
│              │    │              │    │              │
│ • Name       │───▶│ • Keywords   │───▶│ • Score      │
│ • Description│    │ • Patterns   │    │ • Confidence │
│ • Category   │    │ • Weights    │    │ • Reasons    │
└──────────────┘    └──────────────┘    └──────────────┘
       │                     │                     │
       ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ JSON Config  │    │ Processing   │    │ keto_scores  │
│ Rule Files   │    │ Memory       │    │ Table        │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 5. 확장성 고려사항

### 5.1 Horizontal Scaling Points
```
┌─────────────────────────────────────────────────────┐
│                Load Balancer                        │
└─────────────────────────────────────────────────────┘
              │              │              │
┌─────────────▼─┐   ┌────────▼──┐   ┌───────▼────┐
│  Crawler      │   │ Processor │   │  Scorer    │
│  Service 1    │   │ Service 1 │   │ Service 1  │
└───────────────┘   └───────────┘   └────────────┘
┌───────────────┐   ┌───────────┐   ┌────────────┐
│  Crawler      │   │ Processor │   │  Scorer    │
│  Service 2    │   │ Service 2 │   │ Service 2  │
└───────────────┘   └───────────┘   └────────────┘
              │              │              │
        ┌─────▼──────────────▼──────────────▼─────┐
        │            Shared Database              │
        │              (PostgreSQL)               │
        └─────────────────────────────────────────┘
```

### 5.2 Plugin Architecture for Sources
```python
# services/crawler/crawler_factory.py
from typing import Dict, Type
from core.interfaces.crawler_interface import CrawlerInterface

class CrawlerFactory:
    def __init__(self):
        self._crawlers: Dict[str, Type[CrawlerInterface]] = {}

    def register(self, source_name: str, crawler_class: Type[CrawlerInterface]):
        """새로운 크롤러 등록"""
        self._crawlers[source_name] = crawler_class

    def create(self, source_name: str, **kwargs) -> CrawlerInterface:
        """크롤러 인스턴스 생성"""
        if source_name not in self._crawlers:
            raise ValueError(f"Unknown crawler source: {source_name}")

        return self._crawlers[source_name](**kwargs)

    def list_sources(self) -> List[str]:
        """사용 가능한 소스 목록"""
        return list(self._crawlers.keys())

# Usage
factory = CrawlerFactory()
factory.register("diningcode", DiningcodeCrawler)
factory.register("siksin", SiksinCrawler)
factory.register("mangoplate", MangoPlateCrawler)  # 향후 추가
```

## 6. 품질 보증 및 모니터링

### 6.1 Health Check System
```python
# utils/health_checker.py
from typing import Dict, Any
from enum import Enum

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthChecker:
    def __init__(self, db_pool, cache_manager, external_apis):
        self.db_pool = db_pool
        self.cache_manager = cache_manager
        self.external_apis = external_apis

    async def check_health(self) -> Dict[str, Any]:
        checks = {
            "database": await self._check_database(),
            "cache": await self._check_cache(),
            "external_apis": await self._check_external_apis(),
            "disk_space": await self._check_disk_space()
        }

        overall_status = self._determine_overall_status(checks)

        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks
        }
```

### 6.2 Metrics and Observability
```python
# utils/metrics.py
from dataclasses import dataclass
from typing import Dict, Any
import time

@dataclass
class PerformanceMetrics:
    operation: str
    duration: float
    success: bool
    error_type: str = None

class MetricsCollector:
    def __init__(self):
        self.metrics = []

    def record_operation(self, operation: str, duration: float, success: bool, error_type: str = None):
        metric = PerformanceMetrics(
            operation=operation,
            duration=duration,
            success=success,
            error_type=error_type
        )
        self.metrics.append(metric)

    def get_summary(self) -> Dict[str, Any]:
        if not self.metrics:
            return {}

        success_count = sum(1 for m in self.metrics if m.success)
        total_count = len(self.metrics)
        avg_duration = sum(m.duration for m in self.metrics) / total_count

        return {
            "total_operations": total_count,
            "success_rate": success_count / total_count,
            "average_duration": avg_duration,
            "error_types": self._count_error_types()
        }
```

이 아키텍처는 확장성, 유지보수성, 테스트 가능성을 고려하여 설계되었습니다. 각 레이어가 명확히 분리되어 있어 향후 요구사항 변경이나 새로운 기능 추가에 유연하게 대응할 수 있습니다.