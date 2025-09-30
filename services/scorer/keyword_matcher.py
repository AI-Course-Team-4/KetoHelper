from typing import Dict, List, Tuple, Optional, Set
import re
import json
from pathlib import Path
from dataclasses import dataclass

from core.interfaces.scorer_interface import IKeywordMatcher, KeywordMatch, MatchType
from config.settings import Settings


@dataclass
class KeywordConfig:
    weight: float
    confidence: float
    aliases: List[str]
    description: str = ""
    carb_base: Optional[str] = None
    replaces: Optional[List[str]] = None
    patterns: Optional[List[str]] = None
    context_required: bool = False


class KeywordMatcher(IKeywordMatcher):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.keywords = {}
        self.patterns = {}
        self._load_keyword_data()

    def _load_keyword_data(self):
        """키워드 사전 데이터 로드"""
        keyword_dir = Path(self.settings.data_dir) / "config" / "keywords"

        # 각 키워드 파일 로드
        keyword_files = {
            'high_carb': keyword_dir / "high_carb.json",
            'keto_friendly': keyword_dir / "keto_friendly.json",
            'substitutions': keyword_dir / "substitutions.json",
            'negations': keyword_dir / "negations.json",
            'menu_types': keyword_dir / "menu_types.json"
        }

        for category, file_path in keyword_files.items():
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._process_keyword_file(category, data)

        # 한국어 경계 기반 핵심 패턴 추가 (부분일치 오검출 완화)
        self._add_korean_boundary_patterns()

    def _process_keyword_file(self, category: str, data: Dict):
        """키워드 파일 데이터를 내부 구조로 변환"""
        if category == 'high_carb':
            self._process_simple_keywords(data['keywords'], MatchType.HIGH_CARB)

        elif category == 'keto_friendly':
            self._process_simple_keywords(data['keywords'], MatchType.KETO_FRIENDLY)
            # cooking_methods도 키토 친화적으로 처리
            if 'cooking_methods' in data:
                self._process_simple_keywords(data['cooking_methods'], MatchType.KETO_FRIENDLY)

        elif category == 'substitutions':
            self._process_substitutions(data)

        elif category == 'negations':
            self._process_negations(data)

        elif category == 'menu_types':
            self._process_menu_types(data)

    def _process_simple_keywords(self, keywords: Dict, match_type: MatchType):
        """단순 키워드 처리 (고탄수화물, 키토 친화적)"""
        for keyword, config in keywords.items():
            keyword_config = KeywordConfig(
                weight=config['weight'],
                confidence=config['confidence'],
                aliases=config.get('aliases', []),
                description=config.get('description', ''),
                carb_base=config.get('carb_base')
            )

            # 메인 키워드 등록
            self.keywords[keyword] = (match_type, keyword_config)

            # 별명들도 등록
            for alias in keyword_config.aliases:
                self.keywords[alias] = (match_type, keyword_config)

    def _process_substitutions(self, data: Dict):
        """대체재료 키워드 처리"""
        # 완전 대체재료
        for keyword, config in data['complete_substitutions'].items():
            keyword_config = KeywordConfig(
                weight=config['weight'],
                confidence=config['confidence'],
                aliases=config.get('aliases', []),
                replaces=config.get('replaces', []),
                carb_base=config.get('carb_base'),
                description=config.get('description', '')
            )

            self.keywords[keyword] = (MatchType.SUBSTITUTION, keyword_config)
            for alias in keyword_config.aliases:
                self.keywords[alias] = (MatchType.SUBSTITUTION, keyword_config)

        # 키토 재료들
        for keyword, config in data['keto_ingredients'].items():
            keyword_config = KeywordConfig(
                weight=config['weight'],
                confidence=config['confidence'],
                aliases=config.get('aliases', [])
            )

            self.keywords[keyword] = (MatchType.KETO_FRIENDLY, keyword_config)
            for alias in keyword_config.aliases:
                self.keywords[alias] = (MatchType.KETO_FRIENDLY, keyword_config)

        # 패턴들 저장
        if 'patterns' in data:
            self.patterns.update(data['patterns'])

    def _process_negations(self, data: Dict):
        """부정/제외 표현 처리"""
        # 제외 패턴들
        for category, config in data['exclusion_patterns'].items():
            for pattern in config['patterns']:
                if 'negation_patterns' not in self.patterns:
                    self.patterns['negation_patterns'] = []
                self.patterns['negation_patterns'].append({
                    'pattern': pattern,
                    'weight': config['weight'],
                    'confidence': config['confidence'],
                    'description': config['description']
                })

        # 대체 패턴들
        for category, config in data['replacement_patterns'].items():
            for pattern in config['patterns']:
                if 'replacement_patterns' not in self.patterns:
                    self.patterns['replacement_patterns'] = []
                self.patterns['replacement_patterns'].append({
                    'pattern': pattern,
                    'weight': config['weight'],
                    'confidence': config['confidence'],
                    'description': config['description']
                })

        # 단순 부정어들
        for word, config in data['negation_words'].items():
            keyword_config = KeywordConfig(
                weight=config['weight'],
                confidence=config['confidence'],
                aliases=[],
                context_required=config.get('context_required', False)
            )

            self.keywords[word] = (MatchType.NEGATION, keyword_config)

    def _process_menu_types(self, data: Dict):
        """메뉴 타입 키워드 처리"""
        for category, items in data.items():
            if category in ['low_score_types', 'combo_indicators', 'portion_indicators', 'korean_traditional']:
                for keyword, config in items.items():
                    keyword_config = KeywordConfig(
                        weight=config['weight'],
                        confidence=config['confidence'],
                        aliases=config.get('aliases', []),
                        description=config.get('description', '')
                    )

                    self.keywords[keyword] = (MatchType.MENU_TYPE, keyword_config)
                    for alias in keyword_config.aliases:
                        self.keywords[alias] = (MatchType.MENU_TYPE, keyword_config)

        # 패턴들 저장
        if 'patterns' in data:
            for pattern_type, patterns in data['patterns'].items():
                pattern_key = f"menu_{pattern_type}"
                self.patterns[pattern_key] = patterns

    def find_matches(self, text: str) -> List[KeywordMatch]:
        """텍스트에서 키워드 매치 찾기"""
        matches = []
        text_lower = text.lower()

        # 1. 직접 키워드 매칭
        for keyword, (match_type, config) in self.keywords.items():
            if keyword in text_lower:
                # 컨텍스트가 필요한 키워드는 주변 확인
                if config.context_required and match_type == MatchType.NEGATION:
                    if self._has_carb_context(text_lower, keyword):
                        matches.append(KeywordMatch(
                            keyword=keyword,
                            match_type=match_type,
                            weight=config.weight,
                            confidence=config.confidence,
                            position=text_lower.find(keyword),
                            context=self._extract_context(text, keyword)
                        ))
                else:
                    matches.append(KeywordMatch(
                        keyword=keyword,
                        match_type=match_type,
                        weight=config.weight,
                        confidence=config.confidence,
                        position=text_lower.find(keyword),
                        context=self._extract_context(text, keyword)
                    ))

        # 2. 패턴 매칭
        pattern_matches = self._find_pattern_matches(text)
        matches.extend(pattern_matches)

        # 3. 중복 제거 및 정렬
        matches = self._deduplicate_matches(matches)
        matches.sort(key=lambda x: x.position)

        return matches

    def _has_carb_context(self, text: str, negation_word: str) -> bool:
        """부정어 주변에 탄수화물 키워드가 있는지 확인"""
        carb_keywords = ['밥', '면', '국수', '라면', '빵', '파스타']

        neg_pos = text.find(negation_word)
        if neg_pos == -1:
            return False

        # 앞뒤 5단어 범위에서 탄수화물 키워드 찾기
        start = max(0, neg_pos - 20)
        end = min(len(text), neg_pos + len(negation_word) + 20)
        context = text[start:end]

        return any(carb in context for carb in carb_keywords)

    def _extract_context(self, text: str, keyword: str) -> str:
        """키워드 주변 컨텍스트 추출"""
        pos = text.lower().find(keyword)
        if pos == -1:
            return ""

        start = max(0, pos - 10)
        end = min(len(text), pos + len(keyword) + 10)
        return text[start:end].strip()

    def _find_pattern_matches(self, text: str) -> List[KeywordMatch]:
        """정규식 패턴 매칭"""
        matches = []

        # 부정 패턴들
        if 'negation_patterns' in self.patterns:
            for pattern_config in self.patterns['negation_patterns']:
                pattern = pattern_config['pattern']
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    matches.append(KeywordMatch(
                        keyword=match.group(),
                        match_type=MatchType.NEGATION,
                        weight=pattern_config['weight'],
                        confidence=pattern_config['confidence'],
                        position=match.start(),
                        context=self._extract_context(text, match.group())
                    ))

        # 대체 패턴들
        if 'replacement_patterns' in self.patterns:
            for pattern_config in self.patterns['replacement_patterns']:
                pattern = pattern_config['pattern']
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    matches.append(KeywordMatch(
                        keyword=match.group(),
                        match_type=MatchType.SUBSTITUTION,
                        weight=pattern_config['weight'],
                        confidence=pattern_config['confidence'],
                        position=match.start(),
                        context=self._extract_context(text, match.group())
                    ))

        # 한국어 경계 기반 고탄수 핵심 패턴들 (부분일치 방지용)
        if 'boundary_high_carb' in self.patterns:
            for pattern in self.patterns['boundary_high_carb']:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    matches.append(KeywordMatch(
                        keyword=match.group(),
                        match_type=MatchType.HIGH_CARB,
                        weight=-12,  # 기본 패널티 (사전 키워드보다 과도하지 않게 설정)
                        confidence=0.85,
                        position=match.start(),
                        context=self._extract_context(text, match.group())
                    ))

        # 메뉴 타입 패턴들
        for pattern_key, patterns in self.patterns.items():
            if pattern_key.startswith('menu_'):
                for pattern in patterns:
                    for match in re.finditer(pattern, text, re.IGNORECASE):
                        matches.append(KeywordMatch(
                            keyword=match.group(),
                            match_type=MatchType.MENU_TYPE,
                            weight=-6,  # 완화된 기본 메뉴 타입 패널티
                            confidence=0.7,
                            position=match.start(),
                            context=self._extract_context(text, match.group())
                        ))

        return matches

    def _add_korean_boundary_patterns(self):
        """부분일치 오검출을 줄이기 위한 한국어 경계 패턴 최소 추가"""
        # 핵심 고탄수 키워드에 대해 기본 경계 패턴을 동적으로 추가
        boundary_patterns = [
            r"(?<![가-힣a-zA-Z])(밥|볶음밥)(?![가-힣a-zA-Z])",
            r"(?<![가-힣a-zA-Z])(국수|라면|우동)(?![가-힣a-zA-Z])",
            r"(?<![가-힣a-zA-Z])(빵|파스타)(?![가-힣a-zA-Z])"
        ]

        if 'boundary_high_carb' not in self.patterns:
            self.patterns['boundary_high_carb'] = []

        for p in boundary_patterns:
            if p not in self.patterns['boundary_high_carb']:
                self.patterns['boundary_high_carb'].append(p)

    def _deduplicate_matches(self, matches: List[KeywordMatch]) -> List[KeywordMatch]:
        """중복 매치 제거 (위치 기반)"""
        seen_positions = set()
        unique_matches = []

        for match in matches:
            # 같은 위치에서 여러 매치가 있으면 가장 긴 것만 유지
            overlap_found = False
            for seen_pos in seen_positions:
                if abs(match.position - seen_pos) < 3:  # 3글자 이내 중복
                    overlap_found = True
                    break

            if not overlap_found:
                seen_positions.add(match.position)
                unique_matches.append(match)

        return unique_matches

    def get_keyword_info(self, keyword: str) -> Optional[KeywordConfig]:
        """특정 키워드 정보 반환"""
        if keyword in self.keywords:
            return self.keywords[keyword][1]
        return None

    def get_all_keywords(self, match_type: Optional[MatchType] = None) -> Dict[str, KeywordConfig]:
        """모든 키워드 또는 특정 타입 키워드 반환"""
        if match_type is None:
            return {k: v[1] for k, v in self.keywords.items()}

        return {k: v[1] for k, v in self.keywords.items() if v[0] == match_type}