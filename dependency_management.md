# 의존성 관리 및 모듈 구조 설계

## 1. 의존성 주입 (Dependency Injection) 설계

### 1.1 DI Container 구현
```python
# infrastructure/di_container.py
from typing import TypeVar, Type, Callable, Dict, Any
from abc import ABC, abstractmethod
import inspect

T = TypeVar('T')

class Container:
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}

    def register_singleton(self, interface: Type[T], implementation: Type[T]) -> None:
        """싱글톤 서비스 등록"""
        self._services[interface] = ('singleton', implementation)

    def register_transient(self, interface: Type[T], implementation: Type[T]) -> None:
        """일시적 서비스 등록 (매번 새 인스턴스)"""
        self._services[interface] = ('transient', implementation)

    def register_factory(self, interface: Type[T], factory: Callable[[], T]) -> None:
        """팩토리 함수 등록"""
        self._factories[interface] = factory

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """인스턴스 직접 등록"""
        self._singletons[interface] = instance

    def resolve(self, interface: Type[T]) -> T:
        """서비스 해결"""
        # 팩토리 함수가 있으면 우선 사용
        if interface in self._factories:
            return self._factories[interface]()

        # 등록된 인스턴스가 있으면 반환
        if interface in self._singletons:
            return self._singletons[interface]

        # 서비스 등록 정보 확인
        if interface not in self._services:
            raise ValueError(f"Service {interface} not registered")

        service_type, implementation = self._services[interface]

        if service_type == 'singleton':
            if interface not in self._singletons:
                self._singletons[interface] = self._create_instance(implementation)
            return self._singletons[interface]
        else:  # transient
            return self._create_instance(implementation)

    def _create_instance(self, implementation: Type[T]) -> T:
        """생성자 주입을 통한 인스턴스 생성"""
        signature = inspect.signature(implementation.__init__)
        args = {}

        for param_name, param in signature.parameters.items():
            if param_name == 'self':
                continue

            if param.annotation != inspect.Parameter.empty:
                args[param_name] = self.resolve(param.annotation)

        return implementation(**args)

# Global container instance
container = Container()
```

### 1.2 서비스 등록 설정
```python
# config/di_config.py
from infrastructure.di_container import container
from services.crawler.crawler_factory import CrawlerFactory
from services.processor.data_processor import DataProcessor
from services.scorer.keto_scorer import KetoScorer
from infrastructure.database.connection import DatabasePool
from infrastructure.external.kakao_geocoding import KakaoGeocodingService
from services.cache.cache_manager import CacheManager

def configure_dependencies():
    """의존성 등록 설정"""

    # 데이터베이스 연결
    container.register_singleton(
        DatabasePool,
        DatabasePool
    )

    # 외부 서비스
    container.register_singleton(
        KakaoGeocodingService,
        KakaoGeocodingService
    )

    # 캐시 관리자
    container.register_singleton(
        CacheManager,
        CacheManager
    )

    # 크롤러 팩토리
    container.register_singleton(
        CrawlerFactory,
        CrawlerFactory
    )

    # 데이터 처리기
    container.register_transient(
        DataProcessor,
        DataProcessor
    )

    # 점수화 엔진
    container.register_transient(
        KetoScorer,
        KetoScorer
    )

def setup_factories():
    """팩토리 함수 설정"""
    def create_database_pool():
        from config.settings import settings
        return DatabasePool(settings.database)

    container.register_factory(DatabasePool, create_database_pool)
```

## 2. 모듈 간 인터페이스 정의

### 2.1 핵심 인터페이스
```python
# core/interfaces/crawler_interface.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator

class CrawlerInterface(ABC):
    @abstractmethod
    async def crawl_restaurant_list(self, keywords: List[str]) -> List[str]:
        """식당 URL 목록 크롤링"""
        pass

    @abstractmethod
    async def crawl_restaurant_detail(self, url: str) -> Dict[str, Any]:
        """식당 상세 정보 크롤링"""
        pass

    @abstractmethod
    async def crawl_batch(self, urls: List[str]) -> AsyncIterator[Dict[str, Any]]:
        """배치 크롤링"""
        pass

# core/interfaces/processor_interface.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from core.domain.restaurant import Restaurant, Menu

class ProcessorInterface(ABC):
    @abstractmethod
    async def process_restaurant_data(self, raw_data: Dict[str, Any]) -> Restaurant:
        """원시 데이터를 Restaurant 객체로 변환"""
        pass

    @abstractmethod
    async def process_menu_data(self, raw_menus: List[Dict], restaurant_id: str) -> List[Menu]:
        """원시 메뉴 데이터를 Menu 객체 리스트로 변환"""
        pass

    @abstractmethod
    async def deduplicate_restaurants(self, restaurants: List[Restaurant]) -> List[Restaurant]:
        """중복 식당 제거"""
        pass

# core/interfaces/scorer_interface.py
from abc import ABC, abstractmethod
from core.domain.menu import Menu
from core.domain.score import KetoScore

class ScorerInterface(ABC):
    @abstractmethod
    async def calculate_score(self, menu: Menu) -> KetoScore:
        """메뉴의 키토 점수 계산"""
        pass

    @abstractmethod
    async def batch_score(self, menus: List[Menu]) -> List[KetoScore]:
        """메뉴 리스트 일괄 점수 계산"""
        pass
```

