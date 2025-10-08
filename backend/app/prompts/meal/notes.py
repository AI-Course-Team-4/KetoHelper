"""
식단표 조언 생성 프롬프트
생성된 키토 식단표에 대한 실용적인 조언 제공
"""

MEAL_PLAN_NOTES_PROMPT = """
        다음 키토 식단표에 대한 실용적인 조언 2개를 생성하세요.
        
        제약 조건: {constraints}
        
        간결하고 실용적인 키토 다이어트 팁으로 작성하세요.
        """

# Meal Agent에서 분리된 기본 조언 프롬프트
DEFAULT_NOTES_PROMPT = """
키토 식단표에 대한 실용적인 조언을 생성하세요.
제약 조건: {constraints}

2가지 핵심 팁을 제공해주세요.
"""

# 다른 접근법들
NOTES_PROMPT = MEAL_PLAN_NOTES_PROMPT
PROMPT = MEAL_PLAN_NOTES_PROMPT
