"""
개인화 설정 파일
팀원별 개인 설정을 외부에서 관리

사용법:
1. 이 파일을 복사하여 .personal_config.py로 생성
2. 원하는 에이전트 설정을 수정
3. .gitignore에 .personal_config.py 추가하여 개인 설정 보호

설정 구조:
- agent_name: 에이전트 이름 (개인 브랜딩)
- prompts: 프롬프트 파일명 매핑
- tools: 도구 파일명 매핑
"""

# ⚠️ 개인 설정 활성화 여부 - 가장 중요한 설정!
USE_PERSONAL_CONFIG = False  # True로 변경하면 개인 설정 활성화

# ============================================================================
# 아래 설정들은 USE_PERSONAL_CONFIG = True일 때만 적용됩니다
# ============================================================================

# 밀 플래너 개인화 설정
MEAL_PLANNER_CONFIG = {
    "agent_name": "My Custom Meal Agent",
    "prompts": {
        "structure": "my_meal_plan_structure",     # backend/app/meal/prompts/my_meal_plan_structure.py
        "generation": "my_meal_generation",       # backend/app/meal/prompts/my_meal_generation.py
        "notes": "my_meal_notes"                  # backend/app/meal/prompts/my_meal_notes.py
    },
    "tools": {
        "keto_score": "my_keto_score"            # backend/app/meal/tools/my_keto_score.py
    }
}

# 식당 에이전트 개인화 설정
RESTAURANT_AGENT_CONFIG = {
    "agent_name": "My Custom Restaurant Agent", 
    "prompts": {
        "search_improvement": "my_place_search_improvement",  # backend/app/restaurant/prompts/my_place_search_improvement.py
        "search_failure": "my_search_failure",               # backend/app/restaurant/prompts/my_search_failure.py
        "recommendation": "my_restaurant_recommendation"     # backend/app/restaurant/prompts/my_restaurant_recommendation.py
    },
    "tools": {
        "place_search": "my_place_search"                    # backend/app/restaurant/tools/my_place_search.py
    }
}

# 채팅 에이전트 개인화 설정  
CHAT_AGENT_CONFIG = {
    "agent_name": "My Custom Keto Coach",
    "prompt_file_name": "my_general_chat_prompt"            # backend/app/chat/prompts/my_general_chat_prompt.py
}

# 전체 에이전트 설정 통합
AGENT_CONFIGS = {
    "meal_planner": MEAL_PLANNER_CONFIG,
    "restaurant_agent": RESTAURANT_AGENT_CONFIG, 
    "chat_agent": CHAT_AGENT_CONFIG
}


