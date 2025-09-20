"""
식당 검색 쿼리 개선 기본 프롬프트
사용자 요청을 효과적인 검색 키워드로 변환
"""

PLACE_SEARCH_IMPROVEMENT_PROMPT = """
사용자의 식당 검색 요청을 분석하여 더 효과적인 검색 키워드를 생성하세요.

사용자 메시지: "{message}"

키토 식단에 적합한 식당을 찾기 위한 검색 키워드들을 쉼표로 구분하여 제시하세요.
예: "스테이크하우스", "구이 전문점", "샐러드 전문점"
"""

# Restaurant Agent에서 분리된 기본 프롬프트
DEFAULT_SEARCH_IMPROVEMENT_PROMPT = """
사용자의 식당 검색 요청을 분석하여 더 효과적인 검색 키워드를 생성하세요.

사용자 메시지: "{message}"

키토 식단에 적합한 식당을 찾기 위한 검색 키워드들을 쉼표로 구분하여 제시하세요.
예: "스테이크하우스", "구이 전문점", "샐러드 전문점"
"""

# 다른 접근법들
SEARCH_IMPROVEMENT_PROMPT = PLACE_SEARCH_IMPROVEMENT_PROMPT
PROMPT = PLACE_SEARCH_IMPROVEMENT_PROMPT
