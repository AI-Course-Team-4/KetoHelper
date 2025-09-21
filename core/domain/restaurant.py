"""
식당 도메인 모델
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from uuid import UUID, uuid4
from datetime import datetime
from core.domain.base import ValueObject
from core.domain.enums import SourceType, PriceRange

@dataclass
class Address(ValueObject):
    """주소 값 객체 (슈퍼베이스 restaurant 테이블 구조에 맞춤)"""
    addr_road: Optional[str] = None         # 도로명 주소
    addr_jibun: Optional[str] = None        # 지번 주소
    latitude: Optional[float] = None        # 위도 (double precision)
    longitude: Optional[float] = None       # 경도 (double precision)

    def __post_init__(self):
        """주소 유효성 검증"""
        if not self.addr_road and not self.addr_jibun:
            raise ValueError("At least one address (road or jibun) is required")

        super().__post_init__()

    @property
    def has_coordinates(self) -> bool:
        """좌표 정보 보유 여부"""
        return self.latitude is not None and self.longitude is not None

    @property
    def display_address(self) -> str:
        """표시용 주소"""
        return self.addr_road or self.addr_jibun or ""

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
class Restaurant:
    """식당 애그리게이트 루트 (슈퍼베이스 restaurant 테이블 구조에 맞춤)"""

    # 필수 필드들 (기본값 없음)
    name: str
    source: str                             # 소스 (diningcode, siksin 등)
    source_url: str                         # 소스 URL

    # 선택적 필드들 (기본값 있음)
    phone: Optional[str] = None
    address: Optional[Address] = None
    category: Optional[str] = None           # 요리 종류
    price_range: Optional[int] = None        # 가격대 (integer)
    place_provider: Optional[str] = None     # 장소 제공자
    place_id: Optional[str] = None          # 장소 ID
    normalized_name: Optional[str] = None    # 정규화된 이름
    homepage_url: Optional[str] = None      # 홈페이지 URL
    
    # BaseEntity 필드들 (기본값 있음)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # 소스 정보
    sources: List[RestaurantSource] = field(default_factory=list)

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Restaurant name is required")

        # 정규화
        self.name = self.name.strip()


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