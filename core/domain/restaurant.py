"""
식당 도메인 모델
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from core.domain.base import AggregateRoot, ValueObject
from core.domain.enums import SourceType, PriceRange

@dataclass
class Address(ValueObject):
    """주소 값 객체"""
    original: str                           # 원본 주소
    normalized: Optional[str] = None        # 표준화된 주소
    latitude: Optional[Decimal] = None      # 위도
    longitude: Optional[Decimal] = None     # 경도
    geohash6: Optional[str] = None          # 6자리 지오해시

    def __post_init__(self):
        """주소 유효성 검증"""
        if not self.original or not self.original.strip():
            raise ValueError("Original address is required")

        # 좌표가 있으면 지오해시 생성
        if self.latitude is not None and self.longitude is not None:
            self.geohash6 = self._generate_geohash()

        super().__post_init__()

    def _generate_geohash(self) -> str:
        """지오해시 생성"""
        try:
            import geohash2
            return geohash2.encode(float(self.latitude), float(self.longitude), precision=6)
        except ImportError:
            # geohash2가 없으면 간단한 구현
            return f"{self.latitude:.3f},{self.longitude:.3f}"

    @property
    def has_coordinates(self) -> bool:
        """좌표 정보 보유 여부"""
        return self.latitude is not None and self.longitude is not None

    @property
    def display_address(self) -> str:
        """표시용 주소"""
        return self.normalized or self.original

@dataclass
class BusinessHours(ValueObject):
    """영업시간 값 객체"""
    monday: Optional[str] = None
    tuesday: Optional[str] = None
    wednesday: Optional[str] = None
    thursday: Optional[str] = None
    friday: Optional[str] = None
    saturday: Optional[str] = None
    sunday: Optional[str] = None
    holiday: Optional[str] = None

    def to_dict(self) -> Dict[str, Optional[str]]:
        """딕셔너리로 변환"""
        return {
            "monday": self.monday,
            "tuesday": self.tuesday,
            "wednesday": self.wednesday,
            "thursday": self.thursday,
            "friday": self.friday,
            "saturday": self.saturday,
            "sunday": self.sunday,
            "holiday": self.holiday
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'BusinessHours':
        """딕셔너리에서 생성"""
        return cls(
            monday=data.get('monday'),
            tuesday=data.get('tuesday'),
            wednesday=data.get('wednesday'),
            thursday=data.get('thursday'),
            friday=data.get('friday'),
            saturday=data.get('saturday'),
            sunday=data.get('sunday'),
            holiday=data.get('holiday')
        )

@dataclass
class RestaurantSource:
    """식당 소스 정보 (값 객체 성격)"""
    source_name: SourceType
    source_url: str
    source_id: Optional[str] = None
    name_raw: Optional[str] = None
    addr_raw: Optional[str] = None
    phone_raw: Optional[str] = None
    data_raw: Optional[Dict[str, Any]] = None
    is_primary: bool = False

    def __post_init__(self):
        if not self.source_url:
            raise ValueError("Source URL is required")

@dataclass
class Restaurant(AggregateRoot):
    """식당 애그리게이트 루트"""

    # 기본 정보
    name: str
    phone: Optional[str] = None
    address: Optional[Address] = None
    business_hours: Optional[BusinessHours] = None

    # 분류 정보
    cuisine_types: List[str] = field(default_factory=list)
    price_range: Optional[PriceRange] = None

    # 평가 정보
    rating_avg: Optional[Decimal] = None
    review_count: int = 0

    # 메타데이터
    canonical_key: Optional[str] = None
    is_active: bool = True

    # 소스 정보 (별도 테이블로 관리되지만 도메인 객체로도 보유)
    sources: List[RestaurantSource] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()

        if not self.name or not self.name.strip():
            raise ValueError("Restaurant name is required")

        # 정규화
        self.name = self.name.strip()

        # 캐노니컬 키 생성
        if not self.canonical_key:
            self.canonical_key = self._generate_canonical_key()

    def _generate_canonical_key(self) -> str:
        """중복 제거용 캐노니컬 키 생성"""
        import re

        # 이름 정규화
        normalized_name = re.sub(r'[^\w가-힣]', '', self.name.lower())

        # 지오해시 포함 (있으면)
        geohash_part = ""
        if self.address and self.address.geohash6:
            geohash_part = f"_{self.address.geohash6}"

        # 전화번호 포함 (있으면)
        phone_part = ""
        if self.phone:
            clean_phone = re.sub(r'[^\d]', '', self.phone)
            if clean_phone:
                phone_part = f"_{clean_phone[-8:]}"  # 뒤 8자리만

        return f"{normalized_name}{geohash_part}{phone_part}"

    def add_source(self, source: RestaurantSource):
        """소스 정보 추가"""
        # 기존 소스 중복 체크
        existing_sources = [s for s in self.sources if s.source_url == source.source_url]
        if existing_sources:
            return  # 이미 존재

        self.sources.append(source)

        # 주 소스 설정
        if source.is_primary or not any(s.is_primary for s in self.sources):
            self._set_primary_source(source)

    def _set_primary_source(self, primary_source: RestaurantSource):
        """주 소스 설정"""
        for source in self.sources:
            source.is_primary = (source == primary_source)

    def get_primary_source(self) -> Optional[RestaurantSource]:
        """주 소스 반환"""
        primary_sources = [s for s in self.sources if s.is_primary]
        return primary_sources[0] if primary_sources else None

    def update_basic_info(
        self,
        name: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[Address] = None,
        business_hours: Optional[BusinessHours] = None
    ):
        """기본 정보 업데이트"""
        if name is not None:
            self.name = name.strip()

        if phone is not None:
            self.phone = phone

        if address is not None:
            self.address = address

        if business_hours is not None:
            self.business_hours = business_hours

        # 캐노니컬 키 재생성
        self.canonical_key = self._generate_canonical_key()
        self.update_timestamp()

    def update_rating(self, rating: Decimal, review_count: int):
        """평점 정보 업데이트"""
        self.rating_avg = rating
        self.review_count = review_count
        self.update_timestamp()

    def deactivate(self):
        """식당 비활성화"""
        self.is_active = False
        self.update_timestamp()

    def activate(self):
        """식당 활성화"""
        self.is_active = True
        self.update_timestamp()

    @property
    def has_location(self) -> bool:
        """위치 정보 보유 여부"""
        return self.address is not None and self.address.has_coordinates

    @property
    def display_name(self) -> str:
        """표시용 이름"""
        return self.name

    @property
    def source_count(self) -> int:
        """소스 개수"""
        return len(self.sources)

    def to_summary_dict(self) -> Dict[str, Any]:
        """요약 정보 딕셔너리"""
        return {
            "id": str(self.id),
            "name": self.name,
            "phone": self.phone,
            "address": self.address.display_address if self.address else None,
            "cuisine_types": self.cuisine_types,
            "price_range": self.price_range.value if self.price_range else None,
            "rating_avg": float(self.rating_avg) if self.rating_avg else None,
            "review_count": self.review_count,
            "is_active": self.is_active,
            "has_location": self.has_location,
            "source_count": self.source_count
        }