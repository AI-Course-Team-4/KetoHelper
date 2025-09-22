"""
식당 검색 실패시 응답 프롬프트
"""

PLACE_SEARCH_FAILURE_PROMPT = """
사용자가 "{message}"라고 요청했지만 주변 지역에서 적절한 키토 친화적인 식당을 찾지 못했습니다.

다음과 같이 친근하고 도움이 되는 응답을 해주세요:

1. 검색 결과가 없다는 점을 양해 구하기
2. 키토 식단에 맞는 일반적인 식당 선택 팁 제공
3. 대안 제안 (예: 직접 요리, 온라인 주문, 다른 지역 검색)
4. 키토 식단을 고려한 외식 가이드 제공

응답은 200자 이내로 간결하고 실용적으로 작성해주세요.
"""

# Restaurant Agent에서 분리된 기본 프롬프트
DEFAULT_SEARCH_FAILURE_PROMPT = """
식당 검색 결과가 없을 때 도움이 되는 대안을 제시하세요.

검색 요청: "{message}"

키토 식단에 적합한 일반적인 조언과 대안을 제공해주세요.
"""

# 다른 접근법들
SEARCH_FAILURE_PROMPT = PLACE_SEARCH_FAILURE_PROMPT
PROMPT = PLACE_SEARCH_FAILURE_PROMPT
