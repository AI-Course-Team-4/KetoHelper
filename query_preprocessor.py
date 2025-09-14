#!/usr/bin/env python3
"""
쿼리 전처리 모듈
검색 성능 향상을 위한 쿼리 정제 및 핵심 키워드 추출
"""

import re
from typing import List, Set
from synonym_dictionary import expand_query_with_synonyms, normalize_query

# 불용어 사전 (보수적으로 축소)
STOP_WORDS = {
    # 기본 조사만 (핵심 키워드 보호)
    "가", "이", "을", "를", "의", "에", "에서", "로", "으로", "와", "과", "도", "만",
    
    # 기본 어미만
    "는", "은", "한", "인", "된",
    
    # 명확한 불용어만
    "그리고", "또한", "또는", "그런데", "하지만", "그러나", "따라서", "그래서",
    "이것", "저것", "그것", "이런", "저런", "그런", "이렇게", "저렇게", "그렇게",
    "정말", "진짜", "정말로", "진짜로", "아주", "매우", "너무", "굉장히"
}

# 핵심 키워드 우선순위 (높은 점수)
PRIORITY_KEYWORDS = {
    # 식재료 (최고 우선순위)
    "아보카도", "올리브유", "올리브오일", "마늘", "양파", "계란", "달걀", "토마토", 
    "치즈", "베이컨", "버터", "우유", "닭고기", "돼지고기", "소고기", "생선",
    
    # 조리법 (높은 우선순위)
    "볶음", "구운", "구이", "찜", "튀김", "샐러드", "스프", "스테이크", "스크램블",
    "파스타", "피자", "샌드위치", "스무디", "케이크", "쿠키", "빵", "김밥",
    
    # 맛/특성 (중간 우선순위)
    "매운", "달콤한", "단맛", "짠", "신", "고소한", "진한", "부드러운", "바삭한",
    
    # 건강/다이어트 (중간 우선순위)
    "keto", "케토", "키토", "저탄수화물", "저탄", "고단백", "다이어트", "건강", "무설탕"
}

def remove_stop_words(query: str) -> str:
    """
    불용어 제거
    
    Args:
        query: 원본 쿼리
        
    Returns:
        불용어가 제거된 쿼리
    """
    words = query.split()
    filtered_words = [word for word in words if word not in STOP_WORDS]
    return " ".join(filtered_words)

def remove_particles_and_endings(query: str) -> str:
    """
    한국어 조사/어미 제거 (보수적 접근)
    
    Args:
        query: 원본 쿼리
        
    Returns:
        조사/어미가 제거된 쿼리
    """
    # 보수적인 조사/어미 제거 패턴 (핵심 키워드 보호)
    particle_patterns = [
        r'\b[가이을를의에에서로으로와과도만]\b',  # 단어 경계가 있는 조사만
        r'\b[는은한인된]\b',  # 단어 경계가 있는 어미만
    ]
    
    cleaned_query = query
    for pattern in particle_patterns:
        cleaned_query = re.sub(pattern, '', cleaned_query)
    
    # 연속된 공백 제거
    cleaned_query = re.sub(r'\s+', ' ', cleaned_query).strip()
    
    return cleaned_query

def extract_core_keywords(query: str) -> List[str]:
    """
    핵심 키워드 추출
    
    Args:
        query: 원본 쿼리
        
    Returns:
        핵심 키워드 리스트
    """
    # 1. 불용어 제거
    cleaned_query = remove_stop_words(query)
    
    # 2. 조사/어미 제거
    cleaned_query = remove_particles_and_endings(cleaned_query)
    
    # 3. 단어 분리
    words = cleaned_query.split()
    
    # 4. 우선순위 키워드 필터링
    core_keywords = []
    for word in words:
        if word in PRIORITY_KEYWORDS:
            core_keywords.append(word)
        elif len(word) >= 2:  # 2글자 이상인 단어만 포함
            core_keywords.append(word)
    
    return core_keywords

def preprocess_query(query: str, use_synonyms: bool = True) -> str:
    """
    쿼리 전처리 메인 함수
    
    Args:
        query: 원본 쿼리
        use_synonyms: 동의어 확장 사용 여부
        
    Returns:
        전처리된 쿼리
    """
    # 1. 기본 정제
    cleaned_query = query.strip()
    
    # 2. 핵심 키워드 추출
    core_keywords = extract_core_keywords(cleaned_query)
    
    if not core_keywords:
        # 핵심 키워드가 없으면 원본 쿼리 반환
        return query
    
    # 3. 동의어 확장 (선택적)
    if use_synonyms:
        expanded_keywords = []
        for keyword in core_keywords:
            expanded_keywords.append(keyword)
            # 동의어 확장
            expanded_query = expand_query_with_synonyms(keyword)
            expanded_terms = expanded_query.split()
            expanded_keywords.extend(expanded_terms)
        
        # 중복 제거
        unique_keywords = list(dict.fromkeys(expanded_keywords))
        return " ".join(unique_keywords)
    else:
        return " ".join(core_keywords)

def preprocess_for_vector_search(query: str) -> str:
    """
    벡터 검색용 쿼리 전처리 (최소한의 전처리)
    
    Args:
        query: 원본 쿼리
        
    Returns:
        벡터 검색용 전처리된 쿼리
    """
    # 벡터 검색은 원본 쿼리를 최대한 보존
    # OpenAI 임베딩 모델이 자연어를 잘 처리하므로 최소한의 전처리만
    
    # 1. 기본적인 불용어만 제거
    cleaned_query = remove_stop_words(query)
    
    # 2. 조사/어미는 제거하지 않음 (의미 보존)
    
    # 3. 빈 쿼리인 경우 원본 반환
    if not cleaned_query.strip():
        return query
    
    return cleaned_query

def preprocess_for_keyword_search(query: str) -> str:
    """
    키워드 검색용 쿼리 전처리 (동의어 확장 포함)
    
    Args:
        query: 원본 쿼리
        
    Returns:
        키워드 검색용 전처리된 쿼리
    """
    return preprocess_query(query, use_synonyms=True)

def test_query_preprocessing():
    """쿼리 전처리 테스트"""
    test_queries = [
        "아보카도가 들어간 건강한 음식",
        "올리브유로 만드는 이탈리안 요리", 
        "마늘 향이 진한 한국 요리",
        "계란을 주재료로 하는 아침 식사",
        "양파 없이 만드는 요리",
        "keto 다이어트 요리",
        "저탄수화물 건강식",
        "매운 음식 만들기",
        "달콤한 디저트 레시피"
    ]
    
    print("🧪 쿼리 전처리 테스트")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n원본 쿼리: '{query}'")
        
        # 키워드 검색용 전처리
        keyword_processed = preprocess_for_keyword_search(query)
        print(f"키워드용:   '{keyword_processed}'")
        
        # 벡터 검색용 전처리
        vector_processed = preprocess_for_vector_search(query)
        print(f"벡터용:     '{vector_processed}'")
        
        # 핵심 키워드만 추출
        core_keywords = extract_core_keywords(query)
        print(f"핵심 키워드: {core_keywords}")

if __name__ == "__main__":
    test_query_preprocessing()
