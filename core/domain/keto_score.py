"""
키토 점수 도메인 모델
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from decimal import Decimal
from uuid import UUID

from core.domain.base import BaseEntity
from core.domain.enums import CarbBase
from enum import Enum

class ScoreCategory(Enum):
    """키토 점수 카테고리"""
    KETO_RECOMMENDED = "keto_recommended"    # 80점 이상
    KETO_MODERATE = "keto_moderate"          # 50-79점
    KETO_CAUTION = "keto_caution"           # 20-49점
    KETO_AVOID = "keto_avoid"               # 20점 미만

@dataclass
class ScoreReason:
    """점수 산출 근거"""
    rule_id: str
    keyword: str
    impact: float
    explanation: str

@dataclass
class KetoScore(BaseEntity):
    """키토 점수 엔티티 (슈퍼베이스 keto_scores 테이블 구조에 맞춤)"""

    # 관계 (필수 필드)
    menu_id: Optional[UUID] = None
    score: int = 0                          # 0-100

    # 선택적 필드들
    reasons_json: Optional[Dict[str, Any]] = None  # 점수 산출 근거
    rule_version: str = "v1.0"
    prompt_version: Optional[str] = None  # 프롬프트 버전
    valid_until: Optional[str] = None   # 유효 기간
    
    # 추가 필드들 (스코어링 시스템에서 사용)
    confidence: float = 0.5
    raw_score: float = 0.0
    final_score: float = 0.0
    category: Optional[ScoreCategory] = None
    reasons: List[ScoreReason] = field(default_factory=list)
    detected_keywords: List[str] = field(default_factory=list)
    applied_rules: List[str] = field(default_factory=list)
    calculated_at: Optional[Any] = None
    keto_friendly_ingredients: List[str] = field(default_factory=list)
    high_carb_ingredients: List[str] = field(default_factory=list)
    substitution_suggestions: List[str] = field(default_factory=list)

    def __post_init__(self):
        super().__post_init__()

        # 점수 범위 검증
        if not (0 <= self.score <= 100):
            raise ValueError("Score must be between 0 and 100")

        # 신뢰도 검증
        if self.confidence is not None:
            if not (0 <= self.confidence <= 1):
                raise ValueError("Confidence score must be between 0 and 1")

    @property
    def recommendation_label(self) -> str:
        """추천 라벨"""
        if self.score >= 80:
            return "키토 권장"
        elif self.score >= 50:
            return "조건부 키토"
        else:
            return "비추천"

    @property
    def is_estimated(self) -> bool:
        """추정 여부"""
        return (self.ingredients_confidence is not None and
                self.ingredients_confidence < Decimal('0.5'))

    @property
    def has_substitution(self) -> bool:
        """대체 재료 여부"""
        return bool(self.substitution_tags)

    @property
    def has_negation(self) -> bool:
        """부정 표현 여부"""
        return self.negation_detected

    def add_keyword(self, keyword: str, category: str, weight: float = 0.0):
        """키워드 추가"""
        if category == 'penalty':
            if keyword not in self.penalty_keywords:
                self.penalty_keywords.append(keyword)
        elif category == 'bonus':
            if keyword not in self.bonus_keywords:
                self.bonus_keywords.append(keyword)

        if keyword not in self.detected_keywords:
            self.detected_keywords.append(keyword)

        self.update_timestamp()

    def add_substitution_tag(self, tag_type: str, value: Any):
        """대체 태그 추가"""
        if self.substitution_tags is None:
            self.substitution_tags = {}

        self.substitution_tags[tag_type] = value
        self.update_timestamp()

    def add_scoring_reason(self, reason_type: str, details: Any):
        """점수화 근거 추가"""
        self.reasons_json[reason_type] = details
        self.update_timestamp()

    def mark_for_review(self, reason: str = None):
        """검수 필요로 표시"""
        self.needs_review = True
        if reason:
            self.add_scoring_reason('review_reason', reason)
        self.update_timestamp()

    def complete_review(self, reviewer: str, approved: bool = True):
        """검수 완료"""
        from datetime import datetime
        self.needs_review = False
        self.reviewed_at = datetime.utcnow()
        self.reviewed_by = reviewer

        self.add_scoring_reason('review_result', {
            'approved': approved,
            'reviewed_by': reviewer,
            'reviewed_at': self.reviewed_at.isoformat()
        })

        self.update_timestamp()

    def override_score(self, new_score: int, reason: str):
        """점수 수동 조정"""
        if not (0 <= new_score <= 100):
            raise ValueError("Score must be between 0 and 100")

        old_score = self.score
        self.score = new_score
        self.override_reason = reason

        self.add_scoring_reason('score_override', {
            'old_score': old_score,
            'new_score': new_score,
            'reason': reason
        })

        self.update_timestamp()

    def get_summary(self) -> Dict[str, Any]:
        """요약 정보"""
        return {
            'menu_id': str(self.menu_id),
            'score': self.score,
            'recommendation': self.recommendation_label,
            'confidence': float(self.confidence_score) if self.confidence_score else None,
            'final_carb_base': self.final_carb_base.value if self.final_carb_base else None,
            'needs_review': self.needs_review,
            'is_estimated': self.is_estimated,
            'has_substitution': self.has_substitution,
            'has_negation': self.has_negation,
            'detected_keywords_count': len(self.detected_keywords),
            'rule_version': self.rule_version
        }

    def get_detailed_analysis(self) -> Dict[str, Any]:
        """상세 분석 정보"""
        return {
            **self.get_summary(),
            'detected_keywords': self.detected_keywords,
            'penalty_keywords': self.penalty_keywords,
            'bonus_keywords': self.bonus_keywords,
            'substitution_tags': self.substitution_tags,
            'reasons': self.reasons_json,
            'override_reason': self.override_reason,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None
        }

@dataclass
class KetoScoreHistory(BaseEntity):
    """키토 점수 변경 이력"""

    menu_id: Optional[UUID] = None
    old_score: Optional[int] = None
    new_score: int = 0
    change_reason: str = ""
    changed_by: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()

        # 점수 범위 검증
        if self.new_score is not None and not (0 <= self.new_score <= 100):
            raise ValueError("New score must be between 0 and 100")

        if self.old_score is not None and not (0 <= self.old_score <= 100):
            raise ValueError("Old score must be between 0 and 100")

class KetoScoringRule:
    """키토 점수화 룰 (값 객체)"""

    def __init__(
        self,
        rule_version: str = "v1.0",
        base_score: int = 50,
        high_carb_penalty: int = 60,
        keto_friendly_bonus: int = 20,
        menu_type_penalty: int = 15,
        substitution_bonus: int = 10,
        negation_offset: float = 0.5,
        review_threshold_min: int = 35,
        review_threshold_max: int = 45
    ):
        self.rule_version = rule_version
        self.base_score = base_score
        self.high_carb_penalty = high_carb_penalty
        self.keto_friendly_bonus = keto_friendly_bonus
        self.menu_type_penalty = menu_type_penalty
        self.substitution_bonus = substitution_bonus
        self.negation_offset = negation_offset
        self.review_threshold_min = review_threshold_min
        self.review_threshold_max = review_threshold_max

    def is_review_needed(self, score: int) -> bool:
        """검수 필요 여부 판단"""
        return self.review_threshold_min <= score <= self.review_threshold_max

    def calculate_confidence(
        self,
        keyword_count: int,
        substitution_detected: bool,
        negation_detected: bool
    ) -> float:
        """신뢰도 계산"""
        confidence = 0.3  # 기본 신뢰도

        # 키워드 개수에 따른 신뢰도 증가
        confidence += min(keyword_count * 0.1, 0.4)

        # 대체/부정 감지시 신뢰도 조정
        if substitution_detected:
            confidence += 0.2
        if negation_detected:
            confidence += 0.1

        return min(confidence, 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            'rule_version': self.rule_version,
            'base_score': self.base_score,
            'high_carb_penalty': self.high_carb_penalty,
            'keto_friendly_bonus': self.keto_friendly_bonus,
            'menu_type_penalty': self.menu_type_penalty,
            'substitution_bonus': self.substitution_bonus,
            'negation_offset': self.negation_offset,
            'review_threshold_min': self.review_threshold_min,
            'review_threshold_max': self.review_threshold_max
        }