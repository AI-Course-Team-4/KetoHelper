"""
🏪 Restaurant 데이터 모델
- Pydantic 기반 타입 안전성 보장
- 자동 검증 및 직렬화/역직렬화
- Supabase 호환
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import confloat, conint


class RestaurantBase(BaseModel):
    """Restaurant 기본 모델"""
    
    # 🎯 기본 정보 (필수)
    name: str = Field(..., min_length=1, max_length=100, description="식당명")
    
    # 📍 위치 정보
    address_road: Optional[str] = Field(None, max_length=200, description="도로명 주소")
    address_jibun: Optional[str] = Field(None, max_length=200, description="지번 주소")
    lat: Optional[confloat(ge=-90, le=90)] = Field(None, description="위도")
    lng: Optional[confloat(ge=-180, le=180)] = Field(None, description="경도")
    
    # 📞 연락 정보
    phone: Optional[str] = Field(None, max_length=20, description="전화번호")
    homepage_url: Optional[str] = Field(None, max_length=500, description="홈페이지 URL")
    
    # 🍽️ 카테고리 정보
    category: Optional[str] = Field(None, max_length=50, description="음식 카테고리")
    cuisine_type: Optional[str] = Field(None, max_length=50, description="요리 타입")
    
    # ⭐ 평점 정보
    rating: Optional[confloat(ge=0, le=5)] = Field(None, description="평점 (0-5)")
    review_count: Optional[conint(ge=0)] = Field(0, description="리뷰 개수")
    
    # 🕐 운영 정보
    business_hours: Optional[str] = Field(None, max_length=500, description="영업시간")
    
    # 🔍 크롤링 메타데이터
    source: str = Field(..., max_length=20, description="데이터 소스")
    source_url: str = Field(..., max_length=1000, description="원본 URL")
    source_id: Optional[str] = Field(None, max_length=100, description="사이트 내 식당 ID")
    
    # 📊 데이터 품질
    quality_score: Optional[conint(ge=0, le=100)] = Field(0, description="품질 점수")
    last_verified_at: Optional[datetime] = Field(None, description="마지막 검증 시간")
    
    class Config:
        """Pydantic 설정"""
        use_enum_values = True
        validate_assignment = True
        str_strip_whitespace = True
        anystr_strip_whitespace = True
        max_anystr_length = 1000


class RestaurantCreate(RestaurantBase):
    """Restaurant 생성 모델"""
    pass


class RestaurantUpdate(BaseModel):
    """Restaurant 업데이트 모델"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    address_road: Optional[str] = Field(None, max_length=200)
    address_jibun: Optional[str] = Field(None, max_length=200)
    lat: Optional[confloat(ge=-90, le=90)] = None
    lng: Optional[confloat(ge=-180, le=180)] = None
    phone: Optional[str] = Field(None, max_length=20)
    homepage_url: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=50)
    cuisine_type: Optional[str] = Field(None, max_length=50)
    rating: Optional[confloat(ge=0, le=5)] = None
    review_count: Optional[conint(ge=0)] = None
    business_hours: Optional[str] = Field(None, max_length=500)
    quality_score: Optional[conint(ge=0, le=100)] = None
    last_verified_at: Optional[datetime] = None


