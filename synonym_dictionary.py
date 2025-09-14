#!/usr/bin/env python3
"""
동의어 사전 모듈
키워드 검색 성능 향상을 위한 동의어 매핑 제공
"""

# 동의어 사전 (메인 키워드 -> 동의어 리스트)
SYNONYM_DICT = {
    # 식재료 동의어
    "올리브유": ["올리브오일", "엑스트라버진올리브오일", "EVOO"],
    "아보카도": ["아보카도오일"],
    "마늘": ["다진마늘", "마늘가루", "생마늘"],
    "양파": ["다진양파", "양파가루", "생양파"],
    "계란": ["달걀", "계란알", "달걀알"],
    "토마토": ["방울토마토", "체리토마토"],
    "치즈": ["모짜렐라", "체다치즈", "파마산치즈"],
    "베이컨": ["스모크베이컨", "터키베이컨"],
    "버터": ["무염버터", "가염버터"],
    "우유": ["저지방우유", "무지방우유", "두유"],
    
    # 조리법 동의어
    "볶음": ["볶기", "볶아서", "볶음요리"],
    "구운": ["구이", "구워서", "구운요리"],
    "찜": ["찜기", "찜해서", "찜요리"],
    "튀김": ["튀기기", "튀겨서", "튀김요리"],
    "샐러드": ["샐러드요리", "생채"],
    "스프": ["국", "탕", "국물"],
    "스테이크": ["구이", "그릴"],
    "스크램블": ["부치기", "부쳐서"],
    
    # 맛/특성 동의어
    "매운": ["맵게", "고추맛", "고춧가루맛"],
    "달콤한": ["달게", "단맛", "설탕맛"],
    "짠": ["짜게", "소금맛"],
    "신": ["시게", "신맛", "식초맛"],
    "고소한": ["고소하게", "참기름맛", "들기름맛"],
    "진한": ["진하게", "진한맛"],
    "부드러운": ["부드럽게", "연하게"],
    "바삭한": ["바삭하게", "크리스피"],
    
    # 건강/다이어트 관련 동의어
    "keto": ["케토", "키토", "키토제닉"],
    "저탄수화물": ["저탄", "로카브", "로우카브"],
    "고단백": ["고단백질", "프로틴"],
    "다이어트": ["다이어트식", "다이어트용"],
    "건강": ["건강한", "건강식", "건강용"],
    "무설탕": ["설탕없는", "당분없는"],
    "무지방": ["지방없는", "로우팻"],
    "유기농": ["오가닉", "자연농"],
    
    # 요리 종류 동의어
    "파스타": ["스파게티", "면요리"],
    "피자": ["피자요리"],
    "샌드위치": ["샌드", "샌드위치요리"],
    "스무디": ["스무디음료", "드링크"],
    "케이크": ["케이크요리", "디저트"],
    "쿠키": ["쿠키요리", "과자"],
    "빵": ["빵요리", "베이킹"],
    "김밥": ["김밥요리", "롤"],
    
    # 한국어 조사/어미 정규화
    "가": ["이", "을", "를", "의", "에", "에서", "로", "으로"],
    "이": ["가", "을", "를", "의", "에", "에서", "로", "으로"],
    "을": ["를", "가", "이", "의", "에", "에서", "로", "으로"],
    "를": ["을", "가", "이", "의", "에", "에서", "로", "으로"],
    "의": ["가", "이", "을", "를", "에", "에서", "로", "으로"],
    "에": ["에서", "가", "이", "을", "를", "의", "로", "으로"],
    "에서": ["에", "가", "이", "을", "를", "의", "로", "으로"],
    "로": ["으로", "가", "이", "을", "를", "의", "에", "에서"],
    "으로": ["로", "가", "이", "을", "를", "의", "에", "에서"],
    
    # 불용어 (검색에서 제외할 단어들)
    "들어간": ["포함된", "사용된", "넣은"],
    "만드는": ["만든", "제조하는", "조리하는"],
    "음식": ["요리", "식품", "메뉴"],
    "식단": ["식사", "메뉴", "요리"],
    "요리": ["음식", "식품", "메뉴"],
    "만들기": ["만들", "제조", "조리"],
    "방법": ["기법", "요령", "팁"],
    "레시피": ["조리법", "만드는법", "방법"]
}

# 역방향 동의어 사전 (동의어 -> 메인 키워드)
REVERSE_SYNONYM_DICT = {}
for main_keyword, synonyms in SYNONYM_DICT.items():
    for synonym in synonyms:
        REVERSE_SYNONYM_DICT[synonym] = main_keyword

def expand_query_with_synonyms(query: str) -> str:
    """
    쿼리를 동의어로 확장하여 검색 성능 향상
    
    Args:
        query: 원본 검색 쿼리
        
    Returns:
        동의어가 포함된 확장된 쿼리
    """
    expanded_terms = []
    query_terms = query.split()
    
    for term in query_terms:
        # 원본 단어 추가
        expanded_terms.append(term)
        
        # 동의어 추가
        if term in SYNONYM_DICT:
            expanded_terms.extend(SYNONYM_DICT[term])
        elif term in REVERSE_SYNONYM_DICT:
            main_keyword = REVERSE_SYNONYM_DICT[term]
            expanded_terms.append(main_keyword)
            expanded_terms.extend(SYNONYM_DICT[main_keyword])
    
    return " ".join(expanded_terms)

def normalize_query(query: str) -> str:
    """
    쿼리 정규화 (동의어 통합)
    
    Args:
        query: 원본 검색 쿼리
        
    Returns:
        정규화된 쿼리 (메인 키워드로 통합)
    """
    normalized_terms = []
    query_terms = query.split()
    
    for term in query_terms:
        if term in REVERSE_SYNONYM_DICT:
            # 동의어를 메인 키워드로 변환
            normalized_terms.append(REVERSE_SYNONYM_DICT[term])
        else:
            # 메인 키워드이거나 매핑되지 않은 단어는 그대로 유지
            normalized_terms.append(term)
    
    return " ".join(normalized_terms)

def get_synonyms(keyword: str) -> list:
    """
    특정 키워드의 동의어 리스트 반환
    
    Args:
        keyword: 검색할 키워드
        
    Returns:
        동의어 리스트
    """
    if keyword in SYNONYM_DICT:
        return SYNONYM_DICT[keyword]
    elif keyword in REVERSE_SYNONYM_DICT:
        main_keyword = REVERSE_SYNONYM_DICT[keyword]
        return [main_keyword] + SYNONYM_DICT[main_keyword]
    else:
        return [keyword]

def test_synonym_functions():
    """동의어 함수들 테스트"""
    test_queries = [
        "올리브유 파스타",
        "올리브오일 샐러드", 
        "마늘 볶음밥",
        "계란 스크램블",
        "아보카도가 들어간 건강한 음식",
        "keto 다이어트",
        "저탄수화물 요리"
    ]
    
    print("🧪 동의어 사전 테스트")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n원본 쿼리: '{query}'")
        print(f"정규화:    '{normalize_query(query)}'")
        print(f"확장:      '{expand_query_with_synonyms(query)}'")
        
        # 개별 키워드 동의어 확인
        terms = query.split()
        for term in terms:
            synonyms = get_synonyms(term)
            if len(synonyms) > 1:
                print(f"  '{term}' → {synonyms}")

if __name__ == "__main__":
    test_synonym_functions()
