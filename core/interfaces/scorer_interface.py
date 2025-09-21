"""
키토 점수화 인터페이스 정의
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from core.domain.menu import Menu
from core.domain.keto_score import KetoScore

class ScoreConfidenceLevel(Enum):
    """점수 신뢰도 레벨"""
    HIGH = "high"          # 0.8 이상
    MEDIUM = "medium"      # 0.5-0.8
    LOW = "low"            # 0.3-0.5
    VERY_LOW = "very_low"  # 0.3 미만

class RecommendationLevel(Enum):
    """추천 레벨"""
    KETO_RECOMMENDED = "keto_recommended"    # 80점 이상
    CONDITIONALLY_KETO = "conditionally_keto"  # 50-79점
    NOT_RECOMMENDED = "not_recommended"      # 50점 미만

@dataclass
class ScoringResult:
    """점수화 결과"""
    menu_id: str
    score: int                           # 0-100
    confidence: float                    # 0.0-1.0
    recommendation: RecommendationLevel

    # 상세 분석
    detected_keywords: List[str]
    penalty_keywords: List[str]
    bonus_keywords: List[str]

    # 대체/예외 처리
    substitution_detected: bool
    negation_detected: bool
    substitution_tags: Optional[Dict[str, Any]]

    # 최종 판정
    final_carb_base: Optional[str]
    needs_review: bool

    # 근거
    scoring_reasons: Dict[str, Any]
    rule_version: str

class MatchType(Enum):
    """매치 타입"""
    HIGH_CARB = "high_carb"
    KETO_FRIENDLY = "keto_friendly"
    SUBSTITUTION = "substitution"
    NEGATION = "negation"
    MENU_TYPE = "menu_type"

@dataclass
class KeywordMatch:
    """키워드 매칭 결과"""
    keyword: str
    match_type: MatchType
    weight: float
    confidence: float
    position: int           # 텍스트 내 위치
    context: str = ""       # 주변 컨텍스트

@dataclass
class ScoringRule:
    """스코어링 룰"""
    rule_id: str
    description: str
    weight_multiplier: float = 1.0
    confidence_threshold: float = 0.5
    enabled: bool = True

@dataclass
class RuleResult:
    """룰 적용 결과"""
    rule_id: str
    applied: bool
    impact: float
    explanation: str

@dataclass
class ScoringContext:
    """점수화 컨텍스트"""
    menu_name: str
    menu_description: Optional[str] = None
    restaurant_category: Optional[str] = None
    menu_category: Optional[str] = None
    price: Optional[int] = None

class KeywordMatcherInterface(ABC):
    """키워드 매칭 인터페이스"""

    @abstractmethod
    async def find_keywords(self, text: str, category: str = None) -> List[KeywordMatch]:
        """텍스트에서 키워드 찾기"""
        pass

    @abstractmethod
    def get_keyword_weight(self, keyword: str, category: str) -> float:
        """키워드 가중치 반환"""
        pass

    @abstractmethod
    def load_keywords(self, category: str) -> Dict[str, float]:
        """카테고리별 키워드 로드"""
        pass

class SubstitutionDetectorInterface(ABC):
    """대체/예외 감지 인터페이스"""

    @abstractmethod
    async def detect_substitutions(self, text: str) -> Dict[str, Any]:
        """대체 재료 감지"""
        pass

    @abstractmethod
    async def detect_negations(self, text: str) -> Dict[str, Any]:
        """부정 표현 감지"""
        pass

    @abstractmethod
    async def detect_exclusions(self, text: str) -> Dict[str, Any]:
        """제외 표현 감지 (밥 제외, 면 없이 등)"""
        pass

class RuleEngineInterface(ABC):
    """룰 엔진 인터페이스"""

    @abstractmethod
    async def calculate_base_score(self, context: ScoringContext) -> int:
        """기본 점수 계산"""
        pass

    @abstractmethod
    async def apply_keyword_rules(
        self,
        base_score: int,
        keyword_matches: List[KeywordMatch]
    ) -> int:
        """키워드 룰 적용"""
        pass

    @abstractmethod
    async def apply_substitution_rules(
        self,
        score: int,
        substitutions: Dict[str, Any],
        negations: Dict[str, Any]
    ) -> tuple[int, Dict[str, Any]]:
        """대체/예외 룰 적용"""
        pass

    @abstractmethod
    def determine_needs_review(self, score: int, confidence: float) -> bool:
        """검수 필요 여부 판단"""
        pass

class KetoScorerInterface(ABC):
    """키토 점수화 메인 인터페이스"""

    @abstractmethod
    async def score_menu(self, menu: Menu, context: ScoringContext = None) -> ScoringResult:
        """메뉴 점수화"""
        pass

    @abstractmethod
    async def score_batch(self, menus: List[Menu]) -> List[ScoringResult]:
        """메뉴 일괄 점수화"""
        pass

    @abstractmethod
    async def rescore_with_feedback(
        self,
        menu: Menu,
        feedback_score: int,
        reason: str
    ) -> ScoringResult:
        """피드백을 반영한 재점수화"""
        pass

    @abstractmethod
    def get_scoring_statistics(self) -> Dict[str, Any]:
        """점수화 통계"""
        pass

    @abstractmethod
    def get_rule_version(self) -> str:
        """룰 버전 반환"""
        pass

class QualityReporterInterface(ABC):
    """품질 리포트 인터페이스"""

    @abstractmethod
    async def generate_quality_report(
        self,
        scoring_results: List[ScoringResult]
    ) -> Dict[str, Any]:
        """품질 리포트 생성"""
        pass

    @abstractmethod
    async def export_needs_review(
        self,
        scoring_results: List[ScoringResult],
        output_path: str
    ) -> str:
        """검수 필요 목록 내보내기"""
        pass

    @abstractmethod
    async def calculate_hit_rate(
        self,
        scoring_results: List[ScoringResult],
        sample_size: int = 50
    ) -> Dict[str, float]:
        """감지 히트율 계산"""
        pass

class IKeywordMatcher(ABC):
    """키워드 매처 인터페이스"""
    
    @abstractmethod
    def find_matches(self, text: str) -> List[KeywordMatch]:
        """텍스트에서 키워드 매치 찾기"""
        pass

class IRuleEngine(ABC):
    """룰 엔진 인터페이스"""
    
    @abstractmethod
    def apply_rules(self, menu: Menu) -> KetoScore:
        """메뉴에 룰 적용하여 키토 점수 계산"""
        pass

class IKetoScorer(ABC):
    """키토 스코어러 인터페이스"""
    
    @abstractmethod
    async def calculate_score(self, menu: Menu) -> KetoScore:
        """메뉴의 키토 점수 계산"""
        pass
    
    @abstractmethod
    async def batch_calculate_scores(self, menus: List[Menu]) -> List[KetoScore]:
        """메뉴들의 키토 점수 일괄 계산"""
        pass