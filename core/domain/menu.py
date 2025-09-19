"""
메뉴 도메인 모델
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from uuid import UUID
from core.domain.base import BaseEntity, ValueObject
from core.domain.enums import MenuCategory, SpiceLevel, IngredientRole, IngredientSource

@dataclass
class NutritionInfo(ValueObject):
    """영양 정보 값 객체"""
    calories: Optional[int] = None          # 칼로리
    carbohydrates: Optional[Decimal] = None # 탄수화물 (g)
    protein: Optional[Decimal] = None       # 단백질 (g)
    fat: Optional[Decimal] = None           # 지방 (g)
    fiber: Optional[Decimal] = None         # 식이섬유 (g)
    sodium: Optional[Decimal] = None        # 나트륨 (mg)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "calories": self.calories,
            "carbohydrates": float(self.carbohydrates) if self.carbohydrates else None,
            "protein": float(self.protein) if self.protein else None,
            "fat": float(self.fat) if self.fat else None,
            "fiber": float(self.fiber) if self.fiber else None,
            "sodium": float(self.sodium) if self.sodium else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NutritionInfo':
        """딕셔너리에서 생성"""
        return cls(
            calories=data.get('calories'),
            carbohydrates=Decimal(str(data['carbohydrates'])) if data.get('carbohydrates') else None,
            protein=Decimal(str(data['protein'])) if data.get('protein') else None,
            fat=Decimal(str(data['fat'])) if data.get('fat') else None,
            fiber=Decimal(str(data['fiber'])) if data.get('fiber') else None,
            sodium=Decimal(str(data['sodium'])) if data.get('sodium') else None
        )

    @property
    def has_macronutrients(self) -> bool:
        """주요 영양소 정보 보유 여부"""
        return any([self.carbohydrates, self.protein, self.fat])

@dataclass
class MenuIngredient(BaseEntity):
    """메뉴-재료 관계"""
    menu_id: UUID
    ingredient_name: str
    role: IngredientRole = IngredientRole.MAIN
    quantity: Optional[str] = None
    source: IngredientSource = IngredientSource.RULE
    confidence: Optional[Decimal] = None

    def __post_init__(self):
        super().__post_init__()

        if not self.ingredient_name or not self.ingredient_name.strip():
            raise ValueError("Ingredient name is required")

        self.ingredient_name = self.ingredient_name.strip()

        # 신뢰도 검증
        if self.confidence is not None:
            if not (0 <= self.confidence <= 1):
                raise ValueError("Confidence must be between 0 and 1")

    def update_confidence(self, confidence: Decimal):
        """신뢰도 업데이트"""
        if not (0 <= confidence <= 1):
            raise ValueError("Confidence must be between 0 and 1")

        self.confidence = confidence
        self.update_timestamp()

@dataclass
class Menu(BaseEntity):
    """메뉴 엔티티"""

    # 기본 정보
    restaurant_id: UUID
    name: str
    name_norm: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None  # KRW 단위

    # 분류 정보
    category: MenuCategory = MenuCategory.UNKNOWN
    menu_type: Optional[str] = None  # 세트/단품/코스 등
    is_signature: bool = False

    # 영양 정보
    nutrition_info: Optional[NutritionInfo] = None

    # 기타 정보
    allergens: List[str] = field(default_factory=list)
    spice_level: Optional[SpiceLevel] = None

    # 상태
    is_available: bool = True

    # 재료 정보 (관계 데이터지만 도메인 객체로도 보유)
    ingredients: List[MenuIngredient] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()

        if not self.name or not self.name.strip():
            raise ValueError("Menu name is required")

        # 이름 정규화
        self.name = self.name.strip()
        if not self.name_norm:
            self.name_norm = self._normalize_name()

        # 가격 검증
        if self.price is not None and self.price < 0:
            raise ValueError("Price cannot be negative")

    def _normalize_name(self) -> str:
        """메뉴명 정규화"""
        import re

        # 괄호 및 특수문자 제거, 소문자화
        normalized = re.sub(r'[^\w가-힣\s]', '', self.name)
        normalized = re.sub(r'\s+', ' ', normalized)  # 연속 공백 제거
        return normalized.strip().lower()

    def add_ingredient(
        self,
        ingredient_name: str,
        role: IngredientRole = IngredientRole.MAIN,
        quantity: Optional[str] = None,
        source: IngredientSource = IngredientSource.RULE,
        confidence: Optional[Decimal] = None
    ):
        """재료 추가"""
        # 기존 재료 중복 체크
        existing = [ing for ing in self.ingredients if ing.ingredient_name.lower() == ingredient_name.lower()]
        if existing:
            return existing[0]  # 기존 재료 반환

        ingredient = MenuIngredient(
            menu_id=self.id,
            ingredient_name=ingredient_name,
            role=role,
            quantity=quantity,
            source=source,
            confidence=confidence
        )

        self.ingredients.append(ingredient)
        self.update_timestamp()
        return ingredient

    def remove_ingredient(self, ingredient_name: str):
        """재료 제거"""
        original_count = len(self.ingredients)
        self.ingredients = [
            ing for ing in self.ingredients
            if ing.ingredient_name.lower() != ingredient_name.lower()
        ]

        if len(self.ingredients) < original_count:
            self.update_timestamp()

    def get_ingredients_by_role(self, role: IngredientRole) -> List[MenuIngredient]:
        """역할별 재료 조회"""
        return [ing for ing in self.ingredients if ing.role == role]

    def get_main_ingredients(self) -> List[str]:
        """주재료 이름 리스트"""
        return [ing.ingredient_name for ing in self.ingredients if ing.role == IngredientRole.MAIN]

    def update_basic_info(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        price: Optional[int] = None,
        category: Optional[MenuCategory] = None
    ):
        """기본 정보 업데이트"""
        if name is not None:
            self.name = name.strip()
            self.name_norm = self._normalize_name()

        if description is not None:
            self.description = description.strip() if description else None

        if price is not None:
            if price < 0:
                raise ValueError("Price cannot be negative")
            self.price = price

        if category is not None:
            self.category = category

        self.update_timestamp()

    def update_nutrition_info(self, nutrition_info: NutritionInfo):
        """영양 정보 업데이트"""
        self.nutrition_info = nutrition_info
        self.update_timestamp()

    def set_signature(self, is_signature: bool = True):
        """대표 메뉴 설정"""
        self.is_signature = is_signature
        self.update_timestamp()

    def set_availability(self, is_available: bool):
        """메뉴 가용성 설정"""
        self.is_available = is_available
        self.update_timestamp()

    def add_allergen(self, allergen: str):
        """알러지 유발 요소 추가"""
        allergen = allergen.strip()
        if allergen and allergen not in self.allergens:
            self.allergens.append(allergen)
            self.update_timestamp()

    def remove_allergen(self, allergen: str):
        """알러지 유발 요소 제거"""
        if allergen in self.allergens:
            self.allergens.remove(allergen)
            self.update_timestamp()

    @property
    def has_price(self) -> bool:
        """가격 정보 보유 여부"""
        return self.price is not None

    @property
    def has_nutrition_info(self) -> bool:
        """영양 정보 보유 여부"""
        return self.nutrition_info is not None and self.nutrition_info.has_macronutrients

    @property
    def ingredient_count(self) -> int:
        """재료 개수"""
        return len(self.ingredients)

    @property
    def main_ingredient_names(self) -> List[str]:
        """주재료 이름들"""
        return self.get_main_ingredients()

    @property
    def estimated_carb_content(self) -> Optional[Decimal]:
        """추정 탄수화물 함량"""
        if self.nutrition_info and self.nutrition_info.carbohydrates:
            return self.nutrition_info.carbohydrates
        return None

    def to_summary_dict(self) -> Dict[str, Any]:
        """요약 정보 딕셔너리"""
        return {
            "id": str(self.id),
            "restaurant_id": str(self.restaurant_id),
            "name": self.name,
            "name_norm": self.name_norm,
            "price": self.price,
            "category": self.category.value,
            "is_signature": self.is_signature,
            "is_available": self.is_available,
            "spice_level": self.spice_level.value if self.spice_level else None,
            "allergens": self.allergens,
            "ingredient_count": self.ingredient_count,
            "main_ingredients": self.main_ingredient_names,
            "has_nutrition_info": self.has_nutrition_info
        }