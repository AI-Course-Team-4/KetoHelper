"""
벡터 서칭을 통한 메뉴 검색 - 메인 실행 스크립트
사용자가 프롬프트를 입력하면 유사한 메뉴를 찾아주는 인터랙티브 스크립트
"""

import sys
import os
from loguru import logger
from src.vector_searcher import VectorSearcher

def setup_logging():
    """로깅 설정"""
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    )
    
    # 파일 로깅
    os.makedirs("logs", exist_ok=True)
    logger.add(
        "logs/vector_search.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB"
    )

def print_welcome():
    """환영 메시지 출력"""
    print("\n" + "="*60)
    print("🍽️  벡터 서칭 메뉴 검색 시스템")
    print("="*60)
    print("📝 원하는 음식이나 메뉴를 자연어로 입력해보세요!")
    print("💡 예시: '매운 한국 음식', '건강한 샐러드', '치킨 요리' 등")
    print("🔧 설정: 최대 5개 결과, 유사도 임계값 0.1")
    print("❌ 종료하려면 'quit' 또는 'exit'를 입력하세요")
    print("="*60 + "\n")

def print_help():
    """도움말 출력"""
    print("\n📖 사용 가능한 명령어:")
    print("  - help: 이 도움말 표시")
    print("  - settings: 검색 설정 변경")
    print("  - quit/exit: 프로그램 종료")
    print("  - 그 외: 메뉴 검색 쿼리로 인식")
    print()

def get_search_settings():
    """검색 설정 입력받기"""
    print("\n⚙️ 검색 설정:")
    
    try:
        match_count = input("결과 개수 (기본값: 5): ").strip()
        match_count = int(match_count) if match_count else 5
        
        match_threshold = input("유사도 임계값 0~1 (기본값: 0.3): ").strip()
        match_threshold = float(match_threshold) if match_threshold else 0.1
        
        print(f"✅ 설정 완료 - 결과 개수: {match_count}, 임계값: {match_threshold}")
        return match_count, match_threshold
        
    except ValueError:
        print("❌ 잘못된 입력입니다. 기본값을 사용합니다.")
        return 5, 0.3

def main():
    """메인 실행 함수"""
    setup_logging()
    
    try:
        # VectorSearcher 초기화
        logger.info("벡터 서칭 시스템 시작")
        searcher = VectorSearcher()
        
        # 기본 설정
        match_count = 5
        match_threshold = 0.1
        
        # 환영 메시지
        print_welcome()
        
        while True:
            try:
                # 사용자 입력 받기
                user_input = input("🔍 검색어를 입력하세요: ").strip()
                
                if not user_input:
                    print("❌ 검색어를 입력해주세요.")
                    continue
                
                # 종료 명령
                if user_input.lower() in ['quit', 'exit', '종료', 'q']:
                    print("👋 벡터 서칭 시스템을 종료합니다.")
                    break
                
                # 도움말
                elif user_input.lower() in ['help', '도움말', 'h']:
                    print_help()
                    continue
                
                # 설정 변경
                elif user_input.lower() in ['settings', '설정', 's']:
                    match_count, match_threshold = get_search_settings()
                    continue
                
                # 메뉴 검색 실행
                else:
                    searcher.search_and_display(
                        query=user_input,
                        match_count=match_count,
                        match_threshold=match_threshold
                    )
                
            except KeyboardInterrupt:
                print("\n\n👋 사용자가 프로그램을 중단했습니다.")
                break
                
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                logger.error(f"실행 중 오류: {e}")
                
    except Exception as e:
        print(f"❌ 시스템 초기화 실패: {e}")
        logger.error(f"시스템 초기화 실패: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
