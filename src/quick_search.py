"""
빠른 검색 테스트 스크립트
"""
import sys
import logging
from search_service import SearchService
from config import validate_config

def quick_search(query: str, top_k: int = 5):
    """빠른 검색 실행"""
    try:
        # 환경 설정 검증
        validate_config()
        
        # 검색 서비스 초기화
        search_service = SearchService()
        
        print(f"🔍 '{query}' 검색 중...")
        
        # 검색 수행
        results = search_service.search(query, top_k)
        
        if results:
            print(f"\n✅ {len(results)}개 결과 발견:")
            print("=" * 60)
            
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['restaurant_name']} - {result['menu_name']}")
                print(f"   📍 주소: {result['address']}")
                print(f"   💰 가격: {result['price']:,}원" if result['price'] else "   💰 가격: 미정")
                print(f"   🏷️  카테고리: {result.get('category', '미분류')}")
                print(f"   📊 유사도: {result['score']:.4f}")
        else:
            print("❌ 검색 결과가 없습니다.")
            
    except Exception as e:
        print(f"❌ 검색 중 오류 발생: {e}")
        return False
    
    return True

def main():
    """메인 실행 함수"""
    # 로깅 레벨을 WARNING으로 설정 (INFO 메시지 숨김)
    logging.basicConfig(level=logging.WARNING)
    
    # 명령행 인수 처리
    if len(sys.argv) < 2:
        print("사용법: python quick_search.py <검색어> [결과개수]")
        print("예시: python quick_search.py \"매운 음식\" 5")
        
        # 대화형 모드
        while True:
            query = input("\n🔍 검색어를 입력하세요 (종료: quit): ").strip()
            
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
            
            quick_search(query, top_k)
    else:
        # 명령행 모드
        query = sys.argv[1]
        top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        top_k = max(1, min(top_k, 20))  # 1-20 사이로 제한
        
        success = quick_search(query, top_k)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
