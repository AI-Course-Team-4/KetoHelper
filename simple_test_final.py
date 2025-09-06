#!/usr/bin/env python3
"""
최종 벡터 서칭 테스트 스크립트 - 직접 조인 방식
"""

import os
import sys
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def search_menus():
    """메뉴 검색 테스트"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        from src.database import DatabaseManager
        
        print("🔍 벡터 서치 서비스 초기화 중...")
        db = DatabaseManager()
        
        print("✅ 데이터베이스 연결 성공!")
        
        # 대화형 검색 시작
        print("\n" + "="*60)
        print("🎯 메뉴 검색 테스트")
        print("💡 검색어를 입력하면 관련 메뉴를 찾아드립니다!")
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
                # 메뉴와 레스토랑을 조인하여 검색
                result = db.client.table('menus')\
                    .select('*, restaurants(*)')\
                    .not_.is_('embedding', 'null')\
                    .limit(top_k * 3)\
                    .execute()
                
                if result.data:
                    # 간단한 텍스트 매칭으로 정렬
                    query_lower = query.lower()
                    scored_results = []
                    
                    for menu in result.data:
                        menu_text = menu.get('menu_text', '').lower()
                        menu_name = menu.get('name', '').lower()
                        description = menu.get('description', '').lower() if menu.get('description') else ''
                        
                        # 텍스트 매칭 점수 계산
                        score = 0
                        
                        # 완전 매칭 (높은 점수)
                        if query_lower in menu_text:
                            score += 10
                        if query_lower in menu_name:
                            score += 15
                        if query_lower in description:
                            score += 8
                        
                        # 부분 매칭 (중간 점수)
                        for word in query_lower.split():
                            if len(word) > 1:  # 1글자 단어는 제외
                                if word in menu_text:
                                    score += 3
                                if word in menu_name:
                                    score += 5
                                if word in description:
                                    score += 2
                        
                        # 점수가 0보다 큰 것만 결과에 포함
                        if score > 0:
                            scored_results.append((score, menu))
                    
                    # 점수 순으로 정렬
                    scored_results.sort(key=lambda x: x[0], reverse=True)
                    
                    if scored_results:
                        print(f"\n✅ {len(scored_results)}개 결과 발견:")
                        print("=" * 60)
                        
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
                            
                            # 메뉴 텍스트 미리보기
                            menu_text = menu.get('menu_text', 'N/A')
                            if len(menu_text) > 100:
                                menu_text = menu_text[:100] + "..."
                            print(f"   📄 메뉴 정보: {menu_text}")
                    else:
                        print("❌ 검색어와 일치하는 결과가 없습니다.")
                        print("💡 다른 검색어를 시도해보세요.")
                        
                        # 전체 메뉴 목록 표시 (참고용)
                        print("\n📋 사용 가능한 메뉴 목록:")
                        for i, menu in enumerate(result.data[:5], 1):
                            restaurant = menu.get('restaurants', {}) or {}
                            print(f"  {i}. {restaurant.get('name', 'N/A')} - {menu.get('name', 'N/A')}")
                else:
                    print("❌ 데이터베이스에 메뉴 데이터가 없습니다.")
                    print("💡 먼저 데이터를 로드해주세요.")
                    
            except Exception as e:
                print(f"❌ 검색 중 오류 발생: {e}")
                print("💡 데이터베이스 연결을 확인해주세요.")
        
    except Exception as e:
        print(f"❌ 서비스 초기화 중 오류: {e}")

def main():
    """메인 함수"""
    print("🎯 메뉴 검색 테스트 도구")
    print("=" * 50)
    
    # 환경 설정 확인
    if not os.path.exists('.env'):
        print("❌ .env 파일이 없습니다.")
        print("💡 환경 설정을 완료한 후 다시 실행해주세요.")
        return
    
    # 검색 테스트
    search_menus()

if __name__ == "__main__":
    main()
