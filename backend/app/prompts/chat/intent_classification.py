"""
의도 분류 프롬프트
사용자 메시지를 분석하여 의도와 슬롯을 추출
하이브리드 방식 지원: 키워드 분석 힌트 활용 가능
"""

INTENT_CLASSIFICATION_PROMPT = """
사용자 메시지를 분석하여 의도와 슬롯을 추출하세요.

사용자 메시지: "{message}"

{keyword_hint_section}

다음 JSON 형태로 응답하세요:
{{
    "intent": "meal_planning|restaurant_search|calendar_save|general",
    "slots": {{
        "location": "지역명 (예: 역삼역, 강남)",
        "radius": "검색 반경 (km)",
        "category": "음식 카테고리",
        "preferences": "선호사항",
        "allergies": "알레르기",
        "meal_type": "식사 타입 (아침/점심/저녁)",
        "days": "식단표 일수 (하루치/1일=1, 일주일=7, 3일=3 등)"
    }}
}}

의도 분류 기준 (중요!):
- meal_planning: 식단 계획, 레시피, 요리법 관련 모든 요청 (기존 recipe + mealplan 통합)
  예: "불고기 레시피", "계란말이 만드는 법", "7일 식단표 만들어줘", "이번 주 메뉴 계획", "키토 식단 만들어줘"
  
- restaurant_search: 식당을 "찾아달라", "추천해줘", "근처에 어디 있어?" 요청 (기존 place)
  예: "강남역 근처 식당", "키토 식당 찾아줘", "배달 가능한 곳"
  
- calendar_save: 이미 만든 식단을 캘린더에 저장하는 요청
  예: "캘린더에 저장해줘", "일정으로 등록", "캘린더에 추가해줘"
  
중요: days 슬롯에는 다음과 같이 숫자로 입력하세요:
- "하루치", "1일", "하루", "오늘" → days: 1
- "이틀", "2일" → days: 2  
- "3일", "사흘" → days: 3
- "일주일", "7일", "한 주", "이번주", "다음주" → days: 7
  
- general: 일반 대화, 인사, 기억 요청, 도움말 등 (기존 memory + other 통합)
  예: "안녕하세요", "고마워", "브로콜리 싫어해", "알레르기 있어", "키토 식단이 뭐야?", "도움말"
  
주의사항:
- "식단"이라는 단어가 있어도 구체적인 계획 요청이 아니면 general로 분류
- 질문형 문장은 대부분 general로 분류
- 의문사(뭐, 왜, 어떻게, 언제, 어디서)가 있으면 general 우선 고려
"""

# 키워드 힌트가 있을 때 사용하는 향상된 프롬프트
ENHANCED_INTENT_CLASSIFICATION_PROMPT = """
사용자 메시지를 분석하여 의도와 슬롯을 추출하세요.

사용자 메시지: "{message}"

🔍 키워드 분석 결과: {keyword_intent} (확신도: {confidence:.2f})
💡 참고사항: 위 키워드 분석 결과를 참고하되, 맥락을 고려하여 더 정확한 분석을 해주세요.

다음 JSON 형태로 응답하세요:
{{
    "intent": "meal_planning|restaurant_search|calendar_save|general",
    "slots": {{
        "location": "지역명 (예: 역삼역, 강남)",
        "radius": "검색 반경 (km)",
        "category": "음식 카테고리",
        "preferences": "선호사항",
        "allergies": "알레르기",
        "meal_type": "식사 타입 (아침/점심/저녁)",
        "days": "식단표 일수 (하루치/1일=1, 일주일=7, 3일=3 등)"
    }}
}}

의도 분류 기준 (중요!):
- meal_planning: 식단 계획, 레시피, 요리법 관련 모든 요청 (기존 recipe + mealplan 통합)
  예: "불고기 레시피", "계란말이 만드는 법", "7일 식단표 만들어줘", "이번 주 메뉴 계획", "키토 식단 만들어줘"
  
- restaurant_search: 식당을 "찾아달라", "추천해줘", "근처에 어디 있어?" 요청 (기존 place)
  예: "강남역 근처 식당", "키토 식당 찾아줘", "배달 가능한 곳"
  
- calendar_save: 이미 만든 식단을 캘린더에 저장하는 요청
  예: "캘린더에 저장해줘", "일정으로 등록", "캘린더에 추가해줘"
  
중요: days 슬롯에는 다음과 같이 숫자로 입력하세요:
- "하루치", "1일", "하루", "오늘" → days: 1
- "이틀", "2일" → days: 2  
- "3일", "사흘" → days: 3
- "일주일", "7일", "한 주", "이번주", "다음주" → days: 7
  
- general: 일반 대화, 인사, 기억 요청, 도움말 등 (기존 memory + other 통합)
  예: "안녕하세요", "고마워", "브로콜리 싫어해", "알레르기 있어", "키토 식단이 뭐야?", "도움말"

🎯 키워드 분석 활용 가이드:
- 키워드 분석이 높은 확신도(0.8+)를 보인다면 해당 결과를 우선 고려하세요
- 키워드 분석이 낮은 확신도를 보인다면 맥락과 문장 구조를 더 중요하게 고려하세요
- 질문형 패턴이 강하다면 키워드와 관계없이 'general' 고려하세요
- 구체적인 행동 요청(만들어줘, 찾아줘, 생성해줘)이 있다면 해당 의도로 분류하세요

주의사항:
- "식단"이라는 단어가 있어도 구체적인 계획 요청이 아니면 general로 분류
- 질문형 문장은 대부분 general로 분류
- 의문사(뭐, 왜, 어떻게, 언제, 어디서)가 있으면 general 우선 고려
"""

def create_keyword_hint_section(keyword_intent: str = None, confidence: float = None) -> str:
    """키워드 힌트 섹션 생성"""
    if keyword_intent and confidence is not None:
        return f"""
🔍 키워드 분석 결과: {keyword_intent} (확신도: {confidence:.2f})
💡 참고사항: 위 키워드 분석 결과를 참고하되, 맥락을 고려하여 더 정확한 분석을 해주세요.
        """.strip()
    else:
        return ""

def get_intent_prompt(message: str, keyword_intent: str = None, confidence: float = None) -> str:
    """
    적절한 의도 분류 프롬프트 반환
    
    Args:
        message: 사용자 메시지
        keyword_intent: 키워드 분석 결과 (선택사항)
        confidence: 키워드 분석 확신도 (선택사항)
    
    Returns:
        완성된 프롬프트 문자열
    """
    if keyword_intent and confidence is not None:
        # 키워드 힌트가 있을 때 향상된 프롬프트 사용
        return ENHANCED_INTENT_CLASSIFICATION_PROMPT.format(
            message=message,
            keyword_intent=keyword_intent,
            confidence=confidence
        )
    else:
        # 기본 프롬프트 사용
        keyword_hint_section = create_keyword_hint_section()
        return INTENT_CLASSIFICATION_PROMPT.format(
            message=message,
            keyword_hint_section=keyword_hint_section
        )
