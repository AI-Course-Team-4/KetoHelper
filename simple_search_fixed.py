#!/usr/bin/env python3
"""
새로운 스키마에 맞춘 간단한 벡터 서칭 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def test_vector_search_new_schema():
    """새로운 스키마로 벡터 서칭 테스트"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        from src.database import DatabaseManager
        from src.embedding import EmbeddingGenerator
        
        print("🔍 벡터 서치 서비스 초기화 중...")
        db = DatabaseManager()
        embedding_gen = EmbeddingGenerator(db)
        
        print("✅ 벡터 서치 서비스가 성공적으로 초기화되었습니다!")
        
        # 대화형 검색 시작
        print("\n" + "="*60)
        print("🎯 벡터 서칭 테스트 모드 (새로운 스키마)")
        print("💡 검색어를 입력하면 유사한 메뉴를 찾아드립니다!")
        print("💡 종료하려면 'quit', 'exit', '종료', 'q' 를 입력하세요.")
        print("="*60)
        
        while True:
            query = input("\n🔍 검색어를 입력하세요: ").strip()
            
            if query.lower() in ['quit', 'exit', '종료', 'q']:
                print("👋 검색을 종료합니다.")
                break
            
            if not query:
                print("❌ 검색어를 입력해주세요.")
                continue
            
            # 결과 개수 입력
            try:
                top_k_input = input("📊 결과 개수 (기본값: 5): ").strip()
                top_k = int(top_k_input) if top_k_input else 5
                top_k = max(1, min(top_k, 20))  # 1-20 사이로 제한
            except ValueError:
                top_k = 5
            
            print(f"\n🔍 '{query}' 검색 중... (상위 {top_k}개)")
            
            try:
                # 검색 쿼리 임베딩 생성
                query_embedding = embedding_gen.generate_embedding(query)
                if not query_embedding:
                    print("❌ 임베딩 생성 실패")
                    continue
                
                # 새로운 스키마에 맞는 벡터 검색 쿼리
                # 레스토랑 정보와 조인하여 검색
                result = db.client.rpc('search_menus_with_restaurants', {
                    'query_embedding': query_embedding,
                    'match_threshold': 0.0,
                    'match_count': top_k
                }).execute()
                
                if result.data:
                    print(f"\n✅ {len(result.data)}개 결과 발견:")
                    print("=" * 60)
                    
                    for i, menu in enumerate(result.data, 1):
                        print(f"\n{i}. {menu.get('restaurant_name', 'N/A')} - {menu.get('menu_name', 'N/A')}")
                        print(f"   📍 주소: {menu.get('restaurant_address', '주소 정보 없음')}")
                        if menu.get('price'):
                            print(f"   💰 가격: {menu['price']:,}원")
                        else:
                            print("   💰 가격: 미정")
                        print(f"   🏷️  카테고리: {menu.get('restaurant_category', '미분류')}")
                        print(f"   📊 유사도: {menu.get('similarity', 0):.4f}")
                        if menu.get('description'):
                            print(f"   📝 설명: {menu['description']}")
                else:
                    # RPC 함수가 없는 경우 직접 조인 쿼리 시도
                    print("⚠️ RPC 함수를 찾을 수 없습니다. 직접 조인 쿼리를 시도합니다...")
                    
                    # 메뉴와 레스토랑을 조인하여 검색
                    result = db.client.table('menus')\
                        .select('*, restaurants(*)')\
                        .not_.is_('embedding', 'null')\
                        .limit(top_k)\
                        .execute()
                    
                    if result.data:
                        print(f"\n✅ {len(result.data)}개 결과 발견 (직접 조회):")
                        print("=" * 60)
                        
                        # 간단한 텍스트 매칭으로 정렬 (임시)
                        query_lower = query.lower()
                        scored_results = []
                        
                        for menu in result.data:
                            menu_text = menu.get('menu_text', '').lower()
                            menu_name = menu.get('name', '').lower()
                            
                            # 간단한 텍스트 매칭 점수
                            score = 0
                            if query_lower in menu_text:
                                score += 2
                            if query_lower in menu_name:
                                score += 3
                            
                            # 부분 매칭 점수
                            for word in query_lower.split():
                                if word in menu_text:
                                    score += 1
                                if word in menu_name:
                                    score += 1
                            
                            scored_results.append((score, menu))
                        
                        # 점수 순으로 정렬
                        scored_results.sort(key=lambda x: x[0], reverse=True)
                        
                        for i, (score, menu) in enumerate(scored_results[:top_k], 1):
                            restaurant = menu.get('restaurants', {}) or {}
                            
                            print(f"\n{i}. {restaurant.get('name', 'N/A')} - {menu.get('name', 'N/A')}")
                            print(f"   📍 주소: {restaurant.get('address', '주소 정보 없음')}")
                            if menu.get('price'):
                                print(f"   💰 가격: {menu['price']:,}원")
                            else:
                                print("   💰 가격: 미정")
                            print(f"   🏷️  카테고리: {restaurant.get('category', '미분류')}")
                            print(f"   📊 매칭 점수: {score}")
                            if menu.get('description'):
                                print(f"   📝 설명: {menu['description']}")
                            print(f"   📄 메뉴 텍스트: {menu.get('menu_text', 'N/A')[:100]}...")
                    else:
                        print("❌ 검색 결과가 없습니다.")
                        print("💡 다른 검색어를 시도해보세요.")
                    
            except Exception as e:
                print(f"❌ 검색 중 오류 발생: {e}")
                print("💡 데이터베이스 연결이나 설정을 확인해주세요.")
        
    except ImportError as e:
        print(f"❌ 모듈 임포트 오류: {e}")
        print("💡 필요한 패키지가 설치되어 있는지 확인해주세요.")
        print("💡 pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ 벡터 서칭 테스트 중 오류: {e}")

def main():
    """메인 함수"""
    print("🎯 벡터 서칭 테스트 도구 (새로운 스키마)")
    print("=" * 50)
    
    # 환경 설정 확인
    if not os.path.exists('.env'):
        print("❌ .env 파일이 없습니다.")
        print("💡 환경 설정을 완료한 후 다시 실행해주세요.")
        return
    
    # 벡터 서칭 테스트
    test_vector_search_new_schema()

if __name__ == "__main__":
    main()
