#!/usr/bin/env python3
"""
실제 벡터 유사도 검색 테스트 스크립트
OpenAI 임베딩을 사용해서 의미적 유사도를 계산합니다.
"""

import os
import sys
import numpy as np
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def calculate_cosine_similarity(vec1, vec2):
    """코사인 유사도 계산"""
    # numpy 배열로 변환
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    # 코사인 유사도 계산
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0
    
    return dot_product / (norm1 * norm2)

def vector_search_with_similarity():
    """벡터 유사도 기반 검색"""
    try:
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        from src.database import DatabaseManager
        from src.embedding import EmbeddingGenerator
        
        print("🔍 벡터 검색 서비스 초기화 중...")
        db = DatabaseManager()
        embedding_gen = EmbeddingGenerator(db)
        
        print("✅ 벡터 검색 서비스가 성공적으로 초기화되었습니다!")
        
        # 대화형 검색 시작
        print("\n" + "="*70)
        print("🎯 실제 벡터 유사도 검색 테스트")
        print("💡 OpenAI 임베딩을 사용해서 의미적 유사도를 계산합니다!")
        print("💡 종료하려면 'quit', 'exit', '종료', 'q' 를 입력하세요.")
        print("="*70)
        
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
            
            print(f"\n🔍 '{query}' 벡터 검색 중... (상위 {top_k}개)")
            
            try:
                # 1. 검색 쿼리의 임베딩 생성
                print("📊 검색어 임베딩 생성 중...")
                query_embedding = embedding_gen.generate_embedding(query)
                if not query_embedding:
                    print("❌ 검색어 임베딩 생성 실패")
                    continue
                
                print("✅ 검색어 임베딩 생성 완료!")
                
                # 2. 모든 메뉴 데이터와 임베딩 가져오기
                print("📊 메뉴 데이터 로드 중...")
                result = db.client.table('menus')\
                    .select('*, restaurants(*)')\
                    .not_.is_('embedding', 'null')\
                    .execute()
                
                if not result.data:
                    print("❌ 임베딩이 있는 메뉴 데이터가 없습니다.")
                    continue
                
                print(f"✅ {len(result.data)}개 메뉴 데이터 로드 완료!")
                
                # 3. 각 메뉴와의 유사도 계산
                print("🧮 유사도 계산 중...")
                similarities = []
                
                for menu in result.data:
                    menu_embedding = menu.get('embedding')
                    if menu_embedding:
                        try:
                            # 임베딩이 문자열인 경우 리스트로 변환
                            if isinstance(menu_embedding, str):
                                # PostgreSQL 배열 형식 파싱 시도
                                menu_embedding = menu_embedding.strip('[]').split(',')
                                menu_embedding = [float(x.strip()) for x in menu_embedding]
                            elif isinstance(menu_embedding, list):
                                menu_embedding = [float(x) for x in menu_embedding]
                            
                            # 코사인 유사도 계산
                            similarity = calculate_cosine_similarity(query_embedding, menu_embedding)
                            similarities.append((similarity, menu))
                        except (ValueError, TypeError) as e:
                            print(f"⚠️ 임베딩 변환 오류 (메뉴: {menu.get('name', 'N/A')}): {e}")
                            continue
                
                # 4. 유사도 순으로 정렬
                similarities.sort(key=lambda x: x[0], reverse=True)
                
                if similarities:
                    print(f"\n✅ 벡터 유사도 기반 검색 결과 (상위 {min(top_k, len(similarities))}개):")
                    print("=" * 80)
                    
                    for i, (similarity, menu) in enumerate(similarities[:top_k], 1):
                        restaurant = menu.get('restaurants', {}) or {}
                        
                        print(f"\n{i}. {restaurant.get('name', 'N/A')} - {menu.get('name', 'N/A')}")
                        print(f"   📍 주소: {restaurant.get('address', '주소 정보 없음')}")
                        if menu.get('price'):
                            print(f"   💰 가격: {menu['price']:,}원")
                        else:
                            print("   💰 가격: 미정")
                        print(f"   🏷️  카테고리: {restaurant.get('category', '미분류')}")
                        
                        # 유사도 점수 (0~1 범위, 1에 가까울수록 유사)
                        similarity_percent = similarity * 100
                        print(f"   🎯 벡터 유사도: {similarity:.4f} ({similarity_percent:.2f}%)")
                        
                        # 유사도 레벨 표시
                        if similarity > 0.8:
                            level = "🔥 매우 높음"
                        elif similarity > 0.6:
                            level = "✨ 높음"
                        elif similarity > 0.4:
                            level = "👍 보통"
                        elif similarity > 0.2:
                            level = "🤔 낮음"
                        else:
                            level = "❓ 매우 낮음"
                        print(f"   📊 유사도 레벨: {level}")
                        
                        if menu.get('description'):
                            print(f"   📝 설명: {menu['description']}")
                        
                        # 메뉴 텍스트 미리보기
                        menu_text = menu.get('menu_text', 'N/A')
                        if len(menu_text) > 80:
                            menu_text = menu_text[:80] + "..."
                        print(f"   📄 메뉴 정보: {menu_text}")
                    
                    # 검색 통계 정보
                    print(f"\n📈 검색 통계:")
                    print(f"   • 전체 메뉴 수: {len(similarities)}개")
                    print(f"   • 평균 유사도: {np.mean([s[0] for s in similarities]):.4f}")
                    print(f"   • 최고 유사도: {similarities[0][0]:.4f}")
                    print(f"   • 최저 유사도: {similarities[-1][0]:.4f}")
                    
                else:
                    print("❌ 유사도를 계산할 수 있는 메뉴가 없습니다.")
                    
            except Exception as e:
                print(f"❌ 벡터 검색 중 오류 발생: {e}")
                print("💡 오류 상세 정보:")
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        print(f"❌ 서비스 초기화 중 오류: {e}")

def main():
    """메인 함수"""
    print("🎯 벡터 유사도 검색 테스트 도구")
    print("=" * 50)
    
    # 환경 설정 확인
    if not os.path.exists('.env'):
        print("❌ .env 파일이 없습니다.")
        print("💡 환경 설정을 완료한 후 다시 실행해주세요.")
        return
    
    # 벡터 검색 테스트
    vector_search_with_similarity()

if __name__ == "__main__":
    main()
