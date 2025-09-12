"""
🍽️ Menu 데이터 모델
- 식당별 메뉴 정보 관리
- Pydantic 기반 타입 안전성
- Restaurant와 관계 설정
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal

from pydantic import BaseModel, Field, validator, root_validator
from pydantic.types import conint, constr


class MenuBase(BaseModel):
    """Menu 기본 모델"""
    
    # 🔗 관계
    restaurant_id: UUID = Field(..., description="소속 식당 ID")
    
    # 🎯 기본 메뉴 정보
    name: str = Field(..., min_length=1, max_length=100, description="메뉴명")
    price: Optional[conint(gt=0)] = Field(None, description="가격 (원)")
    currency: str = Field("KRW", max_length=3, description="통화")
    description: Optional[str] = Field(None, max_length=1000, description="메뉴 설명")
    
    # 🏷️ 메뉴 분류
    category: Optional[str] = Field(None, max_length=50, description="메뉴 카테고리")
    is_signature: bool = Field(False, description="대표 메뉴 여부")
    is_recommended: bool = Field(False, description="추천 메뉴 여부")
    
    # 🖼️ 이미지 정보
    image_url: Optional[str] = Field(None, max_length=1000, description="메뉴 이미지 URL")
    
    # 📊 메뉴 인기도
    popularity_score: Optional[conint(ge=0, le=100)] = Field(0, description="인기도 점수")
    order_count: Optional[conint(ge=0)] = Field(0, description="주문 횟수 추정")
    
    class Config:
        """Pydantic 설정"""
        use_enum_values = True
        validate_assignment = True
        str_strip_whitespace = True
        anystr_strip_whitespace = True
        max_anystr_length = 1000


class MenuCreate(MenuBase):
    """Menu 생성 모델"""
    pass


class MenuUpdate(BaseModel):
    """Menu 업데이트 모델"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[conint(gt=0)] = None
    currency: Optional[str] = Field(None, max_length=3)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, max_length=50)
    is_signature: Optional[bool] = None
    is_recommended: Optional[bool] = None
    image_url: Optional[str] = Field(None, max_length=1000)
    popularity_score: Optional[conint(ge=0, le=100)] = None
    order_count: Optional[conint(ge=0)] = None


