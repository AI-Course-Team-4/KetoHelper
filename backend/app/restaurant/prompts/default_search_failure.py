"""
식당 검색 실패 시 응답 기본 프롬프트
검색 결과가 없을 때 도움이 되는 대안 제시
"""

PLACE_SEARCH_FAILURE_PROMPT = """
식당 검색 결과가 없을 때 도움이 되는 대안을 제시하세요.

검색 요청: "{message}"

키토 식단에 적합한 일반적인 조언과 대안을 제공해주세요.
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