class Restaurant(RestaurantBase):
    """Restaurant 완전 모델 (DB 포함)"""
    
    # 🔑 시스템 필드
    id: UUID = Field(default_factory=uuid4, description="고유 식별자")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="수정 시간")
    
    class Config(RestaurantBase.Config):
        """설정 확장"""
        orm_mode = True  # SQLAlchemy ORM 호환
    
    @validator('name')
    def validate_name(cls, v):
        """식당명 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('식당명은 필수입니다')
        
        # 불필요한 접미사 제거
        suffixes = ['본점', '분점', '지점', '매장', '식당', '레스토랑']
        name = v.strip()
        for suffix in suffixes:
            if name.endswith(suffix) and len(name) > len(suffix):
                name = name[:-len(suffix)].strip()
                break
        
        return name
    
    @validator('phone')
    def validate_phone(cls, v):
        """전화번호 검증"""
        if v:
            import re
            # 전화번호 패턴 검증
            pattern = r'^(\d{2,3})-(\d{3,4})-(\d{4})$'
            if not re.match(pattern, v):
                # 자동 정규화 시도
                digits = re.sub(r'[^\d]', '', v)
                if len(digits) == 10:
                    v = f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
                elif len(digits) == 11:
                    v = f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
                else:
                    raise ValueError('올바른 전화번호 형식이 아닙니다 (예: 02-1234-5678)')
        
        return v
    
    @validator('homepage_url')
    def validate_url(cls, v):
        """URL 검증"""
        if v:
            import re
            url_pattern = r'^https?://.+'
            if not re.match(url_pattern, v):
                raise ValueError('올바른 URL 형식이 아닙니다')
        
        return v
    
    @root_validator
    def validate_coordinates(cls, values):
        """좌표 검증"""
        lat = values.get('lat')
        lng = values.get('lng')
        
        # 좌표가 하나만 있으면 에러
        if (lat is None) != (lng is None):
            raise ValueError('위도와 경도는 함께 제공되어야 합니다')
        
        # 서울시 경계 검증 (대략적)
        if lat is not None and lng is not None:
            if not (37.4 <= lat <= 37.7 and 126.8 <= lng <= 127.2):
                # 경고만 하고 통과 (다른 지역도 있을 수 있음)
                pass
        
        return values
    
    @root_validator
    def calculate_quality_score(cls, values):
        """품질 점수 자동 계산"""
        if values.get('quality_score') is not None:
            return values  # 이미 설정된 경우 그대로
        
        score = 0
        
        # 기본 정보 점수 (70점)
        if values.get('name'):
            score += 20
        if values.get('address_road'):
            score += 15
        if values.get('lat') is not None and values.get('lng') is not None:
            score += 20
        if values.get('phone'):
            score += 10
        if values.get('category'):
            score += 5
        
        # 추가 정보 점수 (30점)
        if values.get('rating') is not None:
            score += 10
        if values.get('business_hours'):
            score += 5
        if values.get('homepage_url'):
            score += 5
        if values.get('cuisine_type'):
            score += 5
        if values.get('review_count', 0) > 0:
            score += 5
        
        values['quality_score'] = min(score, 100)
        return values
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return self.dict(exclude_none=True)
    
    def is_high_quality(self) -> bool:
        """고품질 데이터 여부"""
        return self.quality_score >= 80
    
    def is_geocoded(self) -> bool:
        """좌표 정보 보유 여부"""
        return self.lat is not None and self.lng is not None
    
    def get_display_name(self) -> str:
        """표시용 이름"""
        return f"{self.name} ({self.source})"
    
    def calculate_similarity(self, other: 'Restaurant') -> float:
        """다른 식당과의 유사도 계산 (0-1)"""
        from ..utils.text_utils import calculate_restaurant_similarity
        
        return calculate_restaurant_similarity(
            self.to_dict(),
            other.to_dict()
        )


class RestaurantSearch(BaseModel):
    """Restaurant 검색 모델"""
    
    keyword: Optional[str] = Field(None, description="검색 키워드")
    category: Optional[str] = Field(None, description="카테고리 필터")
    source: Optional[str] = Field(None, description="소스 필터")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="최소 평점")
    has_coordinates: Optional[bool] = Field(None, description="좌표 보유 여부")
    min_quality_score: Optional[int] = Field(None, ge=0, le=100, description="최소 품질 점수")
    
    # 위치 기반 검색
    center_lat: Optional[float] = Field(None, description="중심 위도")
    center_lng: Optional[float] = Field(None, description="중심 경도")
    radius_km: Optional[float] = Field(None, gt=0, description="검색 반경 (km)")
    
    # 페이지네이션
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(20, ge=1, le=100, description="페이지 크기")
    
    # 정렬
    sort_by: str = Field("created_at", description="정렬 기준")
    sort_desc: bool = Field(True, description="내림차순 정렬")


class RestaurantStats(BaseModel):
    """Restaurant 통계 모델"""
    
    total_count: int = Field(0, description="전체 식당 수")
    by_source: Dict[str, int] = Field(default_factory=dict, description="소스별 개수")
    by_category: Dict[str, int] = Field(default_factory=dict, description="카테고리별 개수")
    
    avg_rating: Optional[float] = Field(None, description="평균 평점")
    avg_quality_score: Optional[float] = Field(None, description="평균 품질 점수")
    geocoded_count: int = Field(0, description="좌표 보유 식당 수")
    high_quality_count: int = Field(0, description="고품질 식당 수")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="마지막 업데이트")


if __name__ == "__main__":
    # 테스트 코드
    restaurant_data = {
        "name": "강남 맛집 본점",
        "address_road": "서울시 강남구 테헤란로 123",
        "lat": 37.5665,
        "lng": 126.9780,
        "phone": "021234567",  # 자동 정규화 테스트
        "category": "한식",
        "rating": 4.5,
        "source": "siksin",
        "source_url": "https://siksin.com/restaurants/123"
    }
    
    try:
        restaurant = Restaurant(**restaurant_data)
        print(f"✅ Restaurant 생성 성공: {restaurant.name}")
        print(f"   전화번호: {restaurant.phone}")
        print(f"   품질 점수: {restaurant.quality_score}")
        print(f"   고품질 여부: {restaurant.is_high_quality()}")
        print(f"   좌표 보유: {restaurant.is_geocoded()}")
        
        # JSON 직렬화 테스트
        json_data = restaurant.json()
        print(f"   JSON 크기: {len(json_data)}바이트")
        
    except Exception as e:
        print(f"❌ Restaurant 생성 실패: {e}")