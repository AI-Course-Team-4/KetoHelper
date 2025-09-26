"""
식단표 구조 계획 프롬프트
일정 기간의 키토 식단 구조를 계획
"""

MEAL_PLAN_STRUCTURE_PROMPT = """
        {days}일간의 키토 식단표를 생성하세요.
        
        제약 조건: {constraints}
        
        각 날짜별로 아침/점심/저녁/간식의 구체적인 메뉴명을 정하세요.
        
        키토 원칙:
        - 아침: 간단하고 지방 위주 (계란, 아보카도, 치즈 등)
        - 점심: 단백질 + 채소 (샐러드, 구이, 볶음 등)  
        - 저녁: 풍성한 단백질 + 발효 채소 (고기, 생선 + 김치, 나물 등)
        - 간식: 초콜렛
        
        다양성을 고려하여 반복되지 않도록 하세요.
        
        간단하고 명확한 메뉴명만 제공하세요. 예시나 설명은 포함하지 마세요.
        
        JSON 형태로 응답하세요:
        [
            {{
                "day": 1,
                "breakfast": "스크램블 에그와 아보카도",
                "lunch": "닭가슴살 시저 샐러드",
                "dinner": "삼겹살 구이와 쌈 채소",
                "snack": "다크 초콜렛"
            }},
            ...
        ]
        """

# Meal Agent에서 분리된 기본 구조 프롬프트
DEFAULT_STRUCTURE_PROMPT = """
{days}일 키토 식단표를 생성하세요.
제약 조건: {constraints}

간단하고 명확한 메뉴명만 제공하세요. 예시나 설명은 포함하지 마세요.

다음 JSON 형태로 응답하세요:
[
    {{
        "day": 1,
        "breakfast": "구체적인 아침 메뉴명",
        "lunch": "구체적인 점심 메뉴명", 
        "dinner": "구체적인 저녁 메뉴명",
        "snack": "구체적인 간식명"
    }}
]
"""

# 다른 접근법들
STRUCTURE_PROMPT = MEAL_PLAN_STRUCTURE_PROMPT
PROMPT = MEAL_PLAN_STRUCTURE_PROMPT
