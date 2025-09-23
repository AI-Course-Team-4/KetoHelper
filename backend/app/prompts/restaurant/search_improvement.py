"""
장소 검색 키워드 개선 프롬프트
사용자 요청을 카카오 로컬 검색에 적합한 키워드로 변환
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

# 간단한 키워드 개선 프롬프트
SIMPLE_SEARCH_IMPROVEMENT_PROMPT = """
사용자 요청을 카카오 로컬 검색에 적합한 키워드로 변환하세요.

사용자 요청: "{message}"

키토 친화적인 검색 키워드 (1-3개)를 반환하세요:
예시: "구이", "샤브샤브", "샐러드", "스테이크", "회"
"""

# 다른 접근법들
SEARCH_IMPROVEMENT_PROMPT = PLACE_SEARCH_IMPROVEMENT_PROMPT
PROMPT = PLACE_SEARCH_IMPROVEMENT_PROMPT