### 2.2 Repository 인터페이스
```python
# core/interfaces/repository_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional, Generic, TypeVar
from uuid import UUID

T = TypeVar('T')

class RepositoryInterface(Generic[T], ABC):
    @abstractmethod
    async def save(self, entity: T) -> T:
        pass

    @abstractmethod
    async def find_by_id(self, entity_id: UUID) -> Optional[T]:
        pass

    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        pass

class RestaurantRepositoryInterface(RepositoryInterface[Restaurant]):
    @abstractmethod
    async def find_by_canonical_key(self, canonical_key: str) -> Optional[Restaurant]:
        pass

    @abstractmethod
    async def find_nearby(self, lat: float, lng: float, radius_km: float) -> List[Restaurant]:
        pass

class MenuRepositoryInterface(RepositoryInterface[Menu]):
    @abstractmethod
    async def find_by_restaurant_id(self, restaurant_id: UUID) -> List[Menu]:
        pass

    @abstractmethod
    async def search_by_name(self, name: str, limit: int = 50) -> List[Menu]:
        pass
```

## 3. 모듈 초기화 및 설정

### 3.1 애플리케이션 팩토리 패턴
```python
# application/app_factory.py
from typing import Dict, Any
from config.di_config import configure_dependencies, setup_factories
from infrastructure.database.connection import DatabasePool
from services.crawler.crawler_factory import CrawlerFactory
from utils.logging_config import setup_logging

class Application:
    def __init__(self):
        self.is_initialized = False
        self.db_pool: DatabasePool = None
        self.crawler_factory: CrawlerFactory = None

    async def initialize(self, config: Dict[str, Any] = None):
        """애플리케이션 초기화"""
        if self.is_initialized:
            return

        # 로깅 설정
        setup_logging(config.get('logging', {}))

        # 의존성 주입 설정
        configure_dependencies()
        setup_factories()

        # 데이터베이스 초기화
        from infrastructure.di_container import container
        self.db_pool = container.resolve(DatabasePool)
        await self.db_pool.initialize()

        # 크롤러 팩토리 설정
        self.crawler_factory = container.resolve(CrawlerFactory)
        self._register_crawlers()

        self.is_initialized = True

    def _register_crawlers(self):
        """크롤러 등록"""
        from services.crawler.diningcode_crawler import DiningcodeCrawler
        from services.crawler.siksin_crawler import SiksinCrawler

        self.crawler_factory.register('diningcode', DiningcodeCrawler)
        self.crawler_factory.register('siksin', SiksinCrawler)

    async def cleanup(self):
        """애플리케이션 정리"""
        if self.db_pool:
            await self.db_pool.close()

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

# 글로벌 애플리케이션 인스턴스
app = Application()
```

### 3.2 설정 기반 초기화
```python
# config/module_config.py
from dataclasses import dataclass
from typing import Dict, Any, List

@dataclass
class CrawlerModuleConfig:
    enabled_sources: List[str]
    rate_limits: Dict[str, float]
    timeout_settings: Dict[str, int]
    retry_settings: Dict[str, int]

@dataclass
class ProcessorModuleConfig:
    geocoding_enabled: bool
    geocoding_provider: str
    deduplication_enabled: bool
    cache_enabled: bool

@dataclass
class ScorerModuleConfig:
    rule_version: str
    keywords_path: str
    confidence_threshold: float
    needs_review_threshold: float

@dataclass
class ModuleConfiguration:
    crawler: CrawlerModuleConfig
    processor: ProcessorModuleConfig
    scorer: ScorerModuleConfig

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ModuleConfiguration':
        return cls(
            crawler=CrawlerModuleConfig(**config_dict.get('crawler', {})),
            processor=ProcessorModuleConfig(**config_dict.get('processor', {})),
            scorer=ScorerModuleConfig(**config_dict.get('scorer', {}))
        )

    @classmethod
    def load_from_file(cls, config_path: str) -> 'ModuleConfiguration':
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)
```

