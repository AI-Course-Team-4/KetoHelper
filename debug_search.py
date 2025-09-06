#!/usr/bin/env python3
"""
벡터 서칭 디버그 스크립트
데이터베이스 상태와 검색 기능을 단계별로 테스트합니다.
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        from src.database import DatabaseManager
        
        print("🔍 데이터베이스 연결 테스트 중...")
        db = DatabaseManager()
        
        # 연결 테스트
        if db.test_connection():
            print("✅ 데이터베이스 연결 성공!")
        else:
            print("❌ 데이터베이스 연결 실패!")
            return False
        
        # 메뉴 개수 확인
        menu_count = db.get_menu_count()
        print(f"📊 총 메뉴 개수: {menu_count}개")
        
        if menu_count == 0:
            print("⚠️ 데이터베이스에 메뉴 데이터가 없습니다.")
            print("💡 먼저 데이터를 로드해야 합니다: python src/data_loader.py")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 테스트 중 오류: {e}")
        return False

def test_direct_query():
    """직접 SQL 쿼리 테스트"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        from src.database import DatabaseManager
        
        print("\n🔍 직접 쿼리 테스트 중...")
        db = DatabaseManager()
        
        # 샘플 데이터 조회
        result = db.client.table('menus').select('*').limit(3).execute()
        
        if result.data:
            print("✅ 샘플 데이터 조회 성공!")
            print("=" * 50)
            for i, menu in enumerate(result.data, 1):
                print(f"{i}. {menu.get('restaurant_name', 'N/A')} - {menu.get('menu_name', 'N/A')}")
                print(f"   주소: {menu.get('address', 'N/A')}")
                print(f"   가격: {menu.get('price', 'N/A')}")
                print(f"   카테고리: {menu.get('category', 'N/A')}")
                print(f"   임베딩 존재: {'있음' if menu.get('embedding') else '없음'}")
                print()
            return True
        else:
            print("❌ 데이터 조회 결과가 없습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 직접 쿼리 테스트 중 오류: {e}")
        return False

def test_vector_function():
    """벡터 검색 함수 테스트"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        from src.database import DatabaseManager
        from src.embedding import EmbeddingGenerator
        
        print("\n🔍 벡터 검색 함수 테스트 중...")
        
        db = DatabaseManager()
        embedding_gen = EmbeddingGenerator(db)
        
        # 테스트 쿼리 임베딩 생성
        test_query = "맛있는 음식"
        print(f"테스트 쿼리: '{test_query}'")
        
        query_embedding = embedding_gen.generate_embedding(test_query)
        if not query_embedding:
            print("❌ 임베딩 생성 실패")
            return False
        
        print("✅ 임베딩 생성 성공!")
        
        # 벡터 검색 수행
        results = db.vector_search(query_embedding, 3)
        
        if results:
            print("✅ 벡터 검색 성공!")
            print("=" * 50)
            for i, result in enumerate(results, 1):
                print(f"{i}. 결과:")
                for key, value in result.items():
                    if key != 'embedding':  # 임베딩은 너무 길어서 제외
                        print(f"   {key}: {value}")
                print()
            return True
        else:
            print("❌ 벡터 검색 결과가 없습니다.")
            return False
            
    except Exception as e:
        print(f"❌ 벡터 검색 함수 테스트 중 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("🔧 벡터 서칭 디버그 도구")
    print("=" * 50)
    
    # 1. 데이터베이스 연결 테스트
    if not test_database_connection():
        return
    
    # 2. 직접 쿼리 테스트
    if not test_direct_query():
        return
    
    # 3. 벡터 검색 함수 테스트
    if not test_vector_function():
        return
    
    print("\n🎉 모든 테스트가 성공했습니다!")
    print("💡 이제 simple_search_test.py를 다시 실행해보세요.")

if __name__ == "__main__":
    main()
