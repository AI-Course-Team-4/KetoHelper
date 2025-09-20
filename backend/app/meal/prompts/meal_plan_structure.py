"""
식단표 구조 계획 프롬프트
일정 기간의 키토 식단 구조를 계획
"""

MEAL_PLAN_STRUCTURE_PROMPT = """
        {days}일간의 키토 식단 구조를 계획하세요.
        
        제약 조건: {constraints}
        
        각 날짜별로 아침/점심/저녁의 대략적인 메뉴 타입을 정하세요.
        
        키토 원칙:
        - 아침: 간단하고 지방 위주 (계란, 아보카도, 치즈 등)
        - 점심: 단백질 + 채소 (샐러드, 구이, 볶음 등)  
        - 저녁: 풍성한 단백질 + 발효 채소 (고기, 생선 + 김치, 나물 등)
        - 간식: 견과류, 치즈, 올리브 등
        
        다양성을 고려하여 반복되지 않도록 하세요.
        
        JSON 형태로 응답하세요:
        [
            {{
                "day": 1,
                "breakfast_type": "계란 요리",
                "lunch_type": "샐러드",
                "dinner_type": "고기 구이",
                "snack_type": "견과류"
            }},
            ...
        ]
        """

# Meal Agent에서 분리된 기본 구조 프롬프트
DEFAULT_STRUCTURE_PROMPT = """
{days}일 키토 식단표의 전체 구조를 계획하세요.
제약 조건: {constraints}

다음 JSON 형태로 응답하세요:
[
    {{
        "day": 1,
        "breakfast_type": "아침 메뉴 타입",
        "lunch_type": "점심 메뉴 타입", 
        "dinner_type": "저녁 메뉴 타입",
        "snack_type": "간식 타입"
    }}
]
"""

# 다른 접근법들
STRUCTURE_PROMPT = MEAL_PLAN_STRUCTURE_PROMPT
PROMPT = MEAL_PLAN_STRUCTURE_PROMPT