## 4. 오케스트레이션 레이어

### 4.1 워크플로우 매니저
```python
# application/orchestrators/workflow_manager.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
from uuid import UUID, uuid4

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowStep:
    id: UUID
    name: str
    function: callable
    args: tuple
    kwargs: dict
    depends_on: List[UUID]
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Any = None
    error: Exception = None

class WorkflowManager:
    def __init__(self):
        self.steps: Dict[UUID, WorkflowStep] = {}
        self.execution_order: List[UUID] = []

    def add_step(
        self,
        name: str,
        function: callable,
        args: tuple = (),
        kwargs: dict = None,
        depends_on: List[UUID] = None
    ) -> UUID:
        """워크플로우 단계 추가"""
        step_id = uuid4()
        step = WorkflowStep(
            id=step_id,
            name=name,
            function=function,
            args=args,
            kwargs=kwargs or {},
            depends_on=depends_on or []
        )
        self.steps[step_id] = step
        return step_id

    async def execute(self) -> Dict[UUID, Any]:
        """워크플로우 실행"""
        self._calculate_execution_order()
        results = {}

        for step_id in self.execution_order:
            step = self.steps[step_id]

            # 의존성 확인
            if not self._check_dependencies(step):
                step.status = WorkflowStatus.FAILED
                step.error = Exception("Dependencies not satisfied")
                continue

            try:
                step.status = WorkflowStatus.RUNNING

                # 의존성 결과를 kwargs에 추가
                for dep_id in step.depends_on:
                    dep_result = self.steps[dep_id].result
                    step.kwargs[f'dep_{dep_id.hex[:8]}'] = dep_result

                # 함수 실행
                if asyncio.iscoroutinefunction(step.function):
                    result = await step.function(*step.args, **step.kwargs)
                else:
                    result = step.function(*step.args, **step.kwargs)

                step.result = result
                step.status = WorkflowStatus.COMPLETED
                results[step_id] = result

            except Exception as e:
                step.status = WorkflowStatus.FAILED
                step.error = e
                raise e

        return results

    def _calculate_execution_order(self):
        """실행 순서 계산 (토폴로지 정렬)"""
        visited = set()
        temp_visited = set()
        self.execution_order = []

        def visit(step_id: UUID):
            if step_id in temp_visited:
                raise Exception("Circular dependency detected")
            if step_id in visited:
                return

            temp_visited.add(step_id)

            for dep_id in self.steps[step_id].depends_on:
                visit(dep_id)

            temp_visited.remove(step_id)
            visited.add(step_id)
            self.execution_order.append(step_id)

        for step_id in self.steps:
            if step_id not in visited:
                visit(step_id)

    def _check_dependencies(self, step: WorkflowStep) -> bool:
        """의존성 체크"""
        for dep_id in step.depends_on:
            if self.steps[dep_id].status != WorkflowStatus.COMPLETED:
                return False
        return True
```