class Menu(MenuBase):
    """Menu 완전 모델 (DB 포함)"""
    
    # 🔑 시스템 필드
    id: UUID = Field(default_factory=uuid4, description="고유 식별자")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 시간")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="수정 시간")
    
    class Config(MenuBase.Config):
        """설정 확장"""
        orm_mode = True  # SQLAlchemy ORM 호환
    
    @validator('name')
    def validate_name(cls, v):
        """메뉴명 검증"""
        if not v or len(v.strip()) == 0:
            raise ValueError('메뉴명은 필수입니다')
        
        # 메뉴명 정규화
        name = v.strip()
        
        # 불필요한 접미사 제거
        suffixes = ['1인분', '2인분', '(대)', '(중)', '(소)']
        for suffix in suffixes:
            if name.endswith(suffix):
                base_name = name[:-len(suffix)].strip()
                if base_name:  # 빈 문자열이 되지 않도록
                    name = base_name
                break
        
        return name
    
    @validator('price')
    def validate_price(cls, v):
        """가격 검증"""
        if v is not None:
            # 가격 범위 검증
            if v < 500:
                raise ValueError('가격이 너무 낮습니다 (최소 500원)')
            if v > 1000000:
                raise ValueError('가격이 너무 높습니다 (최대 1,000,000원)')
        
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        """통화 검증"""
        allowed_currencies = ['KRW', 'USD', 'EUR', 'JPY', 'CNY']
        if v not in allowed_currencies:
            raise ValueError(f'지원되지 않는 통화입니다: {v}')
        
        return v
    
    @validator('category')
    def validate_category(cls, v):
        """카테고리 검증"""
        if v:
            # 카테고리 정규화
            category_mapping = {
                '메인': ['메인요리', '주요리', '본식'],
                '사이드': ['사이드메뉴', '사이드요리', '반찬'],
                '음료': ['음료수', '드링크', '차'],
                '디저트': ['후식', '간식', '디저트'],
                '주류': ['술', '알코올', '맥주', '소주']
            }
            
            v_lower = v.lower()
            for standard_cat, variations in category_mapping.items():
                if v_lower in [var.lower() for var in variations]:
                    v = standard_cat
                    break
        
        return v
    
    @validator('image_url')
    def validate_image_url(cls, v):
        """이미지 URL 검증"""
        if v:
            import re
            url_pattern = r'^https?://.+'
            if not re.match(url_pattern, v):
                raise ValueError('올바른 이미지 URL 형식이 아닙니다')
            
            # 이미지 확장자 검증
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            if not any(v.lower().endswith(ext) for ext in image_extensions):
                # 확장자가 없어도 통과 (동적 이미지 URL일 수 있음)
                pass
        
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return self.dict(exclude_none=True)
    
    def get_display_name(self) -> str:
        """표시용 이름"""
        if self.price:
            return f"{self.name} ({self.price:,}원)"
        else:
            return self.name
    
    def get_price_display(self) -> str:
        """가격 표시 문자열"""
        if self.price:
            if self.currency == 'KRW':
                return f"{self.price:,}원"
            else:
                return f"{self.currency} {self.price:,}"
        else:
            return "가격 문의"
    
    def is_expensive(self, threshold: int = 30000) -> bool:
        """고가 메뉴 여부"""
        return self.price is not None and self.price >= threshold
    
    def is_affordable(self, threshold: int = 10000) -> bool:
        """저가 메뉴 여부"""
        return self.price is not None and self.price <= threshold
    
    def has_image(self) -> bool:
        """이미지 보유 여부"""
        return self.image_url is not None and len(self.image_url) > 0
    
    def calculate_similarity(self, other: 'Menu') -> float:
        """다른 메뉴와의 유사도 계산 (0-1)"""
        from ..utils.text_utils import calculate_text_similarity
        
        # 메뉴명 유사도 (가중치 0.8)
        name_similarity = calculate_text_similarity(self.name, other.name)
        
        # 가격 유사도 (가중치 0.2)
        price_similarity = 0.0
        if self.price and other.price:
            price_diff = abs(self.price - other.price)
            max_price = max(self.price, other.price)
            price_similarity = max(0, 1 - (price_diff / max_price))
        
        return name_similarity * 0.8 + price_similarity * 0.2


class MenuEnriched(BaseModel):
    """Menu 풍부화 모델 (Phase 2 용)"""
    
    menu_id: UUID = Field(..., description="메뉴 ID")
    
    # 🥘 풍부화 정보
    short_desc: Optional[str] = Field(None, max_length=120, description="간단 설명")
    main_ingredients: Optional[List[str]] = Field(None, description="주요 재료 (최대 5개)")
    dietary_tags: Optional[List[str]] = Field(None, description="식단 태그")
    spice_level: Optional[conint(ge=0, le=3)] = Field(None, description="매운 정도 (0-3)")
    temperature: Optional[constr(regex=r'^(hot|cold|room)$')] = Field(None, description="온도")
    cooking_method: Optional[str] = Field(None, max_length=50, description="조리법")
    allergens: Optional[List[str]] = Field(None, description="알레르겐 정보")
    serving_size: Optional[str] = Field(None, max_length=20, description="제공량")
    meal_time: Optional[List[str]] = Field(None, description="식사 시간")
    
    # 🔍 풍부화 메타데이터
    enrichment_source: constr(regex=r'^(raw|rule|search|llm|hybrid)$') = Field("raw", description="풍부화 소스")
    enrichment_confidence: Optional[float] = Field(None, ge=0, le=1, description="신뢰도")
    enrichment_updated_at: Optional[datetime] = Field(None, description="풍부화 업데이트 시간")
    
    class Config:
        use_enum_values = True
        validate_assignment = True


