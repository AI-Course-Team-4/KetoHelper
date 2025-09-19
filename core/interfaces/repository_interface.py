"""
Repository 인터페이스 정의
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Generic, TypeVar, Dict, Any
from uuid import UUID

T = TypeVar('T')

class RepositoryInterface(Generic[T], ABC):
    """기본 Repository 인터페이스"""

    @abstractmethod
    async def save(self, entity: T) -> T:
        """엔티티 저장"""
        pass

    @abstractmethod
    async def save_batch(self, entities: List[T]) -> List[T]:
        """엔티티 일괄 저장"""
        pass

    @abstractmethod
    async def find_by_id(self, entity_id: UUID) -> Optional[T]:
        """ID로 엔티티 조회"""
        pass

    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """전체 엔티티 조회"""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """엔티티 업데이트"""
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """엔티티 삭제"""
        pass

    @abstractmethod
    async def exists(self, entity_id: UUID) -> bool:
        """엔티티 존재 여부 확인"""
        pass

    @abstractmethod
    async def count(self, **filters) -> int:
        """엔티티 개수 조회"""
        pass

class RestaurantRepositoryInterface(RepositoryInterface):
    """식당 Repository 인터페이스"""

    @abstractmethod
    async def find_by_canonical_key(self, canonical_key: str) -> Optional['Restaurant']:
        """캐노니컬 키로 식당 조회"""
        pass

    @abstractmethod
    async def find_nearby(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 1.0,
        limit: int = 50
    ) -> List['Restaurant']:
        """주변 식당 조회"""
        pass

    @abstractmethod
    async def search_by_name(self, name: str, limit: int = 50) -> List['Restaurant']:
        """이름으로 식당 검색"""
        pass

    @abstractmethod
    async def find_by_source_url(self, source_url: str) -> Optional['Restaurant']:
        """소스 URL로 식당 조회"""
        pass

    @abstractmethod
    async def find_duplicates(self, restaurant: 'Restaurant') -> List['Restaurant']:
        """중복 식당 후보 조회"""
        pass

class MenuRepositoryInterface(RepositoryInterface):
    """메뉴 Repository 인터페이스"""

    @abstractmethod
    async def find_by_restaurant_id(self, restaurant_id: UUID) -> List['Menu']:
        """식당별 메뉴 조회"""
        pass

    @abstractmethod
    async def search_by_name(self, name: str, limit: int = 50) -> List['Menu']:
        """이름으로 메뉴 검색"""
        pass

    @abstractmethod
    async def find_by_category(self, category: 'MenuCategory', limit: int = 100) -> List['Menu']:
        """카테고리별 메뉴 조회"""
        pass

    @abstractmethod
    async def find_signature_menus(self, restaurant_id: UUID = None) -> List['Menu']:
        """대표 메뉴 조회"""
        pass

    @abstractmethod
    async def find_available_menus(self, restaurant_id: UUID = None) -> List['Menu']:
        """이용 가능한 메뉴 조회"""
        pass

class MenuIngredientRepositoryInterface(RepositoryInterface):
    """메뉴-재료 Repository 인터페이스"""

    @abstractmethod
    async def find_by_menu_id(self, menu_id: UUID) -> List['MenuIngredient']:
        """메뉴별 재료 조회"""
        pass

    @abstractmethod
    async def find_by_ingredient_name(self, ingredient_name: str) -> List['MenuIngredient']:
        """재료명으로 조회"""
        pass

    @abstractmethod
    async def find_by_source(self, source: 'IngredientSource') -> List['MenuIngredient']:
        """소스별 재료 조회"""
        pass

    @abstractmethod
    async def update_confidence(self, menu_id: UUID, ingredient_name: str, confidence: float) -> bool:
        """신뢰도 업데이트"""
        pass

class KetoScoreRepositoryInterface(RepositoryInterface):
    """키토 점수 Repository 인터페이스"""

    @abstractmethod
    async def find_by_menu_id(self, menu_id: UUID, rule_version: str = None) -> Optional['KetoScore']:
        """메뉴별 키토 점수 조회"""
        pass

    @abstractmethod
    async def find_high_scores(self, min_score: int = 80, limit: int = 100) -> List['KetoScore']:
        """고득점 메뉴 조회"""
        pass

    @abstractmethod
    async def find_needs_review(self, limit: int = 100) -> List['KetoScore']:
        """검토 필요 메뉴 조회"""
        pass

    @abstractmethod
    async def find_by_score_range(
        self,
        min_score: int,
        max_score: int,
        limit: int = 100
    ) -> List['KetoScore']:
        """점수 범위별 조회"""
        pass

    @abstractmethod
    async def get_score_statistics(self) -> Dict[str, Any]:
        """점수 통계 조회"""
        pass

class CrawlJobRepositoryInterface(RepositoryInterface):
    """크롤링 작업 Repository 인터페이스"""

    @abstractmethod
    async def find_by_source(self, source_name: str, limit: int = 50) -> List['CrawlJob']:
        """소스별 크롤링 작업 조회"""
        pass

    @abstractmethod
    async def find_by_status(self, status: 'CrawlJobStatus', limit: int = 50) -> List['CrawlJob']:
        """상태별 크롤링 작업 조회"""
        pass

    @abstractmethod
    async def find_recent_jobs(self, hours: int = 24, limit: int = 50) -> List['CrawlJob']:
        """최근 크롤링 작업 조회"""
        pass

    @abstractmethod
    async def update_status(self, job_id: UUID, status: 'CrawlJobStatus', error_message: str = None) -> bool:
        """작업 상태 업데이트"""
        pass