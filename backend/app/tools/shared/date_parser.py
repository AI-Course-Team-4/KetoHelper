from datetime import datetime, timedelta
from typing import Optional, Dict, List, Literal
from dataclasses import dataclass
import re
from dateutil import parser
from dateutil.relativedelta import relativedelta
import os
import json
import logging
import google.generativeai as genai

# 로거 설정
logger = logging.getLogger(__name__)


@dataclass
class ParsedDateInfo:
    date: datetime
    description: str
    is_relative: bool
    confidence: float  # 0-1, 파싱 신뢰도
    method: Literal['rule-based', 'llm-assisted', 'fallback']
    duration_days: Optional[int] = None  # 기간 정보 (예: 3일치, 7일치)


class DateParser:
    def __init__(self):
        """
        DateParser 초기화
        날짜 파싱 로직만 담당하는 순수한 비즈니스 로직 클래스
        """
        self.today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        logger.info(f"DateParser 초기화 - 기준 날짜: {self.today.isoformat()}")
        
        # 환경 변수 이름 수정: GEMINI_API_KEY -> GOOGLE_API_KEY
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables - LLM 기능 비활성화")
            self.model = None
        else:
            try:
                genai.configure(api_key=api_key)
                # LLM_MODEL 환경 변수 사용
                model_name = os.getenv("LLM_MODEL", "gemini-1.5-flash")
                
                # Gemini 모델명 형식 맞추기
                if model_name.startswith("gemini-"):
                    # 이미 gemini- 접두사가 있는 경우
                    self.model = genai.GenerativeModel(model_name)
                else:
                    # gemini- 접두사가 없는 경우 추가
                    self.model = genai.GenerativeModel(f"gemini-{model_name}")
                
                logger.info(f"Gemini 모델 초기화 성공: {model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini model: {e}")
                self.model = None

    def parse_natural_date(self, input_text: str) -> Optional[ParsedDateInfo]:
        """
        하이브리드 자연어 날짜 파싱 (규칙 기반 + LLM 보조)
        순수한 날짜 파싱 로직만 담당
        """
        return self.parse_natural_date_with_context(input_text, [])
    
    def parse_natural_date_with_context(self, input_text: str, chat_history: List[str]) -> Optional[ParsedDateInfo]:
        """
        대화 맥락을 고려한 하이브리드 자연어 날짜 파싱
        """
        if not input_text or not input_text.strip():
            logger.debug("빈 입력으로 날짜 파싱 시도")
            return None
            
        normalized = input_text.strip().lower()
        logger.debug(f"자연어 날짜 파싱 시작: '{normalized}' (맥락: {len(chat_history)}개 메시지)")

        # 1단계: LLM 우선 파싱 (오타 및 복잡한 표현 처리, 대화 맥락 포함)
        if self.model:
            logger.debug("LLM 우선 파싱 시도 (대화 맥락 포함)")
            llm_result = self._parse_with_llm_with_context(normalized, chat_history)
            if llm_result:
                logger.debug(f"LLM 파싱 성공: {llm_result.description} (신뢰도: {llm_result.confidence})")
                return llm_result

        # 2단계: 규칙 기반 파싱 (명확한 키워드 처리)
        logger.debug("규칙 기반 파싱 시도")
        rule_based_result = self._parse_with_rules(normalized)
        if rule_based_result:
            # 대화 맥락에서 일수 정보 추출하여 적용
            context_duration = self._extract_duration_from_context(chat_history)
            if context_duration and not rule_based_result.duration_days:
                rule_based_result.duration_days = context_duration
                logger.debug(f"대화 맥락에서 일수 정보 적용: {context_duration}일")
            
            logger.debug(f"규칙 기반 파싱 성공: {rule_based_result.description} (신뢰도: {rule_based_result.confidence})")
            return rule_based_result

        # 3단계: 폴백 (기본값)
        logger.debug("폴백 파싱 시도")
        fallback_result = self._get_fallback_date(normalized)
        if fallback_result:
            # 대화 맥락에서 일수 정보 추출하여 적용
            context_duration = self._extract_duration_from_context(chat_history)
            if context_duration and not fallback_result.duration_days:
                fallback_result.duration_days = context_duration
                logger.debug(f"대화 맥락에서 일수 정보 적용: {context_duration}일")
            
            logger.debug(f"폴백 파싱 성공: {fallback_result.description} (신뢰도: {fallback_result.confidence})")
        else:
            logger.debug(f"모든 파싱 방법 실패: '{normalized}'")
        
        return fallback_result

    def _parse_with_rules(self, normalized: str) -> Optional[ParsedDateInfo]:
        """규칙 기반 날짜 파싱"""

        # 오늘 관련
        if self._contains_words(normalized, ['오늘', '오늘날', '지금', '현재']):
            # 일수 정보 추출
            duration_days = self._extract_duration_days(normalized)
            return ParsedDateInfo(
                date=self.today,
                description='오늘',
                is_relative=True,
                confidence=1.0,
                method='rule-based',
                duration_days=duration_days
            )

        # 내일 관련
        if self._contains_words(normalized, ['내일', '다음날', '명일', '낼']):
            duration_days = self._extract_duration_days(normalized)
            return ParsedDateInfo(
                date=self.today + timedelta(days=1),
                description='내일',
                is_relative=True,
                confidence=1.0,
                method='rule-based',
                duration_days=duration_days
            )

        # 모레
        if self._contains_words(normalized, ['모레', '글피', '모래']):
            # '모래'가 단독으로 있고 sand의 의미가 아닐 때
            if '모래' in normalized and not any(word in normalized for word in ['놀이', '바다', '해변']):
                return ParsedDateInfo(
                    date=self.today + timedelta(days=2),
                    description='모레',
                    is_relative=True,
                    confidence=0.9,
                    method='rule-based'
                )
            elif '모레' in normalized or '글피' in normalized:
                return ParsedDateInfo(
                    date=self.today + timedelta(days=2),
                    description='모레',
                    is_relative=True,
                    confidence=1.0,
                    method='rule-based'
                )

        # 하루 관련 (내일로 해석)
        if '하루' in normalized and any(word in normalized for word in ['만', '후', '뒤']):
            return ParsedDateInfo(
                date=self.today + timedelta(days=1),
                description='내일 (하루 후)',
                is_relative=True,
                confidence=0.8,
                method='rule-based'
            )

        # 다음주 관련 (오타 포함)
        if any(word in normalized for word in ['다음주', '담주', '다움주', '다음쥬', '다움쥬', '다윰주', '다음줘']):
            next_week_result = self._parse_next_week(normalized)
            if next_week_result:
                # 일수 정보 추가 (다음주는 기본 7일)
                duration_days = self._extract_duration_days(normalized) or 7
                next_week_result.duration_days = duration_days
            return next_week_result

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

    def _parse_with_llm(self, normalized: str) -> Optional[ParsedDateInfo]:
        """
        Gemini를 사용한 자연어 날짜 파싱
        LLM 관련 로직만 담당
        """
        if not self.model:
            logger.debug("LLM 모델이 없어서 LLM 파싱 건너뜀")
            return None
            
        try:
            logger.debug(f"LLM 파싱 시작: '{normalized}'")
            today_str = self.today.strftime("%Y-%m-%d")
            weekday_name = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'][self.today.weekday()]

            prompt = f"""당신은 한국어 날짜 표현을 파싱하는 전문가입니다. 오타 교정과 지능적 날짜 파싱이 주된 역할입니다.

현재 정보:
- 오늘 날짜: {today_str} ({weekday_name})

작업: 다음 텍스트에서 날짜를 정확히 파싱하세요. 오타나 변형된 표현도 지능적으로 교정하세요.
입력: "{normalized}"

핵심 규칙:
- 모든 한국어 날짜 관련 오타를 지능적으로 교정하여 파싱하세요
- 문맥을 고려하여 날짜 표현과 비날짜 용어를 구분하세요
- 조사 "가" 처리 규칙:
  * "다음주가 캘린더에 추가해줘" → "다음주에"로 해석 (캘린더/일정 관련 문맥)
  * "다음주가 오를까?" → 주식 관련 용어 (주가/투자 관련 문맥)
  * "다음주에", "다음주를", "다음주로" → 명확한 날짜 표현
- 주식/투자 관련 키워드("주가", "투자", "매수", "매도", "상승", "하락")가 함께 있으면 날짜로 파싱하지 마세요

오타 처리 규칙 (최우선):
- 한국어 날짜 표현의 의도를 파악하여 모든 오타를 지능적으로 교정하세요
- 자음/모음 변형, 타이핑 오류, 발음 기반 오타 모두 고려하세요
- 예시 오타들 (이것만이 전부가 아님):
  * "다음주": 다움주, 다윰주, 다움쥬, 다음쥬, 다음줘, 담주, 다ㅡㅁ주 등
  * "이번주": 이벊주, 이번쥬, 이번줘, 이벤주, 이번주 등
  * "내일": 낼, 네일, 내일날, 내일 등
  * "모레": 모래, 모례, 모레 등 (모래(sand)와 구분)
- "하루"는 문맥상 "내일" 또는 "1일 후"를 의미할 수 있음
- 기타 예상치 못한 모든 오타도 한국어 날짜 표현의 의도를 파악하여 교정하세요
- 오타 교정 시 원본 입력을 description에 표시하되, 파싱은 교정된 결과로 진행하세요

응답 규칙:
1. 반드시 JSON 형식으로만 응답하세요
2. 날짜 파싱이 가능하면 success: true, 불가능하면 success: false
3. 상대적 날짜 표현(오늘, 내일, 이번주 등)은 is_relative: true
4. 절대적 날짜 표현(12월 25일 등)은 is_relative: false
5. 날짜 표현이 없거나 애매한 경우 반드시 success: false

JSON 형식:
{{
    "success": true,
    "date": "2024-09-28",
    "description": "이번주 토요일",
    "is_relative": true,
    "confidence": 0.9,
    "duration_days": 7
}}

파싱 예시 (오타 교정 및 문맥 판단 포함):
- "이번주 토요일" → 이번주 토요일 실제 날짜 (duration_days: 1)
- "내일" → 오늘 + 1일 (duration_days: 1)
- "3일 후" → 오늘 + 3일 (duration_days: 3)
- "12월 25일" → 올해 12월 25일 (지났으면 내년) (duration_days: 1)
- "크리스마스" → 12월 25일 (duration_days: 1)
- "다움주" → 다음주로 해석 (duration_days: 7)
- "다윰주" → 다음주로 해석 (오타 교정) (duration_days: 7)
- "다움쥬" → 다음주로 해석 (오타 교정) (duration_days: 7)
- "이벊주" → 이번주로 해석 (오타 교정) (duration_days: 7)
- "이번쥬" → 이번주로 해석 (오타 교정) (duration_days: 7)
- "다음주가 캘린더에 추가해줘" → 다음주로 해석 (캘린더 문맥) (duration_days: 7)
- "다음주가 저장해줘" → 다음주로 해석 (저장 문맥) (duration_days: 7)
- "다음주가 일정에 넣어줘" → 다음주로 해석 (일정 문맥) (duration_days: 7)
- "3일치 저장해줘" → 오늘부터 3일 (duration_days: 3)
- "5일치 계획해줘" → 오늘부터 5일 (duration_days: 5)
- "7일치 식단표" → 오늘부터 7일 (duration_days: 7)
- "하루만" → 내일로 해석 (duration_days: 1)
- "낼" → 내일로 해석 (duration_days: 1)
- "모래" → 모레로 해석 (오타 교정, 모래(sand)와 구분) (duration_days: 1)

파싱하지 않는 예시 (주식/투자 관련):
- "다음주가 오를까?" → 파싱 안함 (주가 문맥)
- "다음주가 상승할 것 같아" → 파싱 안함 (투자 문맥)

파싱할 수 없는 경우: {{"success": false}}

응답:"""

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # JSON 파싱 시도
            try:
                # JSON만 추출 (혹시 추가 텍스트가 있을 경우 대비)
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_text = result_text[json_start:json_end]
                    result = json.loads(json_text)

                    if result.get("success"):
                        date_str = result.get("date")
                        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")

                        return ParsedDateInfo(
                            date=parsed_date,
                            description=result.get("description", normalized),
                            is_relative=result.get("is_relative", True),
                            confidence=min(result.get("confidence", 0.7), 0.9),
                            method='llm-assisted',
                            duration_days=result.get("duration_days")
                        )

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"LLM 응답 JSON 파싱 오류: {e}")
                pass

        except Exception as e:
            logger.error(f"LLM 파싱 중 오류: {e}")
            pass

        return None

    def _parse_with_llm_with_context(self, normalized: str, chat_history: List[str]) -> Optional[ParsedDateInfo]:
        """
        대화 맥락을 포함한 LLM 파싱
        """
        if not self.model:
            logger.debug("LLM 모델이 없어서 LLM 파싱 건너뜀")
            return None
            
        try:
            logger.debug(f"LLM 파싱 시작 (맥락 포함): '{normalized}'")
            today_str = self.today.strftime("%Y-%m-%d")
            weekday_name = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'][self.today.weekday()]

            # 대화 맥락 정보 추가
            context_info = ""
            if chat_history:
                context_info = f"\n\n대화 맥락 (최근 {min(len(chat_history), 3)}개 메시지):\n"
                for i, msg in enumerate(chat_history[-3:], 1):
                    context_info += f"{i}. {msg}\n"
                context_info += "\n중요: 위 대화 맥락에서 언급된 일수 정보(예: 3일치, 7일치)를 현재 날짜 파싱에 반영하세요."

            prompt = f"""당신은 한국어 날짜 표현을 파싱하는 전문가입니다. 오타 교정과 지능적 날짜 파싱이 주된 역할입니다.

현재 정보:
- 오늘 날짜: {today_str} ({weekday_name})

작업: 다음 텍스트에서 날짜를 정확히 파싱하세요. 오타나 변형된 표현도 지능적으로 교정하세요.
입력: "{normalized}"
{context_info}

핵심 규칙:
- 모든 한국어 날짜 관련 오타를 지능적으로 교정하여 파싱하세요
- 문맥을 고려하여 날짜 표현과 비날짜 용어를 구분하세요
- 조사 "가" 처리 규칙:
  * "다음주가 캘린더에 추가해줘" → "다음주에"로 해석 (캘린더/일정 관련 문맥)
  * "다음주가 오를까?" → 주식 관련 용어 (주가/투자 관련 문맥)
  * "다음주에", "다음주를", "다음주로" → 명확한 날짜 표현
- 주식/투자 관련 키워드("주가", "투자", "매수", "매도", "상승", "하락")가 함께 있으면 날짜로 파싱하지 마세요

오타 처리 규칙 (최우선):
- 한국어 날짜 표현의 의도를 파악하여 모든 오타를 지능적으로 교정하세요
- 자음/모음 변형, 타이핑 오류, 발음 기반 오타 모두 고려하세요
- 예시 오타들 (이것만이 전부가 아님):
  * "다음주": 다움주, 다윰주, 다움쥬, 다음쥬, 다음줘, 담주, 다ㅡㅁ주 등
  * "이번주": 이벊주, 이번쥬, 이번줘, 이벤주, 이번주 등
  * "내일": 낼, 네일, 내일날, 내일 등
  * "모레": 모래, 모례, 모레 등 (모래(sand)와 구분)
- "하루"는 문맥상 "내일" 또는 "1일 후"를 의미할 수 있음
- 기타 예상치 못한 모든 오타도 한국어 날짜 표현의 의도를 파악하여 교정하세요
- 오타 교정 시 원본 입력을 description에 표시하되, 파싱은 교정된 결과로 진행하세요

응답 규칙:
1. 반드시 JSON 형식으로만 응답하세요
2. 날짜 파싱이 가능하면 success: true, 불가능하면 success: false
3. 상대적 날짜 표현(오늘, 내일, 이번주 등)은 is_relative: true
4. 절대적 날짜 표현(12월 25일 등)은 is_relative: false
5. 날짜 표현이 없거나 애매한 경우 반드시 success: false
6. duration_days: 대화 맥락에서 추출한 일수 정보를 포함하세요

JSON 형식:
{{
    "success": true,
    "date": "2024-09-28",
    "description": "이번주 토요일",
    "is_relative": true,
    "confidence": 0.9,
    "duration_days": 7
}}

파싱 예시 (오타 교정 및 문맥 판단 포함):
- "이번주 토요일" → 이번주 토요일 실제 날짜 (duration_days: 1)
- "내일" → 오늘 + 1일 (duration_days: 1)
- "3일 후" → 오늘 + 3일 (duration_days: 3)
- "12월 25일" → 올해 12월 25일 (지났으면 내년) (duration_days: 1)
- "크리스마스" → 12월 25일 (duration_days: 1)
- "다움주" → 다음주로 해석 (duration_days: 7)
- "다윰주" → 다음주로 해석 (오타 교정) (duration_days: 7)
- "다움쥬" → 다음주로 해석 (오타 교정) (duration_days: 7)
- "이벊주" → 이번주로 해석 (오타 교정) (duration_days: 7)
- "이번쥬" → 이번주로 해석 (오타 교정) (duration_days: 7)
- "다음주가 캘린더에 추가해줘" → 다음주로 해석 (캘린더 문맥) (duration_days: 7)
- "다음주가 저장해줘" → 다음주로 해석 (저장 문맥) (duration_days: 7)
- "다음주가 일정에 넣어줘" → 다음주로 해석 (일정 문맥) (duration_days: 7)
- "3일치 저장해줘" → 오늘부터 3일 (duration_days: 3)
- "5일치 계획해줘" → 오늘부터 5일 (duration_days: 5)
- "7일치 식단표" → 오늘부터 7일 (duration_days: 7)
- "하루만" → 내일로 해석 (duration_days: 1)
- "낼" → 내일로 해석 (duration_days: 1)
- "모래" → 모레로 해석 (오타 교정, 모래(sand)와 구분) (duration_days: 1)

파싱하지 않는 예시 (주식/투자 관련):
- "다음주가 오를까?" → 파싱 안함 (주가 문맥)
- "다음주가 상승할 것 같아" → 파싱 안함 (투자 문맥)

파싱할 수 없는 경우: {{"success": false}}

응답:"""

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # JSON 파싱 시도
            try:
                # JSON만 추출 (혹시 추가 텍스트가 있을 경우 대비)
                json_start = result_text.find('{')
                json_end = result_text.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_text = result_text[json_start:json_end]
                    result = json.loads(json_text)

                    if result.get("success"):
                        date_str = result.get("date")
                        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")

                        return ParsedDateInfo(
                            date=parsed_date,
                            description=result.get("description", normalized),
                            is_relative=result.get("is_relative", True),
                            confidence=min(result.get("confidence", 0.7), 0.9),
                            method='llm-assisted',
                            duration_days=result.get("duration_days")
                        )

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"LLM 응답 JSON 파싱 오류: {e}")
                pass

        except Exception as e:
            logger.error(f"LLM 파싱 중 오류: {e}")
            pass

        return None

    def _get_fallback_date(self, normalized: str) -> Optional[ParsedDateInfo]:
        """폴백 날짜 처리 (기본값 또는 추론)"""
        
        # 오타 매핑 처리 (더 포괄적인 오타 교정)
        typo_mappings = {
            # 다음주 관련 오타들
            '다움주': '다음주',
            '다음쥬': '다음주', 
            '다움쥬': '다음주',  # 추가된 오타
            '담주': '다음주',
            '다윰주': '다음주',  # 추가된 오타
            '다음줘': '다음주',  # 추가된 오타
            # 이번주 관련 오타들
            '이벊주': '이번주',  # 추가된 오타
            '이번쥬': '이번주',  # 추가된 오타
            '이번줘': '이번주',  # 추가된 오타
            # 내일 관련 오타들
            '낼': '내일',
            '네일': '내일',
            # 모레 관련 오타들
            '모래': '모레',  # 문맥상 날짜로 보이는 경우
            '하루': '내일',  # "하루"를 내일로 해석
        }
        
        # 오타를 정정한 버전 생성
        corrected = normalized
        for typo, correct in typo_mappings.items():
            if typo in corrected:
                corrected = corrected.replace(typo, correct)
        
        # 기본적인 키워드 매칭으로 폴백 처리
        if '오늘' in corrected:
            return ParsedDateInfo(
                date=self.today,
                description='오늘',
                is_relative=True,
                confidence=0.8,
                method='fallback'
            )

        if '내일' in corrected:
            tomorrow = self.today + timedelta(days=1)
            return ParsedDateInfo(
                date=tomorrow,
                description='내일',
                is_relative=True,
                confidence=0.8,
                method='fallback'
            )

        if '모레' in corrected:
            day_after_tomorrow = self.today + timedelta(days=2)
            return ParsedDateInfo(
                date=day_after_tomorrow,
                description='모레',
                is_relative=True,
                confidence=0.8,
                method='fallback'
            )

        if '다음주' in corrected:
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
    
    def _extract_duration_days(self, text: str) -> Optional[int]:
        """텍스트에서 일수 정보를 추출 (예: 3일치, 2주치, 5주일치)"""
        import re
        
        # 1. "N주치" 또는 "N주일치" 패턴 찾기 (주 단위)
        week_patterns = [
            r'(\d+)주일치',  # "2주일치", "3주일치", "5주일치"
            r'(\d+)주치',    # "2주치", "3주치", "5주치"
            r'(\d+)주',      # "2주", "3주", "5주" (문맥상 기간으로 해석)
        ]
        
        for pattern in week_patterns:
            match = re.search(pattern, text)
            if match:
                weeks = int(match.group(1))
                return weeks * 7  # 주를 일로 변환
        
        # 2. "N일치" 패턴 찾기 (일 단위)
        duration_match = re.search(r'(\d+)일치', text)
        if duration_match:
            return int(duration_match.group(1))
        
        # 3. "N일" 패턴 찾기 (기간 표현)
        if '일' in text and any(word in text for word in ['식단', '계획', '추천', '만들']):
            days_match = re.search(r'(\d+)일', text)
            if days_match:
                return int(days_match.group(1))
        
        # 기본값: 일수 정보가 없으면 None
        return None
    
    def _extract_duration_from_context(self, chat_history: List[str]) -> Optional[int]:
        """대화 맥락에서 일수 정보를 추출 (동적 파싱)"""
        if not chat_history:
            return None
            
        # 최근 메시지들에서 일수 정보 찾기 (최대 5개 메시지)
        recent_messages = chat_history[-5:]
        
        for message in reversed(recent_messages):  # 최근 메시지부터 확인
            # 동적 파싱 함수 사용
            duration_days = self._extract_duration_days(message)
            if duration_days:
                logger.debug(f"대화 맥락에서 일수 정보 발견: {duration_days}일")
                return duration_days
        
        return None

    def _parse_next_week(self, text: str) -> Optional[ParsedDateInfo]:
        # 오타 포함 체크 (더 포괄적인 오타 인식)
        if not any(word in text for word in ['다음주', '담주', '다움주', '다음쥬', '다움쥬', '다윰주', '다음줘']):
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
        if any(word in text for word in ['이번주', '다음주', '담주', '다움주']):
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
        """
        채팅 메시지에서 날짜 관련 표현을 찾아 파싱
        순수한 날짜 추출 로직만 담당
        """
        return self.extract_date_from_message_with_context(message, [])
    
    def extract_date_from_message_with_context(self, message: str, chat_history: List[str]) -> Optional[ParsedDateInfo]:
        """
        대화 맥락을 고려하여 채팅 메시지에서 날짜 관련 표현을 찾아 파싱
        """
        if not message or not message.strip():
            logger.debug("빈 메시지로 날짜 추출 시도")
            return None
            
        logger.debug(f"메시지에서 날짜 추출 시작: '{message}'")
        logger.debug(f"대화 맥락: {len(chat_history)}개 메시지")
        
        # 식단 저장과 관련된 키워드와 함께 날짜 표현을 찾음
        save_keywords = ['저장', '추가', '계획', '등록', '넣어', '캘린더', '일정']
        has_save_keyword = any(keyword in message for keyword in save_keywords)

        if not has_save_keyword:
            logger.debug("저장/일정 관련 키워드가 없어서 날짜 추출 건너뜀")
            return None

        # 메시지에서 날짜 표현 추출 (띄어쓰기 및 오타 허용)
        date_patterns = [
            r'오늘', r'내일', r'낼', r'모레', r'모래', r'글피',
            r'다\s*음\s*주', r'다움주', r'다윰주', r'다음줘', r'담\s*주', r'이\s*번\s*주',  # 띄어쓰기 및 오타
            r'이벊주', r'이번줘',  # 이번주 오타들
            r'하루(?:만)?',  # "하루" 또는 "하루만"
            r'월요일', r'화요일', r'수요일', r'목요일', r'금요일', r'토요일', r'일요일',
            r'이\s*번\s*주\s*[월화수목금토일]요일',
            r'다\s*음\s*주\s*[월화수목금토일]요일',
            r'\d{1,2}월\s*\d{1,2}일',
            r'\d{1,2}일(?![일월화수목금토])',
            r'\d+일\s*[후뒤]'
        ]

        # 1단계: 정규표현식으로 날짜 패턴 찾기
        for pattern in date_patterns:
            match = re.search(pattern, message.lower())
            if match:
                logger.debug(f"정규표현식 패턴 매칭: '{pattern}' -> '{match.group(0)}'")
                result = self.parse_natural_date(match.group(0))
                if result:
                    return result

        # 2단계: 정규표현식 매칭 실패 시, 전체 메시지를 LLM에게 전달
        # (오타, 변형된 표현, 복잡한 표현 처리)
        logger.debug("정규표현식 매칭 실패, 전체 메시지로 파싱 시도")
        result = self.parse_natural_date_with_context(message, chat_history)
        
        # LLM이나 폴백이 날짜를 찾았는지 확인
        if result and result.confidence >= 0.3:  # 최소 신뢰도 체크
            logger.debug(f"전체 메시지 파싱 성공: {result.description} (신뢰도: {result.confidence})")
            return result

        logger.debug("메시지에서 날짜 추출 실패")
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