"""
개인화 설정 파일
팀원별 개인 설정을 외부에서 관리

사용법:
1. 이 파일을 복사하여 .personal_config.py로 생성
2. 원하는 에이전트 설정을 수정
3. .gitignore에 .personal_config.py 추가하여 개인 설정 보호

설정 구조:
- agent_name: AI가 자신을 소개할 때 사용할 이름 (예: "키토 마스터", "맛집 헌터") 프롬포트 적용된거 쉽게 확인하라고 해둔것
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
    "agent_name": "수빈의 키토 식단 마스터",    #"안녕하세요! 수빈의 키토 식단 마스터입니다 😊"
    "prompts": {
        "structure": "soobin_structure",     # 식단표 구조 계획 프롬프트
        "generation": "soobin_generation",   # 개별 레시피 생성 프롬프트
        "notes": "soobin_notes"              # 식단표 조언 프롬프트
    },
    "tools": {
        "keto_score": "soobin_keto_score"    # 키토 친화도 점수 계산 도구
    }
}

# 식당 에이전트 개인화 설정
RESTAURANT_AGENT_CONFIG = {
    "agent_name": "수빈의 맛집 헌터", 
    "prompts": {
        "search_improvement": "soobin_search_improvement",  # 검색 키워드 개선 프롬프트
        "search_failure": "soobin_search_failure",          # 검색 실패 처리 프롬프트
        "recommendation": "soobin_recommendation"           # 식당 추천 프롬프트
    },
    "tools": {
        "place_search": "soobin_place_search"               # 장소 검색 도구
    }
}

# 채팅 에이전트 개인화 설정  
CHAT_AGENT_CONFIG = {
    "agent_name": "수빈의 키토 코치",
    "prompt_file_name": "soobin_general_chat"                   # 일반 채팅 프롬프트
}

# 전체 에이전트 설정 통합
AGENT_CONFIGS = {
    "meal_planner": MEAL_PLANNER_CONFIG,
    "restaurant_agent": RESTAURANT_AGENT_CONFIG, 
    "chat_agent": CHAT_AGENT_CONFIG
}


