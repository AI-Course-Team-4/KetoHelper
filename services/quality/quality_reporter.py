from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import statistics

from core.domain.menu import Menu
from core.domain.keto_score import KetoScore, ScoreCategory
from services.scorer.keto_scorer import KetoScorer


class QualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class QualityIssue:
    """품질 이슈"""
    issue_type: str
    severity: QualityLevel
    description: str
    affected_items: List[str]
    recommendation: str
    auto_fixable: bool = False


@dataclass
class QualityMetrics:
    """품질 지표"""
    total_items: int
    scored_items: int
    high_confidence_items: int
    low_confidence_items: int
    avg_confidence: float
    keyword_coverage: float
    issues: List[QualityIssue] = field(default_factory=list)


@dataclass
class QualityReport:
    """품질 리포트"""
    report_id: str
    generated_at: datetime
    restaurant_id: Optional[str]
    overall_quality: QualityLevel
    metrics: QualityMetrics
    detailed_analysis: Dict[str, Any]
    recommendations: List[str]
    needs_review: List[str]


class QualityReporter:
    """품질 리포트 및 검수 시스템"""

    def __init__(self, keto_scorer: KetoScorer):
        self.keto_scorer = keto_scorer

        # 품질 기준
        self.quality_thresholds = {
            'min_confidence': 0.5,
            'low_confidence_limit': 0.3,
            'keyword_coverage_min': 0.7,
            'max_no_keyword_ratio': 0.2
        }

    async def generate_quality_report(
        self,
        menus: List[Menu],
        restaurant_id: Optional[str] = None
    ) -> QualityReport:
        """품질 리포트 생성"""

        # 모든 메뉴 점수 계산
        scores = await self.keto_scorer.batch_calculate_scores(menus)

        # 품질 지표 계산
        metrics = self._calculate_metrics(menus, scores)

        # 품질 이슈 감지
        issues = self._detect_quality_issues(menus, scores)
        metrics.issues = issues

        # 전체 품질 등급 결정
        overall_quality = self._determine_overall_quality(metrics)

        # 상세 분석
        detailed_analysis = self._perform_detailed_analysis(menus, scores)

        # 추천사항 생성
        recommendations = self._generate_recommendations(metrics, issues)

        # 검수 필요 항목
        needs_review = self._identify_review_items(menus, scores)

        return QualityReport(
            report_id=f"QR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            generated_at=datetime.now(),
            restaurant_id=restaurant_id,
            overall_quality=overall_quality,
            metrics=metrics,
            detailed_analysis=detailed_analysis,
            recommendations=recommendations,
            needs_review=needs_review
        )

    def _calculate_metrics(self, menus: List[Menu], scores: List[KetoScore]) -> QualityMetrics:
        """품질 지표 계산"""
        total_items = len(menus)

        if total_items == 0:
            return QualityMetrics(
                total_items=0,
                scored_items=0,
                high_confidence_items=0,
                low_confidence_items=0,
                avg_confidence=0.0,
                keyword_coverage=0.0
            )

        scored_items = len(scores)
        confidences = [score.confidence for score in scores]
        avg_confidence = statistics.mean(confidences) if confidences else 0.0

        high_confidence_items = len([c for c in confidences if c >= self.quality_thresholds['min_confidence']])
        low_confidence_items = len([c for c in confidences if c < self.quality_thresholds['low_confidence_limit']])

        # 키워드 감지율 계산
        items_with_keywords = len([score for score in scores if score.detected_keywords])
        keyword_coverage = items_with_keywords / total_items if total_items > 0 else 0.0

        return QualityMetrics(
            total_items=total_items,
            scored_items=scored_items,
            high_confidence_items=high_confidence_items,
            low_confidence_items=low_confidence_items,
            avg_confidence=avg_confidence,
            keyword_coverage=keyword_coverage
        )

    def _detect_quality_issues(self, menus: List[Menu], scores: List[KetoScore]) -> List[QualityIssue]:
        """품질 이슈 감지"""
        issues = []

        # 1. 낮은 신뢰도 이슈
        low_confidence_items = [
            f"{menu.name} (신뢰도: {score.confidence:.2f})"
            for menu, score in zip(menus, scores)
            if score.confidence < self.quality_thresholds['low_confidence_limit']
        ]

        if low_confidence_items:
            issues.append(QualityIssue(
                issue_type="low_confidence",
                severity=QualityLevel.POOR if len(low_confidence_items) > len(menus) * 0.3 else QualityLevel.FAIR,
                description=f"신뢰도가 낮은 항목이 {len(low_confidence_items)}개 발견됨",
                affected_items=low_confidence_items[:10],  # 최대 10개만 표시
                recommendation="메뉴명이나 설명을 더 상세히 수집하거나 키워드 사전을 보완하세요",
                auto_fixable=False
            ))

        # 2. 키워드 미감지 이슈
        no_keyword_items = [
            menu.name for menu, score in zip(menus, scores)
            if not score.detected_keywords
        ]

        if len(no_keyword_items) > len(menus) * self.quality_thresholds['max_no_keyword_ratio']:
            issues.append(QualityIssue(
                issue_type="no_keywords",
                severity=QualityLevel.POOR,
                description=f"키워드가 전혀 감지되지 않은 항목이 {len(no_keyword_items)}개",
                affected_items=no_keyword_items[:10],
                recommendation="키워드 사전을 확장하거나 메뉴 데이터 품질을 개선하세요",
                auto_fixable=False
            ))

        # 3. 극단적 점수 이슈
        extreme_scores = [
            f"{menu.name} (점수: {score.final_score})"
            for menu, score in zip(menus, scores)
            if abs(score.final_score) >= 90
        ]

        if extreme_scores:
            issues.append(QualityIssue(
                issue_type="extreme_scores",
                severity=QualityLevel.FAIR,
                description=f"극단적 점수를 받은 항목이 {len(extreme_scores)}개",
                affected_items=extreme_scores,
                recommendation="점수가 극단적인 항목들을 수동으로 검토하세요",
                auto_fixable=False
            ))

        # 4. 빈 메뉴 설명 이슈
        empty_description_count = len([menu for menu in menus if not menu.description or len(menu.description.strip()) < 5])

        if empty_description_count > len(menus) * 0.5:
            issues.append(QualityIssue(
                issue_type="empty_descriptions",
                severity=QualityLevel.FAIR,
                description=f"메뉴 설명이 부족한 항목이 {empty_description_count}개",
                affected_items=[],
                recommendation="메뉴 설명 수집을 개선하세요",
                auto_fixable=False
            ))

        return issues

    def _determine_overall_quality(self, metrics: QualityMetrics) -> QualityLevel:
        """전체 품질 등급 결정"""
        score = 0

        # 신뢰도 점수 (40점)
        if metrics.avg_confidence >= 0.8:
            score += 40
        elif metrics.avg_confidence >= 0.6:
            score += 30
        elif metrics.avg_confidence >= 0.4:
            score += 20
        else:
            score += 10

        # 키워드 커버리지 점수 (30점)
        if metrics.keyword_coverage >= 0.9:
            score += 30
        elif metrics.keyword_coverage >= 0.7:
            score += 20
        elif metrics.keyword_coverage >= 0.5:
            score += 15
        else:
            score += 5

        # 이슈 개수에 따른 감점 (30점에서 차감)
        issue_penalty = len([issue for issue in metrics.issues if issue.severity in [QualityLevel.POOR, QualityLevel.CRITICAL]]) * 10
        score += max(0, 30 - issue_penalty)

        # 등급 결정
        if score >= 85:
            return QualityLevel.EXCELLENT
        elif score >= 70:
            return QualityLevel.GOOD
        elif score >= 50:
            return QualityLevel.FAIR
        elif score >= 30:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL

    def _perform_detailed_analysis(self, menus: List[Menu], scores: List[KetoScore]) -> Dict[str, Any]:
        """상세 분석"""
        if not scores:
            return {'error': '분석할 데이터가 없습니다'}

        # 점수 분포
        score_distribution = {
            'excellent': len([s for s in scores if s.category == ScoreCategory.KETO_EXCELLENT]),
            'good': len([s for s in scores if s.category == ScoreCategory.KETO_GOOD]),
            'moderate': len([s for s in scores if s.category == ScoreCategory.KETO_MODERATE]),
            'poor': len([s for s in scores if s.category == ScoreCategory.KETO_POOR]),
            'avoid': len([s for s in scores if s.category == ScoreCategory.KETO_AVOID])
        }

        # 키워드 빈도 분석
        all_keywords = []
        for score in scores:
            all_keywords.extend(score.detected_keywords)

        keyword_frequency = {}
        for keyword in all_keywords:
            keyword_frequency[keyword] = keyword_frequency.get(keyword, 0) + 1

        top_keywords = sorted(keyword_frequency.items(), key=lambda x: x[1], reverse=True)[:10]

        # 룰 적용 통계
        all_rules = []
        for score in scores:
            all_rules.extend(score.applied_rules)

        rule_frequency = {}
        for rule in all_rules:
            rule_frequency[rule] = rule_frequency.get(rule, 0) + 1

        return {
            'score_statistics': {
                'mean': statistics.mean([s.final_score for s in scores]),
                'median': statistics.median([s.final_score for s in scores]),
                'std_dev': statistics.stdev([s.final_score for s in scores]) if len(scores) > 1 else 0,
                'min': min([s.final_score for s in scores]),
                'max': max([s.final_score for s in scores])
            },
            'confidence_statistics': {
                'mean': statistics.mean([s.confidence for s in scores]),
                'median': statistics.median([s.confidence for s in scores]),
                'min': min([s.confidence for s in scores]),
                'max': max([s.confidence for s in scores])
            },
            'category_distribution': score_distribution,
            'top_keywords': top_keywords,
            'rule_usage': rule_frequency,
            'data_completeness': {
                'menus_with_description': len([m for m in menus if m.description]),
                'menus_with_price': len([m for m in menus if m.price]),
                'avg_name_length': statistics.mean([len(m.name) for m in menus]),
                'avg_description_length': statistics.mean([len(m.description or '') for m in menus])
            }
        }

    def _generate_recommendations(self, metrics: QualityMetrics, issues: List[QualityIssue]) -> List[str]:
        """추천사항 생성"""
        recommendations = []

        # 신뢰도 개선
        if metrics.avg_confidence < 0.6:
            recommendations.append("전체적인 신뢰도가 낮습니다. 메뉴 데이터의 품질을 개선하거나 키워드 사전을 보완하세요.")

        # 키워드 커버리지 개선
        if metrics.keyword_coverage < 0.7:
            recommendations.append("키워드 감지율이 낮습니다. 더 다양한 키워드를 사전에 추가하세요.")

        # 이슈별 추천사항
        for issue in issues:
            if issue.severity in [QualityLevel.POOR, QualityLevel.CRITICAL]:
                recommendations.append(f"🔴 {issue.recommendation}")
            elif issue.severity == QualityLevel.FAIR:
                recommendations.append(f"🟡 {issue.recommendation}")

        # 데이터 수집 개선
        if metrics.total_items < 10:
            recommendations.append("메뉴 데이터가 부족합니다. 더 많은 메뉴 정보를 수집하세요.")

        return recommendations

    def _identify_review_items(self, menus: List[Menu], scores: List[KetoScore]) -> List[str]:
        """검수가 필요한 항목 식별"""
        review_items = []

        for menu, score in zip(menus, scores):
            # 낮은 신뢰도
            if score.confidence < 0.3:
                review_items.append(f"[낮은 신뢰도] {menu.name}")

            # 극단적 점수
            if abs(score.final_score) >= 80:
                review_items.append(f"[극단적 점수] {menu.name} ({score.final_score}점)")

            # 키워드 없음
            if not score.detected_keywords:
                review_items.append(f"[키워드 없음] {menu.name}")

            # 룰 적용 개수가 너무 많거나 적음
            if len(score.applied_rules) >= 5:
                review_items.append(f"[복잡한 룰 적용] {menu.name}")
            elif len(score.applied_rules) == 0:
                review_items.append(f"[룰 미적용] {menu.name}")

        return review_items[:20]  # 최대 20개

    async def generate_comparative_report(
        self,
        current_menus: List[Menu],
        previous_menus: List[Menu],
        restaurant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """비교 리포트 생성 (시간별 품질 변화)"""

        current_scores = await self.keto_scorer.batch_calculate_scores(current_menus)
        previous_scores = await self.keto_scorer.batch_calculate_scores(previous_menus)

        current_metrics = self._calculate_metrics(current_menus, current_scores)
        previous_metrics = self._calculate_metrics(previous_menus, previous_scores)

        return {
            'comparison_summary': {
                'current_quality': self._determine_overall_quality(current_metrics).value,
                'previous_quality': self._determine_overall_quality(previous_metrics).value,
                'quality_change': 'improved' if current_metrics.avg_confidence > previous_metrics.avg_confidence else 'declined'
            },
            'metrics_comparison': {
                'confidence_change': current_metrics.avg_confidence - previous_metrics.avg_confidence,
                'coverage_change': current_metrics.keyword_coverage - previous_metrics.keyword_coverage,
                'item_count_change': current_metrics.total_items - previous_metrics.total_items
            },
            'new_issues': [
                issue.description for issue in current_metrics.issues
                if not any(prev_issue.issue_type == issue.issue_type for prev_issue in previous_metrics.issues)
            ],
            'resolved_issues': [
                issue.description for issue in previous_metrics.issues
                if not any(curr_issue.issue_type == issue.issue_type for curr_issue in current_metrics.issues)
            ]
        }