from typing import List, Dict, Optional, Tuple, Set
import re
from dataclasses import dataclass

from core.interfaces.scorer_interface import KeywordMatch, MatchType
from services.scorer.keyword_matcher import KeywordMatcher


@dataclass
class SubstitutionContext:
    """대체/제외 컨텍스트 정보"""
    original_carb: str
    substitute: str
    negation_phrase: str
    confidence: float
    context_window: str


@dataclass
class NegationContext:
    """부정 표현 컨텍스트 정보"""
    negation_word: str
    target_carb: str
    full_phrase: str
    confidence: float
    position: int


class SubstitutionDetector:
    """대체재료 및 제외 표현 감지 시스템"""

    def __init__(self, keyword_matcher: KeywordMatcher):
        self.keyword_matcher = keyword_matcher

        # 탄수화물 키워드 목록
        self.carb_keywords = {
            '밥': ['쌀밥', '흰밥', '현미밥', '잡곡밥'],
            '면': ['국수', '라면', '우동', '파스타'],
            '빵': ['브레드', '식빵', '바게트', '토스트']
        }

        # 대체재료 키워드
        self.substitutes = {
            '곤약밥': ['곤약쌀', 'konjac rice'],
            '두부면': ['두부국수'],
            '콜리플라워라이스': ['콜리플라워 라이스', 'cauliflower rice'],
            '시라타키': ['곤약면', 'shirataki'],
            '호박면': ['주키니면', 'zucchini noodles'],
            '양배추': ['양배추쌀']
        }

        # 부정 표현 패턴
        self.negation_patterns = [
            r'(밥|쌀밥)\s*(을|를)?\s*(빼|제외|없이|빼고)',
            r'(면|국수|라면)\s*(을|를)?\s*(빼|제외|없이|빼고)',
            r'(빵|브레드)\s*(을|를)?\s*(빼|제외|없이|빼고)',
            r'(밥|면|빵)\s*없는',
            r'(밥|면|빵)\s*안\s*들어간'
        ]

        # 대체 표현 패턴
        self.replacement_patterns = [
            r'(밥|쌀밥)\s*대신\s*(곤약|두부|콜리플라워|양배추)',
            r'(면|국수)\s*대신\s*(곤약면|두부면|호박면|시라타키)',
            r'(밥|면)\s*말고\s*(곤약|두부)'
        ]

    def detect_substitutions(self, text: str) -> List[SubstitutionContext]:
        """대체재료 감지"""
        substitutions = []
        text_lower = text.lower()

        # 1. 직접적인 대체재료 언급
        for substitute, aliases in self.substitutes.items():
            all_terms = [substitute] + aliases

            for term in all_terms:
                if term in text_lower:
                    # 주변에서 원래 탄수화물 찾기
                    original_carb = self._find_original_carb_nearby(text_lower, term)

                    if original_carb:
                        substitutions.append(SubstitutionContext(
                            original_carb=original_carb,
                            substitute=term,
                            negation_phrase="",
                            confidence=0.9,
                            context_window=self._extract_context(text, term)
                        ))

        # 2. "대신" 패턴 매칭
        for pattern in self.replacement_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    substitutions.append(SubstitutionContext(
                        original_carb=groups[0],
                        substitute=groups[1],
                        negation_phrase=match.group(),
                        confidence=0.95,
                        context_window=self._extract_context(text, match.group())
                    ))

        return substitutions

    def detect_negations(self, text: str) -> List[NegationContext]:
        """부정/제외 표현 감지"""
        negations = []

        # 정규식 패턴으로 부정 표현 찾기
        for pattern in self.negation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 1:
                    carb_keyword = groups[0]
                    negation_phrase = match.group()

                    negations.append(NegationContext(
                        negation_word=self._extract_negation_word(negation_phrase),
                        target_carb=carb_keyword,
                        full_phrase=negation_phrase,
                        confidence=0.9,
                        position=match.start()
                    ))

        # 추가적인 컨텍스트 기반 부정 감지
        additional_negations = self._detect_contextual_negations(text)
        negations.extend(additional_negations)

        return negations

    def _find_original_carb_nearby(self, text: str, substitute: str) -> Optional[str]:
        """대체재료 주변에서 원래 탄수화물 찾기"""
        substitute_pos = text.find(substitute)
        if substitute_pos == -1:
            return None

        # 앞뒤 30글자 범위에서 탄수화물 키워드 찾기
        window = 30
        start = max(0, substitute_pos - window)
        end = min(len(text), substitute_pos + len(substitute) + window)
        context = text[start:end]

        for main_carb, aliases in self.carb_keywords.items():
            all_carbs = [main_carb] + aliases
            for carb in all_carbs:
                if carb in context:
                    return carb

        return None

    def _extract_negation_word(self, phrase: str) -> str:
        """부정 표현에서 핵심 부정어 추출"""
        negation_words = ['빼', '제외', '없이', '빼고', '없는', '안들어간']

        for word in negation_words:
            if word in phrase:
                return word

        return phrase

    def _detect_contextual_negations(self, text: str) -> List[NegationContext]:
        """컨텍스트 기반 부정 표현 감지"""
        negations = []

        # "선택 가능", "추가 가능" 같은 옵션 표현
        option_patterns = [
            r'(밥|면)\s*(선택|옵션)',
            r'(밥|면)\s*추가\s*가능',
            r'(밥|면)\s*별도\s*주문'
        ]

        for pattern in option_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 1:
                    negations.append(NegationContext(
                        negation_word="선택가능",
                        target_carb=groups[0],
                        full_phrase=match.group(),
                        confidence=0.7,  # 옵션 표현은 신뢰도 낮음
                        position=match.start()
                    ))

        return negations

    def _extract_context(self, text: str, keyword: str) -> str:
        """키워드 주변 컨텍스트 추출"""
        pos = text.lower().find(keyword.lower())
        if pos == -1:
            return ""

        start = max(0, pos - 15)
        end = min(len(text), pos + len(keyword) + 15)
        return text[start:end].strip()

    def calculate_carb_offset(self, text: str, original_matches: List[KeywordMatch]) -> float:
        """탄수화물 패널티 상쇄량 계산"""
        total_offset = 0.0

        # 대체재료 감지
        substitutions = self.detect_substitutions(text)
        for sub in substitutions:
            # 대체재료로 인한 상쇄 (완전 상쇄)
            carb_penalty = self._get_carb_penalty(sub.original_carb, original_matches)
            if carb_penalty < 0:  # 패널티가 있는 경우
                offset = abs(carb_penalty) * sub.confidence
                total_offset += offset

        # 부정 표현 감지
        negations = self.detect_negations(text)
        for neg in negations:
            # 부정 표현으로 인한 상쇄 (50% 상쇄)
            carb_penalty = self._get_carb_penalty(neg.target_carb, original_matches)
            if carb_penalty < 0:
                offset = abs(carb_penalty) * 0.5 * neg.confidence
                total_offset += offset

        return total_offset

    def _get_carb_penalty(self, carb_keyword: str, matches: List[KeywordMatch]) -> float:
        """특정 탄수화물 키워드의 패널티 점수 찾기"""
        for match in matches:
            if match.match_type == MatchType.HIGH_CARB and carb_keyword in match.keyword:
                return match.weight
        return 0.0

    def generate_substitution_suggestions(self, text: str) -> List[Dict[str, str]]:
        """대체재료 제안 생성"""
        suggestions = []
        text_lower = text.lower()

        # 탄수화물이 포함된 메뉴에 대한 대체 제안
        for main_carb, aliases in self.carb_keywords.items():
            all_carbs = [main_carb] + aliases

            for carb in all_carbs:
                if carb in text_lower:
                    if main_carb == '밥':
                        suggestions.extend([
                            {'original': carb, 'substitute': '곤약밥', 'benefit': '칼로리 90% 감소'},
                            {'original': carb, 'substitute': '콜리플라워라이스', 'benefit': '탄수화물 95% 감소'},
                            {'original': carb, 'substitute': '양배추', 'benefit': '식이섬유 풍부'}
                        ])
                    elif main_carb == '면':
                        suggestions.extend([
                            {'original': carb, 'substitute': '시라타키', 'benefit': '칼로리 거의 없음'},
                            {'original': carb, 'substitute': '두부면', 'benefit': '단백질 풍부'},
                            {'original': carb, 'substitute': '호박면', 'benefit': '비타민 풍부'}
                        ])
                    elif main_carb == '빵':
                        suggestions.extend([
                            {'original': carb, 'substitute': '생채소', 'benefit': '탄수화물 제거'},
                            {'original': carb, 'substitute': '양상추 랩', 'benefit': '식이섬유 증가'}
                        ])

        # 중복 제거
        unique_suggestions = []
        seen = set()
        for suggestion in suggestions:
            key = f"{suggestion['original']}-{suggestion['substitute']}"
            if key not in seen:
                seen.add(key)
                unique_suggestions.append(suggestion)

        return unique_suggestions[:5]  # 최대 5개 제안

    def analyze_text_structure(self, text: str) -> Dict[str, any]:
        """텍스트 구조 분석 (디버깅용)"""
        return {
            'total_length': len(text),
            'detected_substitutions': self.detect_substitutions(text),
            'detected_negations': self.detect_negations(text),
            'carb_keywords_found': [
                carb for carb_list in self.carb_keywords.values()
                for carb in carb_list if carb in text.lower()
            ],
            'substitute_keywords_found': [
                sub for sub in self.substitutes.keys()
                if sub in text.lower()
            ]
        }