### 4.2 ETL 오케스트레이터
```python
# application/orchestrators/etl_orchestrator.py
from typing import List, Dict, Any
from application.orchestrators.workflow_manager import WorkflowManager
from services.crawler.crawler_factory import CrawlerFactory
from services.processor.data_processor import DataProcessor
from infrastructure.database.repositories.restaurant_repository import RestaurantRepository

class ETLOrchestrator:
    def __init__(
        self,
        crawler_factory: CrawlerFactory,
        data_processor: DataProcessor,
        restaurant_repo: RestaurantRepository
    ):
        self.crawler_factory = crawler_factory
        self.data_processor = data_processor
        self.restaurant_repo = restaurant_repo

    async def run_full_pipeline(
        self,
        source_name: str,
        keywords: List[str],
        force_crawl: bool = False
    ) -> Dict[str, Any]:
        """전체 ETL 파이프라인 실행"""

        workflow = WorkflowManager()

        # 1. 캐시 확인
        cache_step = workflow.add_step(
            "check_cache",
            self._check_cache,
            args=(source_name, force_crawl)
        )

        # 2. 크롤링 (캐시에 없는 경우)
        crawl_step = workflow.add_step(
            "crawl_data",
            self._crawl_data,
            args=(source_name, keywords),
            depends_on=[cache_step]
        )

        # 3. 데이터 정제
        process_step = workflow.add_step(
            "process_data",
            self._process_data,
            depends_on=[crawl_step]
        )

        # 4. 중복 제거
        dedup_step = workflow.add_step(
            "deduplicate",
            self._deduplicate_data,
            depends_on=[process_step]
        )

        # 5. 데이터베이스 저장
        save_step = workflow.add_step(
            "save_to_database",
            self._save_to_database,
            depends_on=[dedup_step]
        )

        # 워크플로우 실행
        results = await workflow.execute()

        return {
            "pipeline_status": "completed",
            "steps_executed": len(results),
            "final_result": results[save_step]
        }

    async def _check_cache(self, source_name: str, force_crawl: bool):
        if force_crawl:
            return {"use_cache": False, "data": None}

        # 캐시 확인 로직
        cached_data = await self._get_cached_data(source_name)
        return {"use_cache": cached_data is not None, "data": cached_data}

    async def _crawl_data(self, source_name: str, keywords: List[str], **kwargs):
        cache_result = kwargs.get('dep_' + 'check_cache'[:8])

        if cache_result and cache_result.get('use_cache'):
            return cache_result['data']

        # 실제 크롤링 수행
        crawler = self.crawler_factory.create(source_name)
        async with crawler:
            return await crawler.crawl_restaurants(keywords)

    async def _process_data(self, **kwargs):
        raw_data = kwargs.get('dep_' + 'crawl_data'[:8])
        return await self.data_processor.process_batch(raw_data)

    async def _deduplicate_data(self, **kwargs):
        processed_data = kwargs.get('dep_' + 'process_data'[:8])
        return await self.data_processor.deduplicate_restaurants(processed_data)

    async def _save_to_database(self, **kwargs):
        final_data = kwargs.get('dep_' + 'deduplicate'[:8])
        return await self.restaurant_repo.save_batch(final_data)
```

## 5. 환경별 설정 관리

### 5.1 환경 설정 팩토리
```python
# config/environment_factory.py
from abc import ABC, abstractmethod
from typing import Dict, Any
import os

class EnvironmentConfig(ABC):
    @abstractmethod
    def get_database_config(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_crawler_config(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_cache_config(self) -> Dict[str, Any]:
        pass

class DevelopmentConfig(EnvironmentConfig):
    def get_database_config(self) -> Dict[str, Any]:
        return {
            "host": "localhost",
            "port": 5432,
            "database": "restaurant_dev",
            "username": "dev_user",
            "password": "dev_password",
            "pool_size": 5
        }

    def get_crawler_config(self) -> Dict[str, Any]:
        return {
            "rate_limit": 1.0,  # 개발 환경에서는 느리게
            "timeout": 10,
            "retry_count": 2,
            "debug_mode": True
        }

    def get_cache_config(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "strategy": "file",
            "ttl": 1800  # 30분
        }

class ProductionConfig(EnvironmentConfig):
    def get_database_config(self) -> Dict[str, Any]:
        return {
            "host": os.getenv("DB_HOST"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME"),
            "username": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "pool_size": int(os.getenv("DB_POOL_SIZE", "20"))
        }

    def get_crawler_config(self) -> Dict[str, Any]:
        return {
            "rate_limit": 0.5,
            "timeout": 30,
            "retry_count": 3,
            "debug_mode": False
        }

    def get_cache_config(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "strategy": "redis",
            "ttl": 3600  # 1시간
        }

class EnvironmentFactory:
    @staticmethod
    def create(env_name: str = None) -> EnvironmentConfig:
        if env_name is None:
            env_name = os.getenv("ENVIRONMENT", "development")

        if env_name == "production":
            return ProductionConfig()
        elif env_name == "testing":
            return TestingConfig()
        else:
            return DevelopmentConfig()
```

이 의존성 관리 시스템은 다음과 같은 장점을 제공합니다:

1. **느슨한 결합**: 모듈 간 직접 의존성을 제거하여 테스트와 유지보수가 쉬움
2. **확장성**: 새로운 서비스나 구현체를 쉽게 추가 가능
3. **설정 중심**: 코드 변경 없이 설정으로 동작 변경 가능
4. **테스트 친화적**: Mock 객체 주입이 쉬워 단위 테스트 작성 용이
5. **환경별 관리**: 개발/테스트/운영 환경별로 다른 구현체 사용 가능