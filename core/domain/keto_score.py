"""
키토 점수 도메인 모델
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from decimal import Decimal
from uuid import UUID

from core.domain.base import BaseEntity
from core.domain.enums import CarbBase

@dataclass
class KetoScore(BaseEntity):
    """키토 점수 엔티티"""

    # 관계
    menu_id: UUID

    # 점수 정보
    score: int                          # 0-100
    confidence_score: Optional[Decimal] = None  # 점수 신뢰도

    # 상세 분석
    reasons_json: Dict[str, Any] = field(default_factory=dict)
    detected_keywords: List[str] = field(default_factory=list)
    penalty_keywords: List[str] = field(default_factory=list)
    bonus_keywords: List[str] = field(default_factory=list)

    # 대체/예외 처리
    substitution_tags: Optional[Dict[str, Any]] = None
    negation_detected: bool = False

    # 최종 판정
    final_carb_base: Optional[CarbBase] = None
    override_reason: Optional[str] = None

    # 품질 관리
    needs_review: bool = False
    reviewed_at: Optional[Any] = None  # datetime
    reviewed_by: Optional[str] = None

    # 시스템 정보
    rule_version: str = "v1.0"
    ingredients_confidence: Optional[Decimal] = None

    def __post_init__(self):
        super().__post_init__()

        # 점수 범위 검증
        if not (0 <= self.score <= 100):
            raise ValueError("Score must be between 0 and 100")

        # 신뢰도 검증
        if self.confidence_score is not None:
            if not (0 <= self.confidence_score <= 1):
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

    menu_id: UUID
    old_score: Optional[int]
    new_score: int
    change_reason: str
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