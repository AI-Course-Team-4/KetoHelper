"""
팀원별 프롬프트 실험 설정 파일
팀원들이 프롬프트를 개선하고 테스트하기 위한 시스템

사용법:
1. 이 파일을 복사하여 .personal_config.py로 생성
2. 원하는 프롬프트 파일명을 수정하여 실험
3. .gitignore에 .personal_config.py 추가하여 개인 실험 보호
4. USE_PERSONAL_CONFIG = True로 설정하여 개인 실험 활성화

설정 구조:
- agent_name: AI가 자신을 소개할 때 사용할 이름 (프롬프트 적용 확인용)
- prompts: 프롬프트 파일명 매핑 (팀원별 실험용)
- tools: 도구 파일명 매핑 (팀원별 실험용)

실험 예시:
- "soobin_recipe_response": 수빈이 만든 레시피 응답 프롬프트
- "soobin_general_chat": 수빈이 만든 일반 채팅 프롬프트
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
        "notes": "soobin_notes",             # 식단표 조언 프롬프트
        "embedding_based": "soobin_embedding_based",  # 임베딩 기반 검색 프롬프트
        "fallback": "soobin_fallback",       # 폴백 프롬프트
        "recipe_response": "soobin_recipe_response",  # 레시피 응답 프롬프트
        "single_recipe": "soobin_single_recipe"       # 단일 레시피 프롬프트
    },
    "tools": {
        "keto_score": "soobin_keto_score",           # 키토 친화도 점수 계산 도구
        "korean_search": "soobin_korean_search",     # 한국어 검색 도구
        "recipe_response_formatter": "soobin_recipe_response_formatter"  # 레시피 응답 포맷터
    }
}

# 식당 에이전트 개인화 설정
RESTAURANT_AGENT_CONFIG = {
    "agent_name": "수빈의 맛집 헌터", 
    "prompts": {
        "search_improvement": "soobin_search_improvement",  # 검색 키워드 개선 프롬프트
        "search_failure": "soobin_search_failure",          # 검색 실패 처리 프롬프트
        "recommendation": "soobin_recommendation",          # 식당 추천 프롬프트
        "fallback": "soobin_fallback"                       # 폴백 프롬프트
    },
    "tools": {
        "place_search": "soobin_place_search",              # 장소 검색 도구
        "restaurant_hybrid_search": "soobin_restaurant_hybrid_search"  # 하이브리드 검색 도구
    }
}

# 채팅 에이전트 개인화 설정  
CHAT_AGENT_CONFIG = {
    "agent_name": "수빈의 키토 코치",
    "prompts": {
        "general_chat": "soobin_general_chat",              # 일반 채팅 프롬프트
        "fallback": "soobin_fallback",                      # 폴백 프롬프트
        "intent_classification": "soobin_intent_classification",  # 의도 분류 프롬프트
        "memory_update": "soobin_memory_update",            # 메모리 업데이트 프롬프트
        "response_generation": "soobin_response_generation" # 응답 생성 프롬프트
    }
}

# 오케스트레이터 개인화 설정 (팀원별 프롬프트 실험용)
ORCHESTRATOR_CONFIG = {
    "prompts": {
        "recipe_response": "soobin_recipe_response",            # 레시피 응답 생성 프롬프트
        "restaurant_response": "soobin_restaurant_response"     # 식당 응답 생성 프롬프트
    }
}

# 전체 에이전트 설정 통합
AGENT_CONFIGS = {
    "meal_planner": MEAL_PLANNER_CONFIG,
    "restaurant_agent": RESTAURANT_AGENT_CONFIG, 
    "chat_agent": CHAT_AGENT_CONFIG,
    "orchestrator": ORCHESTRATOR_CONFIG
}

# ============================================================================
# 업데이트된 프롬프트 및 도구 목록 (2024.09.26)
# ============================================================================
# 
# Meal Planner 추가된 항목:
# - embedding_based: 임베딩 기반 검색 프롬프트
# - fallback: 폴백 프롬프트  
# - recipe_response: 레시피 응답 프롬프트
# - single_recipe: 단일 레시피 프롬프트
# - korean_search: 한국어 검색 도구
# - recipe_response_formatter: 레시피 응답 포맷터
#
# Restaurant Agent 추가된 항목:
# - fallback: 폴백 프롬프트
# - restaurant_hybrid_search: 하이브리드 검색 도구
#
# Chat Agent 추가된 항목:
# - fallback: 폴백 프롬프트
# - intent_classification: 의도 분류 프롬프트
# - memory_update: 메모리 업데이트 프롬프트
# - response_generation: 응답 생성 프롬프트
#
# 사용법: USE_PERSONAL_CONFIG = True로 변경하여 개인 설정 활성화


