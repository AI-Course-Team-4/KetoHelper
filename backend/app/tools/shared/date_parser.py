from datetime import datetime, timedelta
from typing import Optional, Dict, List, Literal
from dataclasses import dataclass
import re
from dateutil import parser
from dateutil.relativedelta import relativedelta


@dataclass
class ParsedDateInfo:
    date: datetime
    description: str
    is_relative: bool
    confidence: float  # 0-1, 파싱 신뢰도
    method: Literal['rule-based', 'llm-assisted', 'fallback']


class DateParser:
    def __init__(self):
        self.today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def parse_natural_date(self, input_text: str) -> Optional[ParsedDateInfo]:
        """
        하이브리드 자연어 날짜 파싱 (규칙 기반 + LLM 보조)
        """
        normalized = input_text.strip().lower()

        # 1단계: 규칙 기반 파싱 (높은 신뢰도)
        rule_based_result = self._parse_with_rules(normalized)
        if rule_based_result:
            return rule_based_result

        # 2단계: 복잡한 경우 LLM 보조 (향후 구현)
        # llm_assisted_result = await self._parse_with_llm(normalized)
        # if llm_assisted_result:
        #     return llm_assisted_result

        # 3단계: 폴백 (기본값)
        return self._get_fallback_date(normalized)

    def _parse_with_rules(self, normalized: str) -> Optional[ParsedDateInfo]:
        """규칙 기반 날짜 파싱"""

        # 오늘 관련
        if self._contains_words(normalized, ['오늘', '오늘날', '지금', '현재']):
            return ParsedDateInfo(
                date=self.today,
                description='오늘',
                is_relative=True,
                confidence=1.0,
                method='rule-based'
            )

        # 내일 관련
        if self._contains_words(normalized, ['내일', '다음날', '명일']):
            return ParsedDateInfo(
                date=self.today + timedelta(days=1),
                description='내일',
                is_relative=True,
                confidence=1.0,
                method='rule-based'
            )

        # 모레
        if self._contains_words(normalized, ['모레', '글피']):
            return ParsedDateInfo(
                date=self.today + timedelta(days=2),
                description='모레',
                is_relative=True,
                confidence=1.0,
                method='rule-based'
            )

        # 다음주 관련
        next_week_match = self._parse_next_week(normalized)
        if next_week_match:
            next_week_match.confidence = 0.9
            next_week_match.method = 'rule-based'
            return next_week_match

        # 이번주 관련
        this_week_match = self._parse_this_week(normalized)
        if this_week_match:
            this_week_match.confidence = 0.9
            this_week_match.method = 'rule-based'
            return this_week_match

        # 단독 요일 처리 (이번주로 해석)
        standalone_day_match = self._parse_standalone_day(normalized)
        if standalone_day_match:
            standalone_day_match.confidence = 0.8
            standalone_day_match.method = 'rule-based'
            return standalone_day_match

        # 특정 날짜 (예: "12월 25일", "25일")
        specific_date_match = self._parse_specific_date(normalized)
        if specific_date_match:
            specific_date_match.confidence = 0.8
            specific_date_match.method = 'rule-based'
            return specific_date_match

        # N일 후
        days_later_match = self._parse_days_later(normalized)
        if days_later_match:
            days_later_match.confidence = 0.8
            days_later_match.method = 'rule-based'
            return days_later_match

        return None

    def _get_fallback_date(self, normalized: str) -> Optional[ParsedDateInfo]:
        """폴백 날짜 처리 (기본값 또는 추론)"""
        # 기본적인 키워드 매칭으로 폴백 처리
        if '오늘' in normalized:
            return ParsedDateInfo(
                date=self.today,
                description='오늘',
                is_relative=True,
                confidence=0.8,
                method='fallback'
            )

        if '내일' in normalized:
            tomorrow = self.today + timedelta(days=1)
            return ParsedDateInfo(
                date=tomorrow,
                description='내일',
                is_relative=True,
                confidence=0.8,
                method='fallback'
            )

        if '모레' in normalized:
            day_after_tomorrow = self.today + timedelta(days=2)
            return ParsedDateInfo(
                date=day_after_tomorrow,
                description='모레',
                is_relative=True,
                confidence=0.8,
                method='fallback'
            )

        if '다음주' in normalized or '담주' in normalized:
            next_week = self.today + timedelta(days=7)
            return ParsedDateInfo(
                date=next_week,
                description='다음주',
                is_relative=True,
                confidence=0.6,
                method='fallback'
            )

        # 식단 관련 키워드가 있으면 오늘 날짜로 기본 설정
        if any(keyword in normalized for keyword in ['식단', '저장', '추가']):
            return ParsedDateInfo(
                date=self.today,
                description='오늘 (추론)',
                is_relative=True,
                confidence=0.3,
                method='fallback'
            )

        return None

    def _contains_words(self, text: str, words: List[str]) -> bool:
        return any(word in text for word in words)

    def _parse_next_week(self, text: str) -> Optional[ParsedDateInfo]:
        if not ('다음주' in text or '담주' in text):
            return None

        day_map = {
            '월요일': 1, '월': 1,
            '화요일': 2, '화': 2,
            '수요일': 3, '수': 3,
            '목요일': 4, '목': 4,
            '금요일': 5, '금': 5,
            '토요일': 6, '토': 6,
            '일요일': 0, '일': 0
        }

        # 다음주의 시작 (월요일) 구하기
        current_day = self.today.weekday()  # 0=월요일, 6=일요일
        days_to_next_monday = 7 - current_day
        next_monday = self.today + timedelta(days=days_to_next_monday)

        # 특정 요일이 언급되었는지 확인
        for day_name, day_number in day_map.items():
            if day_name in text:
                # day_number를 weekday() 형식으로 변환 (일요일=0 -> 6)
                target_weekday = day_number if day_number != 0 else 6
                if day_number == 0:  # 일요일
                    target_date = next_monday + timedelta(days=6)
                else:  # 월-토
                    target_date = next_monday + timedelta(days=day_number - 1)

                return ParsedDateInfo(
                    date=target_date,
                    description=f"다음주 {self._get_day_name(day_number)}",
                    is_relative=True,
                    confidence=0.9,
                    method='rule-based'
                )

        # 요일이 명시되지 않았으면 다음주 월요일
        return ParsedDateInfo(
            date=next_monday,
            description='다음주 월요일',
            is_relative=True,
            confidence=0.9,
            method='rule-based'
        )

    def _parse_this_week(self, text: str) -> Optional[ParsedDateInfo]:
        if '이번주' not in text:
            return None

        day_map = {
            '월요일': 1, '월': 1,
            '화요일': 2, '화': 2,
            '수요일': 3, '수': 3,
            '목요일': 4, '목': 4,
            '금요일': 5, '금': 5,
            '토요일': 6, '토': 6,
            '일요일': 0, '일': 0
        }

        # 이번주의 시작 (월요일) 구하기
        current_day = self.today.weekday()  # 0=월요일
        this_monday = self.today - timedelta(days=current_day)

        # 특정 요일이 언급되었는지 확인
        for day_name, day_number in day_map.items():
            if day_name in text:
                if day_number == 0:  # 일요일
                    target_date = this_monday + timedelta(days=6)
                else:  # 월-토
                    target_date = this_monday + timedelta(days=day_number - 1)

                return ParsedDateInfo(
                    date=target_date,
                    description=f"이번주 {self._get_day_name(day_number)}",
                    is_relative=True,
                    confidence=0.9,
                    method='rule-based'
                )

        return None

    def _parse_standalone_day(self, text: str) -> Optional[ParsedDateInfo]:
        # "이번주", "다음주" 등이 함께 언급된 경우는 제외
        if any(word in text for word in ['이번주', '다음주', '담주']):
            return None

        day_map = {
            '월요일': 1,
            '화요일': 2,
            '수요일': 3,
            '목요일': 4,
            '금요일': 5,
            '토요일': 6,
            '일요일': 0
        }

        # 특정 요일이 단독으로 언급되었는지 확인
        for day_name, day_number in day_map.items():
            if day_name in text:
                current_day = self.today.weekday()
                this_monday = self.today - timedelta(days=current_day)

                if day_number == 0:  # 일요일
                    target_date = this_monday + timedelta(days=6)
                else:  # 월-토
                    target_date = this_monday + timedelta(days=day_number - 1)

                # 해당 요일이 이미 지났으면 다음주로 설정
                if target_date < self.today:
                    target_date = target_date + timedelta(days=7)

                return ParsedDateInfo(
                    date=target_date,
                    description=self._get_day_name(day_number),
                    is_relative=True,
                    confidence=0.8,
                    method='rule-based'
                )

        return None

    def _parse_specific_date(self, text: str) -> Optional[ParsedDateInfo]:
        current_year = self.today.year

        # "12월 25일" 형태
        month_day_match = re.search(r'(\d{1,2})월\s*(\d{1,2})일', text)
        if month_day_match:
            month = int(month_day_match.group(1))
            day = int(month_day_match.group(2))

            try:
                date = datetime(current_year, month, day)

                # 과거 날짜라면 내년으로 설정
                if date < self.today:
                    date = datetime(current_year + 1, month, day)

                return ParsedDateInfo(
                    date=date,
                    description=f"{month}월 {day}일",
                    is_relative=False,
                    confidence=0.8,
                    method='rule-based'
                )
            except ValueError:
                pass

        # "25일" 형태 (이번 달)
        day_only_match = re.search(r'(\d{1,2})일', text)
        if day_only_match:
            day = int(day_only_match.group(1))
            current_month = self.today.month

            try:
                date = datetime(current_year, current_month, day)

                # 과거 날짜라면 다음 달로 설정
                if date < self.today:
                    date = date + relativedelta(months=1)

                return ParsedDateInfo(
                    date=date,
                    description=f"{day}일",
                    is_relative=False,
                    confidence=0.8,
                    method='rule-based'
                )
            except ValueError:
                pass

        return None

    def _parse_days_later(self, text: str) -> Optional[ParsedDateInfo]:
        # "3일 후", "5일뒤" 등
        days_later_match = re.search(r'(\d+)일\s*[후뒤]', text)
        if days_later_match:
            days = int(days_later_match.group(1))
            target_date = self.today + timedelta(days=days)

            return ParsedDateInfo(
                date=target_date,
                description=f"{days}일 후",
                is_relative=True,
                confidence=0.8,
                method='rule-based'
            )

        return None

    def _get_day_name(self, day_number: int) -> str:
        days = ['일요일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일']
        return days[day_number] if 0 <= day_number <= 6 else '월요일'

    def extract_date_from_message(self, message: str) -> Optional[ParsedDateInfo]:
        """채팅 메시지에서 날짜 관련 표현을 찾아 파싱"""
        # 식단 저장과 관련된 키워드와 함께 날짜 표현을 찾음
        save_keywords = ['저장', '추가', '계획', '등록', '넣어']
        has_save_keyword = any(keyword in message for keyword in save_keywords)

        if not has_save_keyword:
            return None

        # 메시지에서 날짜 표현 추출
        date_patterns = [
            r'오늘', r'내일', r'모레', r'글피',
            r'다음주', r'담주', r'이번주',
            r'월요일', r'화요일', r'수요일', r'목요일', r'금요일', r'토요일', r'일요일',
            r'이번주\s*[월화수목금토일]요일',
            r'다음주\s*[월화수목금토일]요일',
            r'\d{1,2}월\s*\d{1,2}일',
            r'\d{1,2}일(?![일월화수목금토])',
            r'\d+일\s*[후뒤]'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, message)
            if match:
                return self.parse_natural_date(match.group(0))

        return None

    def to_iso_string(self, parsed_date: ParsedDateInfo) -> str:
        """파싱된 날짜를 ISO 형식으로 변환"""
        return parsed_date.date.strftime('%Y-%m-%d')

    def to_display_string(self, parsed_date: ParsedDateInfo) -> str:
        """파싱된 날짜를 사용자 친화적 형식으로 변환"""
        if parsed_date.is_relative:
            return parsed_date.description

        return parsed_date.date.strftime('%m월 %d일 (%a)')


# 싱글톤 인스턴스 생성
date_parser = DateParser()

# 유틸리티 함수들
def parse_date(input_text: str) -> Optional[ParsedDateInfo]:
    return date_parser.parse_natural_date(input_text)

def extract_date_from_message(message: str) -> Optional[ParsedDateInfo]:
    return date_parser.extract_date_from_message(message)

def format_date_for_display(parsed_date: ParsedDateInfo) -> str:
    return date_parser.to_display_string(parsed_date)

def format_date_for_api(parsed_date: ParsedDateInfo) -> str:
    return date_parser.to_iso_string(parsed_date)