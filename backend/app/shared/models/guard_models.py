"""
가드레일 공통 모델
사용자 입력 검증 및 보정을 위한 데이터 모델
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Literal, Union
from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    """가드레일 에러 코드"""
    MISSING_SLOT = "MISSING_SLOT"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    OFF_TOPIC = "OFF_TOPIC"
    SAFETY = "SAFETY"
    INJECTION = "INJECTION"
    INPUT_TOO_LONG = "INPUT_TOO_LONG"


class IntentType(str, Enum):
    """의도 분류 타입"""
    MEAL_PLANNING = "MEAL_PLANNING"
    RESTAURANT_SEARCH = "RESTAURANT_SEARCH"
    BOTH = "BOTH"
    GENERAL = "GENERAL"


class TimeOfDay(str, Enum):
    """끼니 타입"""
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    DINNER = "dinner"
    SNACK = "snack"


class SpiceLevel(str, Enum):
    """매운 정도"""
    MILD = "mild"
    MEDIUM = "medium"
    HOT = "hot"


class GuardRequest(BaseModel):
    """가드레일 요청 모델"""
    utterance: str = Field(..., description="사용자 메시지")
    expected_intent: Optional[IntentType] = Field(default=None, description="예상 의도")
    slots: Optional[Dict[str, Any]] = Field(default_factory=dict, description="슬롯 데이터")


class GuardSuccessResponse(BaseModel):
    """가드레일 성공 응답"""
    ok: bool = Field(True, description="성공 여부")
    normalized_slots: Dict[str, Any] = Field(..., description="정규화된 슬롯")
    auto_corrections: Dict[str, Any] = Field(default_factory=dict, description="자동 보정 항목")


class GuardErrorResponse(BaseModel):
    """가드레일 에러 응답"""
    ok: bool = Field(False, description="성공 여부")
    error_code: ErrorCode = Field(..., description="에러 코드")
    message: str = Field(..., description="사용자에게 보여줄 메시지")
    required_slots: Optional[List[str]] = Field(default=None, description="필수 슬롯")
    auto_corrections: Optional[Dict[str, Any]] = Field(default=None, description="시도된 보정")
    hint: Optional[str] = Field(default=None, description="힌트 메시지")


GuardResponse = Union[GuardSuccessResponse, GuardErrorResponse]


class GuardConfig:
    """가드레일 설정 상수"""
    
    # 입력 길이 제한
    MAX_INPUT_LENGTH = 500
    
    # 기본값
    DEFAULT_LOCATION = "강남역"
    DEFAULT_DISTANCE_M = 500
    DEFAULT_BUDGET_KRW = 12000
    DEFAULT_CARB_LIMIT_G = 20
    DEFAULT_KCAL_LIMIT = 600
    
    # 범위 제한
    DISTANCE_MIN = 50
    DISTANCE_MAX = 1000
    BUDGET_MIN = 5000
    BUDGET_MAX = 50000
    CARB_MIN = 0
    CARB_MAX = 100
    KCAL_MIN = 200
    KCAL_MAX = 1200
    
    # 리스트 제한
    MAX_ALLERGIES = 10
    MAX_DISLIKES = 10
    
    # 키워드 매핑 (의도 분류용)
    INTENT_KEYWORDS = {
        IntentType.MEAL_PLANNING: ["레시피", "식단", "요리", "끼니", "아침", "점심", "저녁"],
        IntentType.RESTAURANT_SEARCH: ["식당", "맛집", "추천", "근처", "가게"],
        IntentType.BOTH: ["키토", "저탄고지", "다이어트"]
    }
    
    # 금칙어 (안전성 검증용)
    FORBIDDEN_KEYWORDS = [
        "자살", "폭탄", "증오", "민감질병치료", "치료약", "복용량",
        "의학적", "진단", "치료", "병원", "약물"
    ]
    
    # 오프토픽 키워드
    OFF_TOPIC_KEYWORDS = [
        "주식", "부동산", "게임핵", "암호화폐", "비트코인", "투자",
        "정치", "선거", "대통령", "코로나", "백신"
    ]
    
    # 프롬프트 인젝션 패턴
    INJECTION_PATTERNS = [
        "시스템 규칙 무시", "토큰 유출","토큰", "프롬프트 조작",
        "지시 무시", "역할 변경", "시스템 메시지"
    ]


class StockMessages:
    """고정 메시지 템플릿"""
    
    # 에러 메시지 (사용자 친화적)
    ERROR_MESSAGES = {
        ErrorCode.OFF_TOPIC: "죄송해요! 저는 키토 식단·레시피·강남역 주변 식당 추천만 도와드릴 수 있어요 😊 다른 분야 질문은 답변드리기 어려워요.",
        ErrorCode.MISSING_SLOT: "좀 더 구체적으로 알려주시면 바로 추천해드릴게요! 어느 끼니(아침/점심/저녁)와 탄수 한도(예: 20g)를 알려주세요.",
        ErrorCode.OUT_OF_RANGE: "조건을 조금 조정해서 추천해드릴게요! 더 현실적인 범위로 찾아볼게요 😊",
        ErrorCode.SAFETY: "의학적 조언은 드릴 수 없어요. 대신 일반적인 키토 식단 팁을 안내해드릴게요!",
        ErrorCode.INJECTION: "죄송해요! 키토 식단과 강남역 주변 식당 추천만 도와드릴 수 있어요 😊 다른 질문이 있으시면 말씀해 주세요!",
        ErrorCode.INPUT_TOO_LONG: "질문이 너무 길어요! 500자 이내로 간단하게 작성해주세요 😊"
    }
    
    # 힌트 메시지 (원클릭 보정용)
    HINT_MESSAGES = {
        ErrorCode.MISSING_SLOT: "예) 점심, 탄수 20g 이하로 강남역 500m 내 추천해줘",
        ErrorCode.OFF_TOPIC: "예) 강남역 근처 키토 식당 추천해줘",
        ErrorCode.OUT_OF_RANGE: "예) 강남역 500m 내 1만원 이하 식당 추천해줘",
        ErrorCode.SAFETY: "예) 키토 식단에서 좋은 지방 음식 추천해줘",
        ErrorCode.INJECTION: "예) 강남역 근처 키토 식당 추천해줘",
        ErrorCode.INPUT_TOO_LONG: "예) 강남역 근처 탄수 20g 이하 키토 식당 추천해줘"
    }
    
    # 성공 메시지 (자동 보정 알림)
    SUCCESS_MESSAGES = {
        "location_corrected": "위치를 강남역으로 설정하고 추천해드릴게요!",
        "distance_corrected": "거리를 500m로 조정하고 추천해드릴게요!",
        "budget_corrected": "예산을 12,000원으로 조정하고 추천해드릴게요!"
    }
