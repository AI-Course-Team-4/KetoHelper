"""
의도 분류 프롬프트
사용자 메시지를 분석하여 의도를 분류
"""

INTENT_CLASSIFICATION_PROMPT = """
사용자 메시지를 분석하여 의도를 분류하세요.

사용자 메시지: "{message}"

다음 JSON 형태로 응답하세요:
{{
    "intent": "meal_plan",
    "confidence": 0.9,
    "reasoning": "분류 이유"
}}

**중요한 분류 규칙:**

1. **식단표/식단 계획 = meal_plan** (최우선)
   - "식단표", "식단", "일주일", "7일", "메뉴 계획" 키워드가 있으면 무조건 meal_plan
   - "7일 키토 식단표 만들어줘" → meal_plan
   - "일주일 식단 만들어줘" → meal_plan
   - "3일 식단표" → meal_plan

2. **개별 레시피 = recipe_search**
   - "레시피", "조리법", "만드는 법" 키워드만 있을 때
   - "불고기 레시피" → recipe_search
   - "계란말이 만드는 법" → recipe_search

3. **식당 검색 = place_search**
   - "식당", "맛집", "근처" 키워드
   - "강남역 근처 식당" → place_search

4. **캘린더 저장 = calendar_save**
   - "캘린더", "저장", "넣어줘" 키워드
   - "캘린더에 저장" → calendar_save

5. **일반 대화 = general**
   - 위 키워드들이 없을 때
   - "키토 다이어트가 뭐야?" → general

"""

def get_intent_prompt(message: str) -> str:
    """의도 분류 프롬프트 생성"""
    return INTENT_CLASSIFICATION_PROMPT.format(message=message)