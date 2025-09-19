from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from core.domain.menu import Menu
from core.domain.keto_score import KetoScore, ScoreCategory
from services.quality.quality_reporter import QualityReport, QualityLevel


class ReviewStatus(Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CORRECTION = "needs_correction"


class ReviewPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ReviewItem:
    """검수 항목"""
    item_id: str
    menu: Menu
    score: KetoScore
    priority: ReviewPriority
    status: ReviewStatus
    issues: List[str]
    created_at: datetime
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: str = ""
    corrections: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewRule:
    """검수 룰"""
    rule_id: str
    description: str
    condition: Callable[[Menu, KetoScore], bool]
    priority: ReviewPriority
    auto_assignable: bool = True


class ReviewSystem:
    """검수 시스템"""

    def __init__(self):
        self.review_rules = self._initialize_review_rules()
        self.review_queue: List[ReviewItem] = []

    def _initialize_review_rules(self) -> List[ReviewRule]:
        """검수 룰 초기화"""
        return [
            ReviewRule(
                rule_id="low_confidence",
                description="신뢰도가 낮은 점수",
                condition=lambda menu, score: score.confidence < 0.3,
                priority=ReviewPriority.HIGH
            ),
            ReviewRule(
                rule_id="extreme_positive_score",
                description="극단적으로 높은 점수",
                condition=lambda menu, score: score.final_score >= 90,
                priority=ReviewPriority.MEDIUM
            ),
            ReviewRule(
                rule_id="extreme_negative_score",
                description="극단적으로 낮은 점수",
                condition=lambda menu, score: score.final_score <= -90,
                priority=ReviewPriority.MEDIUM
            ),
            ReviewRule(
                rule_id="no_keywords",
                description="키워드가 전혀 감지되지 않음",
                condition=lambda menu, score: len(score.detected_keywords) == 0,
                priority=ReviewPriority.HIGH
            ),
            ReviewRule(
                rule_id="conflicting_keywords",
                description="상충하는 키워드들",
                condition=lambda menu, score: self._has_conflicting_keywords(score),
                priority=ReviewPriority.MEDIUM
            ),
            ReviewRule(
                rule_id="short_menu_name",
                description="메뉴명이 너무 짧음",
                condition=lambda menu, score: len(menu.name) <= 2,
                priority=ReviewPriority.LOW
            ),
            ReviewRule(
                rule_id="no_description",
                description="메뉴 설명이 없음",
                condition=lambda menu, score: not menu.description or len(menu.description.strip()) < 3,
                priority=ReviewPriority.LOW
            ),
            ReviewRule(
                rule_id="unusual_price",
                description="비정상적인 가격",
                condition=lambda menu, score: menu.price and (menu.price < 1000 or menu.price > 100000),
                priority=ReviewPriority.LOW
            ),
            ReviewRule(
                rule_id="many_rules_applied",
                description="너무 많은 룰이 적용됨",
                condition=lambda menu, score: len(score.applied_rules) >= 5,
                priority=ReviewPriority.MEDIUM
            ),
            ReviewRule(
                rule_id="score_reason_mismatch",
                description="점수와 사유가 불일치",
                condition=lambda menu, score: self._score_reason_mismatch(score),
                priority=ReviewPriority.HIGH
            )
        ]

    def _has_conflicting_keywords(self, score: KetoScore) -> bool:
        """상충하는 키워드 감지"""
        keywords = score.detected_keywords

        # 키토 친화적 키워드와 고탄수화물 키워드가 동시에 있는 경우
        keto_keywords = ['연어', '스테이크', '아보카도', '사시미']
        carb_keywords = ['밥', '면', '빵', '파스타', '라면']

        has_keto = any(k in keywords for k in keto_keywords)
        has_carb = any(k in keywords for k in carb_keywords)

        return has_keto and has_carb

    def _score_reason_mismatch(self, score: KetoScore) -> bool:
        """점수와 사유 불일치 감지"""
        # 점수가 양수인데 부정적인 키워드만 있는 경우
        if score.final_score > 20:
            negative_reasons = [r for r in score.reasons if r.impact < 0]
            positive_reasons = [r for r in score.reasons if r.impact > 0]
            return len(negative_reasons) > len(positive_reasons) * 2

        # 점수가 음수인데 긍정적인 키워드만 있는 경우
        if score.final_score < -20:
            negative_reasons = [r for r in score.reasons if r.impact < 0]
            positive_reasons = [r for r in score.reasons if r.impact > 0]
            return len(positive_reasons) > len(negative_reasons) * 2

        return False

    async def process_quality_report(self, quality_report: QualityReport, menus: List[Menu], scores: List[KetoScore]):
        """품질 리포트를 기반으로 검수 항목 생성"""

        # 기존 검수 대기 중인 항목들과 중복 체크
        existing_menu_ids = {item.menu.id for item in self.review_queue if item.status == ReviewStatus.PENDING}

        for menu, score in zip(menus, scores):
            if menu.id in existing_menu_ids:
                continue  # 이미 검수 대기 중

            # 각 룰 적용하여 검수 필요성 확인
            triggered_rules = []
            for rule in self.review_rules:
                if rule.condition(menu, score):
                    triggered_rules.append(rule)

            if triggered_rules:
                # 가장 높은 우선순위 설정
                max_priority = max(rule.priority for rule in triggered_rules)

                review_item = ReviewItem(
                    item_id=f"RI_{menu.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    menu=menu,
                    score=score,
                    priority=max_priority,
                    status=ReviewStatus.PENDING,
                    issues=[rule.description for rule in triggered_rules],
                    created_at=datetime.now()
                )

                self.review_queue.append(review_item)

        # 우선순위별로 정렬
        self.review_queue.sort(key=lambda x: (-x.priority.value, x.created_at))

    def get_review_queue(self, status: Optional[ReviewStatus] = None, limit: Optional[int] = None) -> List[ReviewItem]:
        """검수 대기열 조회"""
        items = self.review_queue

        if status:
            items = [item for item in items if item.status == status]

        if limit:
            items = items[:limit]

        return items

    def assign_review(self, item_id: str, reviewer_id: str) -> bool:
        """검수 할당"""
        for item in self.review_queue:
            if item.item_id == item_id and item.status == ReviewStatus.PENDING:
                item.status = ReviewStatus.IN_REVIEW
                item.reviewer_id = reviewer_id
                return True
        return False

    def complete_review(
        self,
        item_id: str,
        status: ReviewStatus,
        review_notes: str = "",
        corrections: Optional[Dict[str, Any]] = None
    ) -> bool:
        """검수 완료"""
        for item in self.review_queue:
            if item.item_id == item_id and item.status == ReviewStatus.IN_REVIEW:
                item.status = status
                item.reviewed_at = datetime.now()
                item.review_notes = review_notes
                if corrections:
                    item.corrections = corrections
                return True
        return False

    def get_review_statistics(self) -> Dict[str, Any]:
        """검수 통계"""
        total_items = len(self.review_queue)

        status_counts = {}
        for status in ReviewStatus:
            status_counts[status.value] = len([item for item in self.review_queue if item.status == status])

        priority_counts = {}
        for priority in ReviewPriority:
            priority_counts[priority.name.lower()] = len([
                item for item in self.review_queue
                if item.priority == priority and item.status == ReviewStatus.PENDING
            ])

        # 검수자별 통계
        reviewer_stats = {}
        for item in self.review_queue:
            if item.reviewer_id:
                if item.reviewer_id not in reviewer_stats:
                    reviewer_stats[item.reviewer_id] = {'assigned': 0, 'completed': 0}

                reviewer_stats[item.reviewer_id]['assigned'] += 1
                if item.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]:
                    reviewer_stats[item.reviewer_id]['completed'] += 1

        return {
            'total_items': total_items,
            'status_distribution': status_counts,
            'priority_distribution': priority_counts,
            'reviewer_statistics': reviewer_stats,
            'completion_rate': (
                status_counts.get('approved', 0) + status_counts.get('rejected', 0)
            ) / max(total_items, 1) * 100
        }

    def generate_review_recommendations(self, item_id: str) -> List[str]:
        """검수 항목에 대한 추천사항 생성"""
        item = next((item for item in self.review_queue if item.item_id == item_id), None)
        if not item:
            return []

        recommendations = []

        # 신뢰도 관련
        if item.score.confidence < 0.3:
            recommendations.extend([
                "메뉴명이나 설명에서 더 명확한 키워드를 찾아보세요",
                "유사한 메뉴의 점수와 비교해보세요",
                "식당의 전체적인 메뉴 스타일을 고려해보세요"
            ])

        # 키워드 없음
        if not item.score.detected_keywords:
            recommendations.extend([
                "메뉴명을 다시 한 번 확인해보세요",
                "일반적이지 않은 메뉴명일 수 있습니다",
                "키워드 사전에 추가가 필요한지 검토하세요"
            ])

        # 극단적 점수
        if abs(item.score.final_score) >= 80:
            recommendations.extend([
                "점수가 극단적입니다. 계산 과정을 검토하세요",
                "해당 메뉴가 정말 이 점수를 받을 만한지 확인하세요"
            ])

        # 상충하는 키워드
        if self._has_conflicting_keywords(item.score):
            recommendations.extend([
                "키토 친화적 재료와 탄수화물이 함께 감지되었습니다",
                "메뉴의 주재료가 무엇인지 파악하세요",
                "부가 재료와 주재료를 구분해서 판단하세요"
            ])

        return recommendations

    def auto_resolve_simple_issues(self) -> int:
        """간단한 이슈 자동 해결"""
        resolved_count = 0

        for item in self.review_queue:
            if item.status != ReviewStatus.PENDING:
                continue

            # 메뉴명이 너무 짧은 경우 - 설명이 있으면 승인
            if "메뉴명이 너무 짧음" in item.issues and item.menu.description:
                item.status = ReviewStatus.APPROVED
                item.review_notes = "자동 승인: 설명이 충분함"
                item.reviewed_at = datetime.now()
                resolved_count += 1

            # 설명이 없지만 점수가 명확한 경우
            elif "메뉴 설명이 없음" in item.issues and item.score.confidence > 0.7:
                item.status = ReviewStatus.APPROVED
                item.review_notes = "자동 승인: 신뢰도 충분함"
                item.reviewed_at = datetime.now()
                resolved_count += 1

        return resolved_count

    def export_review_data(self) -> Dict[str, Any]:
        """검수 데이터 내보내기 (분석용)"""
        return {
            'export_time': datetime.now().isoformat(),
            'review_items': [
                {
                    'item_id': item.item_id,
                    'menu_name': item.menu.name,
                    'menu_description': item.menu.description,
                    'score': item.score.final_score,
                    'confidence': item.score.confidence,
                    'category': item.score.category.value,
                    'detected_keywords': item.score.detected_keywords,
                    'priority': item.priority.name,
                    'status': item.status.value,
                    'issues': item.issues,
                    'created_at': item.created_at.isoformat(),
                    'reviewed_at': item.reviewed_at.isoformat() if item.reviewed_at else None,
                    'reviewer_id': item.reviewer_id,
                    'review_notes': item.review_notes
                }
                for item in self.review_queue
            ],
            'statistics': self.get_review_statistics()
        }

    def clear_completed_reviews(self, days_old: int = 30) -> int:
        """완료된 검수 항목 정리"""
        cutoff_date = datetime.now() - timedelta(days=days_old)

        initial_count = len(self.review_queue)

        self.review_queue = [
            item for item in self.review_queue
            if not (
                item.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED] and
                item.reviewed_at and item.reviewed_at < cutoff_date
            )
        ]

        return initial_count - len(self.review_queue)