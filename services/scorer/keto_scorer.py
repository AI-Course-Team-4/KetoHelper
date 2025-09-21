from typing import List, Optional, Dict, Any
from datetime import datetime

from core.interfaces.scorer_interface import IKetoScorer
from core.domain.menu import Menu
from core.domain.keto_score import KetoScore, ScoreCategory, ScoreReason
from services.scorer.keyword_matcher import KeywordMatcher
from services.scorer.menu_rule_engine import MenuRuleEngine
from config.settings import Settings


class KetoScorer(IKetoScorer):
    """키토 점수화 메인 서비스"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.keyword_matcher = KeywordMatcher(settings)
        self.rule_engine = MenuRuleEngine(self.keyword_matcher, settings)

    async def calculate_score(self, menu: Menu) -> KetoScore:
        """메뉴의 키토 점수 계산"""
        try:
            # 룰 엔진을 통해 점수 계산
            keto_score = self.rule_engine.apply_rules(menu)

            # 계산 시간 기록
            keto_score.calculated_at = datetime.utcnow()

            # 추가 검증 및 조정
            keto_score = self._post_process_score(keto_score, menu)

            return keto_score

        except Exception as e:
            # 에러 발생시 기본 점수 반환
            return KetoScore(
                menu_id=menu.id,
                raw_score=0.0,
                final_score=0.0,
                confidence=0.1,
                category=ScoreCategory.KETO_AVOID,
                reasons=[ScoreReason(
                    rule_id="error_handling",
                    keyword="error",
                    impact=0.0,
                    explanation=f"점수 계산 오류: {str(e)}"
                )],
                detected_keywords=[],
                applied_rules=["error_handling"],
                calculated_at=datetime.utcnow()
            )

    async def batch_calculate_scores(self, menus: List[Menu]) -> List[KetoScore]:
        """여러 메뉴의 점수를 일괄 계산"""
        scores = []

        for menu in menus:
            score = await self.calculate_score(menu)
            scores.append(score)

        return scores

    def _post_process_score(self, score: KetoScore, menu: Menu) -> KetoScore:
        """점수 후처리 및 추가 검증"""

        # 1. 극단적인 점수 조정
        if score.final_score < -100:
            score.final_score = -100
            score.reasons.append(ScoreReason(
                rule_id="post_process",
                keyword="extreme_negative",
                impact=0.0,
                explanation="극단적 저점 방지로 -100으로 제한"
            ))

        if score.final_score > 100:
            score.final_score = 100
            score.reasons.append(ScoreReason(
                rule_id="post_process",
                keyword="extreme_positive",
                impact=0.0,
                explanation="극단적 고점 방지로 100으로 제한"
            ))

        # 2. 가격 기반 조정 (고가 메뉴는 품질이 좋을 가능성)
        if menu.price and menu.price > 30000:  # 3만원 이상
            if score.final_score > 0:
                bonus = min(5, menu.price / 10000)  # 최대 5점 보너스
                score.final_score += bonus
                score.reasons.append(ScoreReason(
                    rule_id="post_process",
                    keyword="premium_price",
                    impact=bonus,
                    explanation=f"고가 메뉴 품질 보정 (+{bonus:.1f})"
                ))

        # 3. 메뉴명 길이 기반 신뢰도 조정
        if len(menu.name) < 3:
            score.confidence *= 0.8
            score.reasons.append(ScoreReason(
                rule_id="post_process",
                keyword="short_name",
                impact=0.0,
                explanation="짧은 메뉴명으로 신뢰도 하향 조정"
            ))

        # 4. 카테고리 재검증
        score.category = self._determine_final_category(score.final_score, score.confidence)

        return score

    def _determine_final_category(self, score: float, confidence: float) -> ScoreCategory:
        """최종 카테고리 결정 (신뢰도 고려)"""

        # 신뢰도가 너무 낮으면 보수적으로 분류
        if confidence < 0.3:
            return ScoreCategory.KETO_MODERATE

        # 신뢰도를 반영한 점수 조정
        adjusted_score = score * confidence

        if adjusted_score >= 40:
            return ScoreCategory.KETO_RECOMMENDED
        elif adjusted_score >= 15:
            return ScoreCategory.KETO_MODERATE
        elif adjusted_score >= -15:
            return ScoreCategory.KETO_CAUTION
        else:
            return ScoreCategory.KETO_AVOID

    async def get_score_explanation(self, menu: Menu) -> Dict[str, Any]:
        """점수에 대한 상세 설명 생성"""
        score = await self.calculate_score(menu)

        # 룰별 상세 결과
        rule_results = self.rule_engine.get_rule_results(menu)

        # 키워드별 분석
        keyword_analysis = {}
        for keyword in score.detected_keywords:
            keyword_info = self.keyword_matcher.get_keyword_info(keyword)
            if keyword_info:
                keyword_analysis[keyword] = {
                    'weight': keyword_info.weight,
                    'confidence': keyword_info.confidence,
                    'description': keyword_info.description
                }

        return {
            'menu_info': {
                'name': menu.name,
                'description': menu.description,
                'price': menu.price
            },
            'score_summary': {
                'final_score': score.final_score,
                'raw_score': score.raw_score,
                'confidence': score.confidence,
                'category': score.category.value
            },
            'detected_keywords': keyword_analysis,
            'applied_rules': score.applied_rules,
            'rule_details': [
                {
                    'rule_id': r.rule_id,
                    'applied': r.applied,
                    'score_impact': r.score_impact,
                    'matched_keywords': r.matched_keywords,
                    'explanation': r.explanation
                }
                for r in rule_results
            ],
            'score_reasons': [
                {
                    'rule_id': r.rule_id,
                    'keyword': r.keyword,
                    'impact': r.impact,
                    'explanation': r.explanation
                }
                for r in score.reasons
            ],
            'recommendations': self._generate_recommendations(score, menu)
        }

    def _generate_recommendations(self, score: KetoScore, menu: Menu) -> List[str]:
        """점수 기반 추천사항 생성"""
        recommendations = []

        if score.category == ScoreCategory.KETO_AVOID:
            recommendations.extend([
                "이 메뉴는 키토 다이어트에 적합하지 않습니다",
                "탄수화물이 많이 포함되어 있을 가능성이 높습니다",
                "대신 고기, 생선, 채소 위주의 메뉴를 선택하세요"
            ])

        elif score.category == ScoreCategory.KETO_CAUTION:
            recommendations.extend([
                "키토 다이어트 중이라면 피하는 것이 좋습니다",
                "밥이나 면을 제외하고 주문할 수 있는지 확인해보세요"
            ])

        elif score.category == ScoreCategory.KETO_MODERATE:
            recommendations.extend([
                "조심스럽게 선택할 수 있는 메뉴입니다",
                "탄수화물 함량을 확인하고 주문하세요",
                "가능하다면 밥이나 면을 빼고 주문하세요"
            ])

        elif score.category == ScoreCategory.KETO_MODERATE:
            recommendations.extend([
                "키토 다이어트에 적합한 메뉴입니다",
                "안심하고 드실 수 있습니다"
            ])

        elif score.category == ScoreCategory.KETO_RECOMMENDED:
            recommendations.extend([
                "키토 다이어트에 매우 좋은 메뉴입니다",
                "이런 메뉴를 더 많이 선택하세요"
            ])

        # 신뢰도 기반 추가 코멘트
        if score.confidence < 0.5:
            recommendations.append("※ 메뉴 정보가 부족하여 정확도가 낮을 수 있습니다")

        return recommendations

    async def analyze_restaurant_keto_friendliness(self, restaurant_id: str, menus: List[Menu]) -> Dict[str, Any]:
        """레스토랑 전체의 키토 친화도 분석"""
        if not menus:
            return {'error': '분석할 메뉴가 없습니다'}

        # 모든 메뉴 점수 계산
        scores = await self.batch_calculate_scores(menus)

        # 통계 계산
        total_menus = len(scores)
        avg_score = sum(s.final_score for s in scores) / total_menus
        avg_confidence = sum(s.confidence for s in scores) / total_menus

        # 카테고리별 분포
        category_distribution = {}
        for category in ScoreCategory:
            count = len([s for s in scores if s.category == category])
            category_distribution[category.value] = {
                'count': count,
                'percentage': round(count / total_menus * 100, 1)
            }

        # 키토 친화도 등급 결정
        keto_friendly_percentage = (
            category_distribution[ScoreCategory.KETO_RECOMMENDED.value]['percentage'] +
            category_distribution[ScoreCategory.KETO_MODERATE.value]['percentage']
        )

        if keto_friendly_percentage >= 50:
            friendliness_grade = 'A'
        elif keto_friendly_percentage >= 30:
            friendliness_grade = 'B'
        elif keto_friendly_percentage >= 15:
            friendliness_grade = 'C'
        else:
            friendliness_grade = 'D'

        return {
            'restaurant_id': restaurant_id,
            'analysis_summary': {
                'total_menus': total_menus,
                'average_score': round(avg_score, 1),
                'average_confidence': round(avg_confidence, 2),
                'keto_friendly_percentage': round(keto_friendly_percentage, 1),
                'friendliness_grade': friendliness_grade
            },
            'category_distribution': category_distribution,
            'top_recommended_menus': [
                {
                    'name': menu.name,
                    'score': score.final_score,
                    'category': score.category.value
                }
                for menu, score in sorted(
                    zip(menus, scores),
                    key=lambda x: x[1].final_score,
                    reverse=True
                )[:5]
            ],
            'menus_to_avoid': [
                {
                    'name': menu.name,
                    'score': score.final_score,
                    'category': score.category.value
                }
                for menu, score in sorted(
                    zip(menus, scores),
                    key=lambda x: x[1].final_score
                )[:3]
            ]
        }