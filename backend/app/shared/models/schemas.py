"""
Pydantic 스키마 정의
API 요청/응답 모델
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Literal
from datetime import date, datetime
from uuid import UUID

class ChatMessage(BaseModel):
    """채팅 메시지 스키마"""
    message: str = Field(..., description="사용자 메시지")
    location: Optional[Dict[str, float]] = Field(None, description="위치 정보 {lat, lng}")
    radius_km: Optional[float] = Field(5.0, description="검색 반경(km)")
    profile: Optional[Dict[str, Any]] = Field(None, description="사용자 프로필")
    thread_id: Optional[str] = Field(None, description="대화 스레드 ID")
    user_id: Optional[str] = Field(None, description="사용자 ID (로그인 시)")
    guest_id: Optional[str] = Field(None, description="게스트 ID (비로그인 시)")
    chat_history: Optional[List[Dict[str, Any]]] = Field(None, description="게스트 사용자용 채팅 히스토리")
    days: Optional[int] = Field(None, description="식단표 생성 일수")

class ChatResponse(BaseModel):
    """채팅 응답 스키마"""
    response: str = Field(..., description="AI 응답")
    intent: str = Field(..., description="의도 분류")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="검색 결과")
    session_id: Optional[str] = Field(None, description="세션 ID")
    thread_id: Optional[str] = Field(None, description="대화 스레드 ID")
    assistantBatch: Optional[List[Dict[str, Any]]] = Field(None, description="AI 응답 메시지 배열")

class ChatThread(BaseModel):
    """채팅 스레드 스키마"""
    id: str = Field(..., description="스레드 ID")
    title: str = Field(..., description="스레드 제목")
    last_message_at: datetime = Field(..., description="마지막 메시지 시간")
    created_at: datetime = Field(..., description="생성 시간")

class ChatHistory(BaseModel):
    """채팅 히스토리 스키마"""
    id: int = Field(..., description="메시지 ID")
    thread_id: str = Field(..., description="스레드 ID")
    role: str = Field(..., description="역할 (user/assistant)")
    message: str = Field(..., description="메시지 내용")
    created_at: datetime = Field(..., description="생성 시간")
    results: Optional[List[Dict[str, Any]]] = Field(None, description="검색 결과 (식당, 레시피)")

class RecipeBase(BaseModel):
    """레시피 기본 스키마"""
    title: str
    tags: List[str] = []
    ketoized: bool = False
    macros: Optional[Dict[str, int]] = None
    source: Optional[str] = None
    ingredients: Optional[List[Dict[str, Any]]] = None
    steps: List[str] = []
    tips: List[str] = []
    allergen_flags: List[str] = []

class RecipeCreate(RecipeBase):
    """레시피 생성 스키마"""
    pass

class RecipeResponse(RecipeBase):
    """레시피 응답 스키마"""
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class PlaceBase(BaseModel):
    """장소 기본 스키마"""
    name: str
    address: str
    category: Optional[str] = None
    lat: float
    lng: float
    keto_score: Optional[int] = None

class PlaceResponse(PlaceBase):
    """장소 응답 스키마"""
    place_id: str
    why: List[str] = Field([], description="키토 점수 이유")
    tips: List[str] = Field([], description="주문 팁")
    source_url: Optional[str] = Field(None, description="출처 URL")
    
class PlaceSearchRequest(BaseModel):
    """장소 검색 요청 스키마"""
    query: str = Field(..., description="검색 키워드")
    lat: float = Field(..., description="위도")
    lng: float = Field(..., description="경도")
    radius: int = Field(1000, description="검색 반경(m)")
    category: Optional[str] = Field(None, description="카테고리 필터")

class PlanBase(BaseModel):
    """플랜 기본 스키마"""
    date: date
    slot: Literal['breakfast', 'lunch', 'dinner', 'snack']
    type: Literal['recipe', 'place']
    ref_id: str
    title: str
    url: Optional[str] = None  # ✅ URL 필드 추가
    location: Optional[Dict[str, str]] = None
    macros: Optional[Dict[str, int]] = None
    notes: Optional[str] = None

class PlanCreate(PlanBase):
    """플랜 생성 스키마"""
    pass

class PlanUpdate(BaseModel):
    """플랜 업데이트 스키마"""
    status: Optional[Literal['planned', 'done', 'skipped']] = None
    notes: Optional[str] = None

class PlanResponse(PlanBase):
    """플랜 응답 스키마"""
    id: str
    user_id: str
    status: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

class MealPlanRequest(BaseModel):
    """식단표 생성 요청 스키마"""
    days: int = Field(7, description="생성할 일수")
    kcal_target: Optional[int] = Field(None, description="목표 칼로리")
    carbs_max: Optional[int] = Field(30, description="최대 탄수화물(g)")
    allergies: List[str] = Field([], description="알레르기")
    dislikes: List[str] = Field([], description="비선호 음식")

class MealPlanResponse(BaseModel):
    """식단표 응답 스키마"""
    days: List[Dict[str, Any]]
    total_macros: Dict[str, int]
    notes: List[str]

class UserProfile(BaseModel):
    """사용자 프로필 스키마"""
    nickname: Optional[str] = None
    goals_kcal: Optional[int] = None
    goals_carbs_g: Optional[int] = None
    allergies: List[str] = []
    dislikes: List[str] = []

class WeightRecord(BaseModel):
    """체중 기록 스키마"""
    date: date
    weight_kg: float

class StatsSummary(BaseModel):
    """통계 요약 스키마"""
    compliance_rate: float = Field(..., description="이행률(%)")
    avg_carbs: float = Field(..., description="평균 탄수화물(g)")
    dining_out_ratio: float = Field(..., description="외식 비중(%)")
    total_days: int = Field(..., description="총 일수")
