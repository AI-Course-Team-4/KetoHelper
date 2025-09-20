"""
식당 추천 생성 기본 프롬프트
검색된 식당들을 개인화하여 추천
"""

RESTAURANT_RECOMMENDATION_PROMPT = """
검색된 식당들을 바탕으로 개인화된 추천을 생성하세요.

사용자 요청: "{message}"
식당 목록: {restaurants}
사용자 프로필: {profile}

키토 관점에서 각 식당의 장점과 주문 팁을 포함한 추천을 제공해주세요.
"""

# Restaurant Agent에서 분리된 기본 프롬프트
DEFAULT_RECOMMENDATION_PROMPT = """
검색된 식당들을 바탕으로 개인화된 추천을 생성하세요.

사용자 요청: "{message}"
식당 목록: {restaurants}
사용자 프로필: {profile}

키토 관점에서 각 식당의 장점과 주문 팁을 포함한 추천을 제공해주세요.
"""

# 다른 접근법들
RECOMMENDATION_PROMPT = RESTAURANT_RECOMMENDATION_PROMPT
PROMPT = RESTAURANT_RECOMMENDATION_PROMPT
