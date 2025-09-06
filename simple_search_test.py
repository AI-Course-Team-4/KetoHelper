#!/usr/bin/env python3
"""
간단한 벡터 서칭 테스트 스크립트
환경 설정 없이 기본 기능을 테스트할 수 있습니다.
"""

import os
import sys

def check_environment():
    """환경 설정 확인"""
    print("🔍 환경 설정 확인 중...")
    
    # .env 파일 확인
    env_file = ".env"
    if not os.path.exists(env_file):
        print(f"❌ {env_file} 파일이 없습니다.")
        print("📝 다음 내용으로 .env 파일을 생성해주세요:")
        print()
        print("# Supabase 설정")
        print("SUPABASE_URL=https://your-project-id.supabase.co")
        print("SUPABASE_KEY=your_supabase_anon_key")
        print()
        print("# OpenAI API 설정")
        print("OPENAI_API_KEY=sk-your-openai-api-key")
        print()
        return False
    
    # 환경 변수 로드 시도
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not supabase_url or supabase_url == "your_supabase_url":
            print("❌ SUPABASE_URL이 설정되지 않았습니다.")
            return False
            
        if not supabase_key or supabase_key == "your_supabase_anon_key":
            print("❌ SUPABASE_KEY가 설정되지 않았습니다.")
            return False
            
        if not openai_key or openai_key == "your_openai_api_key":
            print("❌ OPENAI_API_KEY가 설정되지 않았습니다.")
            return False
            
        print("✅ 환경 설정이 완료되었습니다!")
        return True
        
    except ImportError:
        print("❌ python-dotenv 패키지가 설치되지 않았습니다.")
        print("💡 pip install python-dotenv 실행 후 다시 시도해주세요.")
        return False
    except Exception as e:
        print(f"❌ 환경 설정 로드 중 오류: {e}")
        return False

def test_vector_search():
    """벡터 서칭 테스트"""
    try:
        # 현재 디렉토리를 sys.path에 추가
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        
        from src.search_service import SearchService
        
        print("🔍 벡터 서치 서비스 초기화 중...")
        search_service = SearchService()
        
        print("✅ 벡터 서치 서비스가 성공적으로 초기화되었습니다!")
        
        # 대화형 검색 시작
        print("\n" + "="*60)
        print("🎯 벡터 서칭 테스트 모드")
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
                # 검색 수행
                results = search_service.search(query, top_k)
                
                if results:
                    print(f"\n✅ {len(results)}개 결과 발견:")
                    print("=" * 60)
                    
                    for i, result in enumerate(results, 1):
                        print(f"\n{i}. {result['restaurant_name']} - {result['menu_name']}")
                        print(f"   📍 주소: {result.get('address', '주소 정보 없음')}")
                        if result.get('price'):
                            print(f"   💰 가격: {result['price']:,}원")
                        else:
                            print("   💰 가격: 미정")
                        print(f"   🏷️  카테고리: {result.get('category', '미분류')}")
                        print(f"   📊 유사도: {result['score']:.4f}")
                        if result.get('description'):
                            print(f"   📝 설명: {result['description']}")
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
    print("🎯 벡터 서칭 테스트 도구")
    print("=" * 50)
    
    # 환경 설정 확인
    if not check_environment():
        print("\n❌ 환경 설정을 완료한 후 다시 실행해주세요.")
        return
    
    # 벡터 서칭 테스트
    test_vector_search()

if __name__ == "__main__":
    main()