class MenuSearch(BaseModel):
    """Menu 검색 모델"""
    
    restaurant_id: Optional[UUID] = Field(None, description="식당 ID 필터")
    keyword: Optional[str] = Field(None, description="검색 키워드")
    category: Optional[str] = Field(None, description="카테고리 필터")
    
    # 가격 필터
    min_price: Optional[int] = Field(None, ge=0, description="최소 가격")
    max_price: Optional[int] = Field(None, ge=0, description="최대 가격")
    
    # 특성 필터
    is_signature: Optional[bool] = Field(None, description="대표 메뉴만")
    is_recommended: Optional[bool] = Field(None, description="추천 메뉴만")
    has_image: Optional[bool] = Field(None, description="이미지 보유 메뉴만")
    
    # 페이지네이션
    page: int = Field(1, ge=1, description="페이지 번호")
    size: int = Field(20, ge=1, le=100, description="페이지 크기")
    
    # 정렬
    sort_by: str = Field("name", description="정렬 기준")
    sort_desc: bool = Field(False, description="내림차순 정렬")


class MenuStats(BaseModel):
    """Menu 통계 모델"""
    
    total_count: int = Field(0, description="전체 메뉴 수")
    by_category: Dict[str, int] = Field(default_factory=dict, description="카테고리별 개수")
    by_restaurant: Dict[str, int] = Field(default_factory=dict, description="식당별 개수")
    
    avg_price: Optional[float] = Field(None, description="평균 가격")
    min_price: Optional[int] = Field(None, description="최저 가격")
    max_price: Optional[int] = Field(None, description="최고 가격")
    
    signature_count: int = Field(0, description="대표 메뉴 수")
    recommended_count: int = Field(0, description="추천 메뉴 수")
    with_image_count: int = Field(0, description="이미지 보유 메뉴 수")
    
    price_distribution: Dict[str, int] = Field(default_factory=dict, description="가격대별 분포")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="마지막 업데이트")


# 편의 함수들
def classify_price_range(price: Optional[int]) -> str:
    """가격대 분류"""
    if price is None:
        return "알 수 없음"
    elif price <= 5000:
        return "저가 (5천원 이하)"
    elif price <= 15000:
        return "중가 (5천원-1만5천원)"
    elif price <= 30000:
        return "고가 (1만5천원-3만원)"
    else:
        return "최고가 (3만원 이상)"


def extract_menu_keywords(menu_name: str, description: str = "") -> List[str]:
    """메뉴에서 키워드 추출"""
    from ..utils.text_utils import normalize_text
    
    text = normalize_text(f"{menu_name} {description}")
    
    # 음식 관련 키워드 패턴
    food_patterns = [
        r'(김치|된장|고추장|간장)',  # 한식 양념
        r'(볶음|찜|구이|튀김|국|탕)',  # 조리법
        r'(소고기|돼지고기|닭고기|생선)',  # 주재료
        r'(밥|면|국수|떡)',  # 주식
        r'(매운|달콤|짭짤|시원)',  # 맛
    ]
    
    keywords = []
    for pattern in food_patterns:
        import re
        matches = re.findall(pattern, text)
        keywords.extend(matches)
    
    return list(set(keywords))  # 중복 제거


if __name__ == "__main__":
    # 테스트 코드
    from uuid import uuid4
    
    menu_data = {
        "restaurant_id": uuid4(),
        "name": "김치찌개 1인분",
        "price": 8000,
        "description": "매콤한 김치와 돼지고기가 들어간 찌개",
        "category": "메인요리",
        "is_signature": True,
        "image_url": "https://example.com/kimchi-stew.jpg"
    }
    
    try:
        menu = Menu(**menu_data)
        print(f"✅ Menu 생성 성공: {menu.name}")
        print(f"   표시명: {menu.get_display_name()}")
        print(f"   가격 표시: {menu.get_price_display()}")
        print(f"   고가 여부: {menu.is_expensive()}")
        print(f"   이미지 보유: {menu.has_image()}")
        print(f"   가격대: {classify_price_range(menu.price)}")
        
        # 키워드 추출 테스트
        keywords = extract_menu_keywords(menu.name, menu.description or "")
        print(f"   키워드: {keywords}")
        
        # JSON 직렬화 테스트
        json_data = menu.json()
        print(f"   JSON 크기: {len(json_data)}바이트")
        
    except Exception as e:
        print(f"❌ Menu 생성 실패: {e}")