from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from core.interfaces.scorer_interface import IRuleEngine, KeywordMatch, MatchType, ScoringRule, RuleResult
from services.scorer.keyword_matcher import KeywordMatcher
from core.domain.menu import Menu
from core.domain.keto_score import KetoScore, ScoreReason, ScoreCategory
from config.settings import Settings


class RuleType(Enum):
    BASE_SCORING = "base_scoring"
    NEGATION_DETECTION = "negation_detection"
    SUBSTITUTION_BONUS = "substitution_bonus"
    MENU_TYPE_PENALTY = "menu_type_penalty"
    CONTEXT_ADJUSTMENT = "context_adjustment"


@dataclass
class RuleContext:
    """룰 실행 컨텍스트"""
    menu: Menu
    matches: List[KeywordMatch]
    text: str
    current_score: float = 0.0
    applied_rules: List[str] = field(default_factory=list)
    reasons: List[ScoreReason] = field(default_factory=list)


class MenuRuleEngine(IRuleEngine):
    def __init__(self, keyword_matcher: KeywordMatcher, settings: Settings):
        self.keyword_matcher = keyword_matcher
        self.settings = settings
        self.rules = self._initialize_rules()

    def _initialize_rules(self) -> Dict[RuleType, ScoringRule]:
        """스코어링 룰들 초기화"""
        return {
            RuleType.BASE_SCORING: ScoringRule(
                rule_id="base_scoring",
                description="기본 키워드 가중치 적용",
                weight_multiplier=1.0,
                confidence_threshold=0.5,
                enabled=True
            ),
            RuleType.NEGATION_DETECTION: ScoringRule(
                rule_id="negation_detection",
                description="부정/제외 표현 감지 및 패널티 상쇄",
                weight_multiplier=0.5,  # 패널티 50% 상쇄
                confidence_threshold=0.7,
                enabled=True
            ),
            RuleType.SUBSTITUTION_BONUS: ScoringRule(
                rule_id="substitution_bonus",
                description="대체재료 사용시 보너스 점수",
                weight_multiplier=1.2,
                confidence_threshold=0.8,
                enabled=True
            ),
            RuleType.MENU_TYPE_PENALTY: ScoringRule(
                rule_id="menu_type_penalty",
                description="메뉴 타입별 패널티 적용",
                weight_multiplier=1.0,
                confidence_threshold=0.6,
                enabled=True
            ),
            RuleType.CONTEXT_ADJUSTMENT: ScoringRule(
                rule_id="context_adjustment",
                description="컨텍스트 기반 점수 조정",
                weight_multiplier=0.8,
                confidence_threshold=0.6,
                enabled=True
            )
        }

    def apply_rules(self, menu: Menu) -> KetoScore:
        """메뉴에 모든 룰 적용하여 키토 점수 계산"""
        # 텍스트에서 키워드 매치 찾기
        text = f"{menu.name} {menu.description or ''}"
        matches = self.keyword_matcher.find_matches(text)

        # 룰 컨텍스트 초기화
        context = RuleContext(
            menu=menu,
            matches=matches,
            text=text
        )

        # 각 룰 순차적으로 적용
        self._apply_base_scoring(context)
        self._apply_negation_detection(context)
        self._apply_substitution_bonus(context)
        self._apply_menu_type_penalty(context)
        self._apply_context_adjustment(context)

        # 최종 점수 계산
        final_score = max(-100, min(100, context.current_score))
        confidence = self._calculate_overall_confidence(context)

        # 카테고리 결정은 최종 단계(KetoScorer)에서 수행
        return KetoScore(
            menu_id=menu.id,
            raw_score=context.current_score,
            final_score=final_score,
            confidence=confidence,
            category=ScoreCategory.KETO_AVOID,
            reasons=context.reasons,
            detected_keywords=[match.keyword for match in matches],
            applied_rules=context.applied_rules
        )

    def _apply_base_scoring(self, context: RuleContext):
        """기본 키워드 가중치 적용"""
        rule = self.rules[RuleType.BASE_SCORING]
        if not rule.enabled:
            return

        for match in context.matches:
            if match.confidence >= rule.confidence_threshold:
                adjusted_weight = match.weight * rule.weight_multiplier

                # 고탄수화물 키워드는 큰 패널티
                if match.match_type == MatchType.HIGH_CARB:
                    context.current_score += adjusted_weight
                    context.reasons.append(ScoreReason(
                        rule_id=rule.rule_id,
                        keyword=match.keyword,
                        impact=adjusted_weight,
                        explanation=f"고탄수화물 식품 감지: {match.keyword}"
                    ))

                # 키토 친화적 키워드는 보너스
                elif match.match_type == MatchType.KETO_FRIENDLY:
                    context.current_score += adjusted_weight
                    context.reasons.append(ScoreReason(
                        rule_id=rule.rule_id,
                        keyword=match.keyword,
                        impact=adjusted_weight,
                        explanation=f"키토 친화적 식품 감지: {match.keyword}"
                    ))

        context.applied_rules.append(rule.rule_id)

    def _apply_negation_detection(self, context: RuleContext):
        """부정/제외 표현 감지 및 패널티 상쇄"""
        rule = self.rules[RuleType.NEGATION_DETECTION]
        if not rule.enabled:
            return

        negation_matches = [m for m in context.matches if m.match_type == MatchType.NEGATION]

        for neg_match in negation_matches:
            if neg_match.confidence >= rule.confidence_threshold:
                # 부정어 주변의 고탄수화물 키워드 패널티 상쇄
                carb_matches = self._find_nearby_carb_matches(context, neg_match)

                for carb_match in carb_matches:
                    # 거리 기반 가변 상쇄 (<=5: 100%, <=15: 70%, <=30: 50%)
                    distance = abs(carb_match.position - neg_match.position)
                    if distance <= 5:
                        factor = 1.0
                    elif distance <= 15:
                        factor = 0.7
                    else:
                        factor = 0.5

                    offset = abs(carb_match.weight) * factor
                    context.current_score += offset

                    context.reasons.append(ScoreReason(
                        rule_id=rule.rule_id,
                        keyword=f"{neg_match.keyword}+{carb_match.keyword}",
                        impact=offset,
                        explanation=f"'{carb_match.keyword}' 제외 표현으로 패널티 상쇄"
                    ))

        context.applied_rules.append(rule.rule_id)

    def _apply_substitution_bonus(self, context: RuleContext):
        """대체재료 사용시 보너스 점수"""
        rule = self.rules[RuleType.SUBSTITUTION_BONUS]
        if not rule.enabled:
            return

        substitution_matches = [m for m in context.matches if m.match_type == MatchType.SUBSTITUTION]

        for sub_match in substitution_matches:
            if sub_match.confidence >= rule.confidence_threshold:
                # 대체재료 보너스 적용
                bonus = sub_match.weight * rule.weight_multiplier
                context.current_score += bonus

                context.reasons.append(ScoreReason(
                    rule_id=rule.rule_id,
                    keyword=sub_match.keyword,
                    impact=bonus,
                    explanation=f"건강한 대체재료 사용: {sub_match.keyword}"
                ))

        context.applied_rules.append(rule.rule_id)

    def _apply_menu_type_penalty(self, context: RuleContext):
        """메뉴 타입별 패널티 적용"""
        rule = self.rules[RuleType.MENU_TYPE_PENALTY]
        if not rule.enabled:
            return

        menu_type_matches = [m for m in context.matches if m.match_type == MatchType.MENU_TYPE]

        for type_match in menu_type_matches:
            if type_match.confidence >= rule.confidence_threshold:
                penalty = type_match.weight * rule.weight_multiplier
                context.current_score += penalty

                context.reasons.append(ScoreReason(
                    rule_id=rule.rule_id,
                    keyword=type_match.keyword,
                    impact=penalty,
                    explanation=f"메뉴 타입 패널티: {type_match.keyword}"
                ))

        context.applied_rules.append(rule.rule_id)

    def _apply_context_adjustment(self, context: RuleContext):
        """컨텍스트 기반 점수 조정"""
        rule = self.rules[RuleType.CONTEXT_ADJUSTMENT]
        if not rule.enabled:
            return

        # 복합적인 컨텍스트 분석
        adjustments = []

        # 1. 여러 고탄수화물 키워드가 함께 나타나면 추가 패널티
        high_carb_count = len([m for m in context.matches if m.match_type == MatchType.HIGH_CARB])
        if high_carb_count >= 2:
            penalty = -10 * (high_carb_count - 1)
            adjustments.append(("multiple_carbs", penalty, f"다중 탄수화물 식품 ({high_carb_count}개)"))

        # 2. 키토 키워드가 많으면 보너스
        keto_count = len([m for m in context.matches if m.match_type == MatchType.KETO_FRIENDLY])
        if keto_count >= 3:
            bonus = 5 * (keto_count - 2)
            adjustments.append(("multiple_keto", bonus, f"다양한 키토 식품 ({keto_count}개)"))

        # 3. 설명이 길고 상세하면 신뢰도 보정
        if len(context.text) > 50:
            description_bonus = 2
            adjustments.append(("detailed_description", description_bonus, "상세한 설명"))

        # 4. 강한 키토 키워드 보너스 (샐러드/키토/저탄고지)
        strong_keto_keywords = {"샐러드", "키토", "저탄고지", "케토", "salad", "keto"}
        strong_hits = [
            m for m in context.matches
            if m.match_type == MatchType.KETO_FRIENDLY and any(sk in m.keyword.lower() for sk in strong_keto_keywords)
        ]
        if strong_hits:
            # '키토/케토/keto'가 직접 포함된 경우는 더 강하게 가산
            has_explicit_keto = any(
                ("키토" in m.keyword) or ("케토" in m.keyword) or ("keto" in m.keyword.lower())
                for m in strong_hits
            )

            # 포케 기반 강한키워드 트리거는 과도한 중복가산을 유발하므로 축소 처리
            strong_hit_keywords = [m.keyword.lower() for m in strong_hits]
            is_poke_based = any(("포케" in kw) or ("poke" in kw) for kw in strong_hit_keywords)

            if has_explicit_keto:
                default_bonus = 40 if high_carb_count == 0 else 25
            else:
                default_bonus = 30 if high_carb_count == 0 else 18

            # 포케일 때는 강한 보너스를 크게 줄여 중복 보너스 누적을 방지
            strong_bonus = min(default_bonus, (10 if high_carb_count == 0 else 6)) if is_poke_based else default_bonus
            adjustments.append(("strong_keto_keyword", strong_bonus, "강한 키토 키워드 감지"))

        # 5. 포케 조건부 보너스 (밥/라이스 등 존재 시 보너스 감쇄)
        text_lower = context.text.lower()
        has_poke = ("포케" in text_lower) or any("포케" in m.keyword for m in context.matches)
        if has_poke:
            carb_terms = ["밥", "라이스", "rice", "현미", "쌀", "잡곡"]
            has_rice = any(term in text_lower for term in carb_terms)
            poke_bonus = 40 if not has_rice else 25
            if poke_bonus != 0:
                adjustments.append(("poke_conditional", poke_bonus, "포케: 밥 여부에 따른 보너스"))

        # 조정사항 적용
        for adj_type, impact, explanation in adjustments:
            context.current_score += impact
            context.reasons.append(ScoreReason(
                rule_id=rule.rule_id,
                keyword=adj_type,
                impact=impact,
                explanation=explanation
            ))

        context.applied_rules.append(rule.rule_id)

    def _find_nearby_carb_matches(self, context: RuleContext, negation_match: KeywordMatch) -> List[KeywordMatch]:
        """부정어 주변의 탄수화물 키워드 찾기"""
        nearby_matches = []
        window = 30  # 30글자 범위

        for match in context.matches:
            if match.match_type == MatchType.HIGH_CARB:
                distance = abs(match.position - negation_match.position)
                if distance <= window:
                    nearby_matches.append(match)

        return nearby_matches

    def _calculate_overall_confidence(self, context: RuleContext) -> float:
        """전체 신뢰도 계산"""
        if not context.matches:
            return 0.1  # 키워드가 없으면 낮은 신뢰도

        # 각 매치의 신뢰도 가중평균
        total_weight = sum(abs(match.weight) for match in context.matches)
        if total_weight == 0:
            return 0.5

        weighted_confidence = sum(
            match.confidence * abs(match.weight) for match in context.matches
        ) / total_weight

        # 매치 개수에 따른 보정
        match_count_factor = min(1.0, len(context.matches) / 3)

        # 최종 신뢰도
        return min(0.95, weighted_confidence * 0.7 + match_count_factor * 0.3)

    def _determine_category(self, score: float) -> ScoreCategory:
        """점수를 기반으로 카테고리 결정"""
        if score >= 80:
            return ScoreCategory.KETO_RECOMMENDED
        elif score >= 50:
            return ScoreCategory.KETO_MODERATE
        elif score >= 20:
            return ScoreCategory.KETO_CAUTION
        else:
            return ScoreCategory.KETO_AVOID

    def get_rule(self, rule_type: RuleType) -> Optional[ScoringRule]:
        """특정 룰 정보 반환"""
        return self.rules.get(rule_type)

    def update_rule(self, rule_type: RuleType, rule: ScoringRule):
        """룰 업데이트"""
        self.rules[rule_type] = rule

    def get_rule_results(self, menu: Menu) -> List[RuleResult]:
        """각 룰별 결과 상세 분석"""
        results = []

        # 임시로 각 룰을 개별 적용하여 영향도 측정
        base_context = RuleContext(
            menu=menu,
            matches=self.keyword_matcher.find_matches(f"{menu.name} {menu.description or ''}"),
            text=f"{menu.name} {menu.description or ''}"
        )

        for rule_type, rule in self.rules.items():
            if rule.enabled:
                test_context = RuleContext(
                    menu=base_context.menu,
                    matches=base_context.matches.copy(),
                    text=base_context.text,
                    current_score=0.0
                )

                # 개별 룰 적용
                if rule_type == RuleType.BASE_SCORING:
                    self._apply_base_scoring(test_context)
                elif rule_type == RuleType.NEGATION_DETECTION:
                    self._apply_negation_detection(test_context)
                elif rule_type == RuleType.SUBSTITUTION_BONUS:
                    self._apply_substitution_bonus(test_context)
                elif rule_type == RuleType.MENU_TYPE_PENALTY:
                    self._apply_menu_type_penalty(test_context)
                elif rule_type == RuleType.CONTEXT_ADJUSTMENT:
                    self._apply_context_adjustment(test_context)

                results.append(RuleResult(
                    rule_id=rule.rule_id,
                    applied=len(test_context.applied_rules) > 0,
                    score_impact=test_context.current_score,
                    confidence_impact=rule.confidence_threshold,
                    matched_keywords=[r.keyword for r in test_context.reasons],
                    explanation=rule.description
                ))

        return results