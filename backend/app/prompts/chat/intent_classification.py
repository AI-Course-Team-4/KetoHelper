"""
의도 분류 프롬프트
사용자 메시지를 분석하여 의도와 슬롯을 추출
"""

INTENT_CLASSIFICATION_PROMPT = """
사용자 메시지를 분석하여 의도와 슬롯을 추출하세요.

사용자 메시지: "{message}"

다음 JSON 형태로 응답하세요:
{{
    "intent": "recipe|place|mealplan|memory|other",
    "slots": {{
        "location": "지역명 (예: 역삼역, 강남)",
        "radius": "검색 반경 (km)",
        "category": "음식 카테고리",
        "preferences": "선호사항",
        "allergies": "알레르기",
        "meal_type": "식사 타입 (아침/점심/저녁)",
        "days": "식단표 일수"
    }}
}}

의도 분류:
- recipe: 레시피 추천 요청 (만들어 먹을 음식, 조리법)
- place: 식당/장소 검색 요청 (외식, 배달, 근처 식당)
- mealplan: 식단표 생성 요청 (주간/일간 식단)
- memory: 프로필/선호도 업데이트
- other: 일반 대화/기타
"""
