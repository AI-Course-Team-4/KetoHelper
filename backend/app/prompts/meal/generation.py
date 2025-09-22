"""
개별 식사 메뉴 생성 프롬프트
특정 시간대와 타입에 맞는 키토 메뉴 생성
"""

MEAL_GENERATION_PROMPT = """
        {slot}에 적합한 {meal_type} 키토 메뉴를 생성하세요.
        
        제약 조건: {constraints}
        
        다음 JSON 형태로 응답하세요:
        {{
            "type": "recipe",
            "title": "메뉴명",
            "macros": {{"kcal": 칼로리, "carb": 탄수화물g, "protein": 단백질g, "fat": 지방g}},
            "ingredients": [
                {{"name": "재료명", "amount": 양, "unit": "단위"}}
            ],
            "steps": ["조리 과정"],
            "tips": ["키토 팁"]
        }}
        """

# Meal Agent에서 분리된 기본 생성 프롬프트
DEFAULT_GENERATION_PROMPT = """
{slot}에 적합한 {meal_type} 키토 메뉴를 생성하세요.
제약 조건: {constraints}

다음 JSON 형태로 응답하세요:
{{
    "type": "recipe",
    "title": "메뉴명",
    "macros": {{"kcal": 칼로리, "carb": 탄수화물g, "protein": 단백질g, "fat": 지방g}},
    "ingredients": [{{"name": "재료명", "amount": 양, "unit": "단위"}}],
    "steps": ["조리 과정"],
    "tips": ["키토 팁"]
}}
"""

# 다른 접근법들
GENERATION_PROMPT = MEAL_GENERATION_PROMPT
PROMPT = MEAL_GENERATION_PROMPT
