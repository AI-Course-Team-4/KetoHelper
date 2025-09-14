#!/usr/bin/env python3
"""
테스트 질의셋 생성기
"""

import sys
sys.path.append('src')

from src.config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

def create_test_queries():
    """30개 테스트 질의셋 생성"""
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print("📝 테스트 질의셋 생성")
        print("=" * 50)
        
        # 30개 테스트 질의
        test_queries = [
            # 재료 기반 질의
            {"query": "아몬드 가루로 만드는 디저트", "category": "재료", "difficulty": "초급"},
            {"query": "계란을 많이 사용하는 요리", "category": "재료", "difficulty": "초급"},
            {"query": "두부로 만드는 김밥", "category": "재료", "difficulty": "중급"},
            {"query": "치즈가 들어간 키토 요리", "category": "재료", "difficulty": "초급"},
            {"query": "버터를 사용하는 베이킹", "category": "재료", "difficulty": "중급"},
            {"query": "닭고기로 만드는 요리", "category": "재료", "difficulty": "중급"},
            {"query": "생크림이 들어간 디저트", "category": "재료", "difficulty": "중급"},
            {"query": "연어를 사용하는 요리", "category": "재료", "difficulty": "고급"},
            {"query": "아보카도가 들어간 요리", "category": "재료", "difficulty": "초급"},
            {"query": "코코넛 가루로 만드는 디저트", "category": "재료", "difficulty": "중급"},
            
            # 요리법 기반 질의
            {"query": "굽는 방식의 키토 요리", "category": "조리법", "difficulty": "중급"},
            {"query": "볶음 요리", "category": "조리법", "difficulty": "초급"},
            {"query": "찌는 방식의 요리", "category": "조리법", "difficulty": "초급"},
            {"query": "튀기는 요리", "category": "조리법", "difficulty": "중급"},
            {"query": "끓이는 방식의 요리", "category": "조리법", "difficulty": "초급"},
            {"query": "데치는 방식의 요리", "category": "조리법", "difficulty": "초급"},
            {"query": "무치는 방식의 요리", "category": "조리법", "difficulty": "초급"},
            {"query": "절이는 방식의 요리", "category": "조리법", "difficulty": "중급"},
            
            # 음식 종류 기반 질의
            {"query": "키토 김밥", "category": "음식종류", "difficulty": "중급"},
            {"query": "키토 디저트", "category": "음식종류", "difficulty": "중급"},
            {"query": "키토 빵", "category": "음식종류", "difficulty": "고급"},
            {"query": "키토 케이크", "category": "음식종류", "difficulty": "고급"},
            {"query": "키토 피자", "category": "음식종류", "difficulty": "중급"},
            {"query": "키토 파스타", "category": "음식종류", "difficulty": "중급"},
            {"query": "키토 스무디", "category": "음식종류", "difficulty": "초급"},
            {"query": "키토 샐러드", "category": "음식종류", "difficulty": "초급"},
            
            # 특수 요구사항 기반 질의
            {"query": "빠르게 만들 수 있는 키토 요리", "category": "특수요구", "difficulty": "초급"},
            {"query": "단백질이 많은 키토 요리", "category": "특수요구", "difficulty": "중급"},
            {"query": "저칼로리 키토 요리", "category": "특수요구", "difficulty": "중급"},
            {"query": "아이들이 좋아할 키토 요리", "category": "특수요구", "difficulty": "초급"}
        ]
        
        # 기존 테스트 질의 삭제
        supabase.table('test_queries').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        
        # 새 테스트 질의 삽입
        for query_data in test_queries:
            supabase.table('test_queries').insert(query_data).execute()
        
        print(f"✅ {len(test_queries)}개 테스트 질의 생성 완료")
        
        # 생성된 질의 확인
        created_queries = supabase.table('test_queries').select('*').execute()
        print(f"📊 데이터베이스에 저장된 질의 수: {len(created_queries.data)}개")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류: {str(e)}")
        return False

if __name__ == "__main__":
    create_test_queries()
